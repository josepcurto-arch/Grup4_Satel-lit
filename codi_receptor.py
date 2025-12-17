# -*- coding: utf-8 -*-
"""
Aplicació de recepció i visualització de telemetria
---------------------------------------------------
- Lectura de dades per port sèrie (thread separat)
- Validació de checksum (suma ASCII % 256)
- Gestió d'error_code amb camps absents
- Càlcul de mitjanes si no venen donades
- Interfície gràfica amb Tkinter
- Gràfiques amb Matplotlib (temps, radar, groundtrack)
- Registre d'errors i observacions

"""

# ===================== IMPORTS =====================
import os
import threading
import time
from datetime import datetime
from collections import deque

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import serial
import serial.tools.list_ports

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ===================== CONFIGURACIÓ GLOBAL =====================

DEFAULT_COM = "COM3"
BAUDRATE = 9600

# Arxiu d'alarmes a l'escriptori
ALARMES_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "alarmes.txt")

# Temps màxim sense recepció (es pot modificar des del menú)
temps_tx = 6

# Buffers per mitjanes (últims 10 valors)
buf_temp = deque(maxlen=10)
buf_hum = deque(maxlen=10)
buf_pres = deque(maxlen=10)

# Històric temporal per gràfiques (30 segons)
hist_temp = deque()
hist_hum = deque()
hist_pres = deque()
hist_time = deque()

# Estat global
last_rx_time = 0
running = True
start_time = None

# Flags de botons
TX_state = True   # True = TX1, False = TX0
MI_state = False  # False = Terra, True = Satèl·lit
POS_state = True  # False = GNSS, True = Satèl·lit


# ===================== FUNCIONS D'UTILITAT =====================

def log_alarm(tipus, descripcio):
    """Escriu una línia al fitxer d'alarmes amb timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ALARMES_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} {tipus} {descripcio}\n")


def verify_checksum(received_checksum: int, data_str: str) -> bool:
    """
    Verifica el checksum rebut.
    - data_str ha de començar per la coma (,i,error_code,...)
    """
    calculated = sum(ord(c) for c in data_str) % 256
    return calculated == received_checksum


# ===================== CONVERSIÓ ECEF → LAT/LON =====================

def ecef_to_latlon(x, y, z):
    """Converteix coordenades ECEF (metres) a latitud i longitud."""
    a = 6378137.0
    e = 8.1819190842622e-2

    b = np.sqrt(a**2 * (1 - e**2))
    ep = np.sqrt((a**2 - b**2) / b**2)
    p = np.sqrt(x**2 + y**2)
    th = np.arctan2(a * z, b * p)

    lon = np.arctan2(y, x)
    lat = np.arctan2(z + ep**2 * b * np.sin(th)**3,
                     p - e**2 * a * np.cos(th)**3)

    lat = np.degrees(lat)
    lon = np.degrees(lon)
    return lat, lon

# ===================== CLASSES DE GRÀFIQUES =====================

class RadarPlot:
    """Visualització polar de distància-angle (només punts)."""
    def __init__(self, parent):
        self.fig = plt.Figure(figsize=(4, 3))
        self.ax = self.fig.add_subplot(111, polar=True)
        self.ax.set_thetamin(0)
        self.ax.set_thetamax(180)
        self.ax.set_theta_zero_location("W")
        self.ax.set_theta_direction(-1)
        self.ax.set_ylim(0, 250)
        self.scatter = self.ax.scatter([], [])

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update(self, dist, ang):
        if not dist:
            return
        theta = np.deg2rad(ang)
        self.ax.clear()
        self.ax.set_thetamin(0)
        self.ax.set_thetamax(180)
        self.ax.set_theta_zero_location("W")
        self.ax.set_theta_direction(-1)
        self.ax.set_ylim(0, 250)
        self.ax.scatter(theta, dist, c='g')
        self.canvas.draw()


class GroundTrackPlot:
    """Dibuixa la posició actual i l'històric sobre un mapa."""
    def __init__(self, parent):
        self.fig = plt.Figure(figsize=(4, 3))
        self.ax = self.fig.add_subplot(111)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(script_dir, "GroundTrackBackground.png")
        img = mpimg.imread(img_path)
        self.ax.imshow(img, extent=[-180, 180, -90, 90], aspect="auto")

        self.ax.set_xlim(-180, 180)
        self.ax.set_ylim(-90, 90)
        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")

        self.lats = []
        self.lons = []
        self.line, = self.ax.plot([], [], 'g-')
        self.point, = self.ax.plot([], [], 'ro')

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update(self, x, y, z):
        lat, lon = ecef_to_latlon(x, y, z)
        self.lats.append(lat)
        self.lons.append(lon)
        if len(self.lats) > 2000:
            self.lats.pop(0)
            self.lons.pop(0)
        self.line.set_data(self.lons, self.lats)
        self.point.set_data([lon], [lat])
        self.canvas.draw()


# ===================== LECTURA SÈRIE =====================

def serial_thread(port):
    """Thread de lectura del port sèrie."""
    global last_rx_time

    while running:
        try:
            line = port.readline().decode(errors='ignore').strip()
            print(f"Rebut: {line}")
            if not line:
                continue

            last_rx_time = time.time()
            process_line(line)

        except Exception as e:
            log_alarm("ERROR", f"SERIAL {e}")


def process_line(line):
    """Processa una línia de telemetria rebuda."""
    try:
        global start_time
        now = time.time()
        if start_time is None:
            start_time = now
        parts = line.split(',')
        received_checksum = int(parts[0])
        data_str = ',' + ','.join(parts[1:])

        # Verificació checksum
        if not verify_checksum(received_checksum, data_str):
            log_alarm("ERROR", "CHECKSUM")
            return

        # Índex i error_code
        idx = int(parts[1])
        error_code = int(parts[2])
        error_bits = [(error_code >> i) & 1 for i in range(5)]

        cursor = 3

        # Posició
        x = float(parts[cursor]); y = float(parts[cursor+1]); z = float(parts[cursor+2])
        cursor += 3

        # Bateria
        batt = float(parts[cursor]); cursor += 1

        # Sensors
        temp = hum = pres = None

        if not error_bits[0]:
            temp = float(parts[cursor]); cursor += 1
            buf_temp.append(temp)
        if not error_bits[1]:
            hum = float(parts[cursor]); cursor += 1
            buf_hum.append(hum)
        if not error_bits[4]:
            pres = float(parts[cursor]); cursor += 1
            buf_pres.append(pres)

        # Radar dist:angle
        dist = []
        ang = []
        while cursor < len(parts) and ':' in parts[cursor]:
            d, a = parts[cursor].split(':')
            dist.append(float(d))
            ang.append(float(a))
            cursor += 1

        # Mitjanes
        if error_bits[3]:
            medt = float(parts[cursor]); medh = float(parts[cursor+1]); medp = float(parts[cursor+2])
        else:
            medt = np.mean(buf_temp) if buf_temp else None
            medh = np.mean(buf_hum) if buf_hum else None
            medp = np.mean(buf_pres) if buf_pres else None

        # Actualització gràfiques
        now = time.time()
        t = now - start_time
        hist_time.append(t)
        if temp is not None:
            hist_temp.append(temp)
        if hum is not None:
            hist_hum.append(hum)
        if pres is not None:
            hist_pres.append(pres)

        # Neteja > 30s
        while hist_time and (hist_time[-1] - hist_time[0]) > 30:
            hist_time.popleft()
            if hist_temp: hist_temp.popleft()
            if hist_hum: hist_hum.popleft()
            if hist_pres: hist_pres.popleft()

        # Actualitza dades reals
        times = list(hist_time)
        line_temp.set_data(times, list(hist_temp))
        line_hum.set_data(times, list(hist_hum))
        line_pres.set_data(times, list(hist_pres))

        ax_temp.relim()
        ax_temp.autoscale_view()

        ax_hum.relim()
        ax_hum.autoscale_view()

        ax_pres.relim()
        ax_pres.autoscale_view()

        t_now = times[-1]

        ax_temp.set_xlim(max(0, t_now - 35), t_now+1)
        ax_hum.set_xlim(max(0, t_now - 35), t_now+1)
        ax_pres.set_xlim(max(0, t_now - 35), t_now+1)


        # Actualitza línies de mitjana (si existeixen)
        if medt is not None and len(times) > 0:
            line_med_temp.set_data(times, [medt]*len(times))
        else:
            line_med_temp.set_data([], [])

        if medh is not None and len(times) > 0:
            line_med_hum.set_data(times, [medh]*len(times))
        else:
            line_med_hum.set_data([], [])

        if medp is not None and len(times) > 0:
            line_med_pres.set_data(times, [medp]*len(times))
        else:
            line_med_pres.set_data([], [])

        # Ajusta límits i redibuixa cada eix per separat
        for ax in (ax_temp, ax_hum, ax_pres):
            ax.relim()
            ax.autoscale_view()

        canvas_thp.draw()

        radar.update(dist, ang)
        ground.update(x, y, z)

        lbl_i.config(text=f"i = {idx}")
        lbl_batt.config(text=f"Bateria = {batt:.1f}%")(text=f"Bateria = {batt:.1f}%")

    except Exception as e:
        log_alarm("ERROR", f"PARSE {e}")

# ===================== MENÚ CONFIGURACIÓ =====================

def open_config_menu():
    """Menú de configuració complet: temp, humitat i pressió (màx/min)."""
    win = tk.Toplevel(window)
    win.title("Menú de Configuració")
    win.geometry("400x400")

    # Variables locals
    vars_cfg = {
        "maxTemp": tk.StringVar(value="50"),
        "minTemp": tk.StringVar(value="-10"),
        "maxHum":  tk.StringVar(value="100"),
        "minHum":  tk.StringVar(value="0"),
        "maxPres": tk.StringVar(value="110"),
        "minPres": tk.StringVar(value="98"),
        "tempstx": tk.StringVar(value=temps_tx),
        "fixAngle": tk.StringVar(value="-1"),
    }

    labels = [
        ("Temp màx", "maxTemp"), ("Temp mín", "minTemp"),
        ("Hum màx", "maxHum"),   ("Hum mín", "minHum"),
        ("Pres màx", "maxPres"), ("Pres mín", "minPres"),
        ("Temps tx", "tempstx"), ("Angle fix radar", "fixAngle")
    ]

    for i, (txt, key) in enumerate(labels):
        tk.Label(win, text=txt).grid(row=i//2, column=(i%2)*2, padx=5, pady=5, sticky="e")
        tk.Entry(win, textvariable=vars_cfg[key], width=6).grid(row=i//2, column=(i%2)*2+1, padx=5, pady=5)

    def enviar():
        try:
            maxT = int(vars_cfg["maxTemp"].get())
            minT = int(vars_cfg["minTemp"].get())
            maxH = int(vars_cfg["maxHum"].get())
            minH = int(vars_cfg["minHum"].get())
            maxP = int(vars_cfg["maxPres"].get())
            minP = int(vars_cfg["minPres"].get())
            temps_tx = int(vars_cfg["tempstx"].get())
            fix_angle = int(vars_cfg["fixAngle"].get())

            if not (maxT > minT and maxH > minH and maxP > minP):
                raise ValueError

            cfg_str = f"{maxT},{minT},{maxH},{minH},{maxP},{minP},{temps_tx},{fix_angle}"

            if mySerial and mySerial.is_open:
                mySerial.write((cfg_str + "\n").encode())

            messagebox.showinfo("Configuració", f"Enviat: {cfg_str}")

        except:
            messagebox.showerror("Error", "Valors invàlids de configuració")


    tk.Button(win, text="Enviar configuració", command=enviar).grid(row=4, column=1, columnspan=2)


# ===================== MENÚ ALERTES =====================

def open_alerts_menu():
    """Mostra el registre d'alarmes amb filtres per tipus i dia."""
    win = tk.Toplevel(window)
    win.title("Menú d'Alertes")
    win.geometry("900x500")

    top = tk.Frame(win)
    top.pack(fill='x')

    tk.Label(top, text="Tipus:").pack(side='left')
    tipo_var = tk.StringVar(value="Tots")
    cb_tipo = ttk.Combobox(top, textvariable=tipo_var,
                           values=["Tots", "ERROR", "OBSERVACIO"])
    cb_tipo.pack(side='left', padx=5)

    tk.Label(top, text="Dia (YYYY-MM-DD):").pack(side='left')
    dia_var = tk.StringVar()
    tk.Entry(top, textvariable=dia_var, width=12).pack(side='left', padx=5)

    text = tk.Text(win)
    text.pack(fill='both', expand=True)

    def carregar():
        text.delete("1.0", tk.END)
        if not os.path.exists(ALARMES_PATH):
            return
        with open(ALARMES_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if tipo_var.get() != "Tots" and tipo_var.get() not in line:
                    continue
                if dia_var.get() and not line.startswith(dia_var.get()):
                    continue
                text.insert(tk.END, line)

    ttk.Button(top, text="Aplicar filtre", command=carregar).pack(side='left', padx=5)
    carregar()


# ===================== GUI =====================

window = tk.Tk()
window.title("Telemetria")
window.geometry("1200x800")

# --- Connexió sèrie ---
try:
    mySerial = serial.Serial(DEFAULT_COM, BAUDRATE, timeout=1)
except Exception as e:
    messagebox.showerror("Error", f"No s'ha pogut obrir el port sèrie: {e}")
    mySerial = None

# --- Widgets superiors ---
frm_top = ttk.Frame(window)
frm_top.pack(fill='x')

entry_cmd = ttk.Entry(frm_top, width=40)
entry_cmd.pack(side='left', padx=5)

def send_entry():
    txt = entry_cmd.get().strip()
    if not txt:
        return
    if txt.startswith("OBSERVACIO"):
        log_alarm("OBSERVACIO", txt[len("OBSERVACIO"):].strip())
    else:
        if mySerial and mySerial.is_open:
            mySerial.write((txt + '').encode())

btn_send = ttk.Button(frm_top, text="Enviar", command=send_entry)
btn_send.pack(side='left', padx=5)

# --- Botons A–E ---
def toggle_TX():
    global TX_state
    TX_state = not TX_state
    cmd = "TX1" if TX_state else "TX0"
    if mySerial and mySerial.is_open:
        mySerial.write((cmd + '').encode())
    lbl_tx.config(text=f"TX: {'ON' if TX_state else 'OFF'}")

btn_A = ttk.Button(frm_top, text="A: TX", command=toggle_TX)
btn_A.pack(side='left', padx=3)

def toggle_MI():
    global MI_state
    MI_state = not MI_state
    cmd = "MI1" if MI_state else "MI0"
    if mySerial and mySerial.is_open:
        mySerial.write((cmd + '').encode())
    lbl_mi.config(text=f"MI: {'SAT' if MI_state else 'TERRA'}")

btn_B = ttk.Button(frm_top, text="B: Mitjanes", command=toggle_MI)
btn_B.pack(side='left', padx=3)

btn_C = ttk.Button(frm_top, text="C: Config", command=lambda: open_config_menu())
btn_C.pack(side='left', padx=3)

btn_D = ttk.Button(frm_top, text="D: Alertes", command=lambda: open_alerts_menu())
btn_D.pack(side='left', padx=3)

def toggle_POS():
    global POS_state
    POS_state = not POS_state
    if POS_state:
        cmd = "POS1"
    else:
        cmd = "POS0"

    if mySerial and mySerial.is_open:
        mySerial.write((cmd + '').encode())
    lbl_pos.config(text=f"POS: {'SAT' if POS_state else 'GNSS'}")

btn_E = ttk.Button(frm_top, text="E: POS", command=toggle_POS)
btn_E.pack(side='left', padx=3)

lbl_i = ttk.Label(frm_top, text="i = --")
lbl_i.pack(side='left', padx=10)

lbl_batt = ttk.Label(frm_top, text="Bateria = --")
lbl_batt.pack(side='left', padx=10)

lbl_tx = ttk.Label(frm_top, text="TX: ON")
lbl_tx.pack(side='left', padx=6)

lbl_mi = ttk.Label(frm_top, text="MI: TERRA")
lbl_mi.pack(side='left', padx=6)

lbl_pos = ttk.Label(frm_top, text="POS: GNSS")
lbl_pos.pack(side='left', padx=6)

lbl_status = ttk.Label(frm_top, text="RX OK", foreground="green")
lbl_status.pack(side='left', padx=10)

# --- Gràfiques ---
frm_plots = ttk.Frame(window)
frm_plots.pack(fill='both', expand=True)

# Subframes per organitzar gràfiques
frm_left = ttk.Frame(frm_plots)
frm_left.pack(side='left', fill='both', expand=True)

frm_right = ttk.Frame(frm_plots)
frm_right.pack(side='right', fill='both', expand=True)

# --- Gràfiques temporals (Temp / Hum / Pres) - tres gràfiques apilades ------
# Creem una sola figura ampla amb tres eixos apilats (cada gràfica és més ampla que alta)
fig_thp = plt.Figure(figsize=(6,6))
# Tres eixos apilats verticalment; cada un tindrà una altura reduïda fent la figura "ampla i curta"
ax_temp = fig_thp.add_subplot(311)
ax_hum  = fig_thp.add_subplot(312)
ax_pres = fig_thp.add_subplot(313)

# Configuració estètica bàsica
ax_temp.set_title("Temperatura")
ax_hum.set_title("Humitat")
ax_pres.set_title("Pressió")
for ax in (ax_temp, ax_hum, ax_pres):
    ax.grid(True, linestyle=':', linewidth=0.5)

# Línies de dades i de mitjanes per cada eix
line_temp, = ax_temp.plot([], [], label="Temp")
line_med_temp, = ax_temp.plot([], [], alpha=0.4, linewidth=1)

line_hum, = ax_hum.plot([], [], label="Hum")
line_med_hum, = ax_hum.plot([], [], alpha=0.4, linewidth=1)

line_pres, = ax_pres.plot([], [], label="Pres")
line_med_pres, = ax_pres.plot([], [], alpha=0.4, linewidth=1)

# Llegenda petita a cada eix
ax_temp.legend(loc='upper right', fontsize='small')
ax_hum.legend(loc='upper right', fontsize='small')
ax_pres.legend(loc='upper right', fontsize='small')

fig_thp.subplots_adjust(hspace=0.6, top=0.95, bottom=0.05)
canvas_thp = FigureCanvasTkAgg(fig_thp, master=frm_left)
canvas_thp.get_tk_widget().pack(fill="both", expand=True)


# --- Radar i Groundtrack ---
radar = RadarPlot(frm_right)
ground = GroundTrackPlot(frm_right)

# --- Monitor estat RX ---

def monitor_rx():
    if time.time() - last_rx_time > temps_tx + 1:
        lbl_status.config(text="SENSE DADES", foreground="red")
    else:
        lbl_status.config(text="RX OK", foreground="green")
    window.after(1000, monitor_rx)

monitor_rx()

# --- Thread sèrie ---
if mySerial:
    t = threading.Thread(target=serial_thread, args=(mySerial,), daemon=True)
    t.start()

window.mainloop()
running = False
