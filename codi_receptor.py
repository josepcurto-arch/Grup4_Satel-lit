from tkinter import *
from tkinter import messagebox
from datetime import datetime
import tkinter as tk
import serial
import threading
import time
import math
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os


# ---------- CONFIGURACIÓ DEL PORT SÈRIE ----------
device = 'COM3'   # Canvia-ho segons el teu cas
baudrate = 9600

try:  # Intentem establir comunicació amb el port sèrie
    mySerial = serial.Serial(device, baudrate, timeout=1)
    print("Port sèrie obert:", device)
except Exception as e:
    print("No s'ha pogut obrir el port sèrie:", e)
    mySerial = None

# ---------- VARIABLES GLOBALS ----------
transmissio_activa = True
temps = []
temps_inicial = time.time()
temps_max = 30
temps_max_punts = 50
temps_ultima_dada = time.time()
valors_temp = []
valors_hum = []
time_control = 0
mitjana_satelit = 0
dist_list_global = []   # Per guardar totes les distàncies
angle_list_global = []  # Per guardar tots els angles corresponents
med_temp_list = [0] * 10
med_hum_list  = [0] * 10
valors_med_temp = []
valors_med_hum = []

# Config related variables
max_temp = 30
min_temp = 5
max_hum = 80
min_hum = 10
temps_tx = 5 # Segons

# ---------- FUNCIONS ----------

class Events:
    def __init__(self, temps, tipus, descripcio):
        self.temps = temps
        self.tipus = tipus
        self.descripcio = descripcio

def RegistrarEvents(tipus, descripcio):
    temps = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    event = Events(temps, tipus, descripcio)
    EscriureEvents(event, "registro_eventos.txt")

def EscriureEvents(event, nombreFichero):
    with open(nombreFichero, "a") as salida:
        salida.write(f"{event.temps} {event.tipus} {event.descripcio}\n")

# ---------- NOU: FUNCIO DE VERIFICACIÓ CHECKSUM ----------
def verify_checksum(received_checksum: int, data_str: str) -> bool:
    """
    Verifies if the checksum of `data_str` matches the `received_checksum`.
    
    Args:
        received_checksum (int): The checksum received from Arduino.
        data_str (str): The string data that was used to calculate the checksum, 
                        including the leading comma if present.
    
    Returns:
        bool: True if checksum matches, False otherwise.
    """
    calculated_checksum = sum(ord(c) for c in data_str) % 256
    return received_checksum == calculated_checksum

class RadarPlot:
    def __init__(self, parent):
        # Convert Tkinter background color to real hex color
        tk_color = parent.cget("bg")
        rgb = parent.winfo_rgb(tk_color)
        bg = "#%02x%02x%02x" % (rgb[0]//256, rgb[1]//256, rgb[2]//256)

        # Background semicircle
        theta = np.linspace(0, np.pi, 181)
        r = np.full_like(theta, 200)

        self.fig = plt.Figure(figsize=(5, 3))
        self.ax = self.fig.add_subplot(111, polar=True)
        self.ax.set_autoscale_on(False)
        self.ax.set_xlim(-180, 180)
        self.ax.set_ylim(-90, 90)
        

        self.fig.subplots_adjust(top=0.98, bottom=0.05, left=0.05, right=0.95)

        self.fig.patch.set_facecolor(bg)
        self.ax.set_facecolor(bg)

        self.ax.plot(theta, r, color='lightgray', linewidth=2, linestyle='--')

        self.ax.set_thetamin(0)
        self.ax.set_thetamax(180)
        self.ax.set_theta_zero_location("W")
        self.ax.set_theta_direction(-1)
        self.ax.set_ylim(0, 250)

        # Empty radar plot line
        self.line, = self.ax.plot([], [], "go-", linewidth=2)

        # Embed into Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=4,column=0,rowspan=1,columnspan=2,sticky="nsew")

    def update_plot(self, dist_list, angle_list):
        """
        dist_list = list of distances (max 18)
        angle_list = angles in degrees (0–180)
        """
        if not dist_list or not angle_list:
            return

        theta_rad = np.deg2rad(angle_list)
        self.line.set_data(theta_rad, dist_list)
        self.canvas.draw()

class GroundTrackPlot:
    def __init__(self, parent):
        # Background color from Tk
        tk_color = parent.cget("bg")
        rgb = parent.winfo_rgb(tk_color)
        bg = "#%02x%02x%02x" % (rgb[0]//256, rgb[1]//256, rgb[2]//256)

        # Create figure
        self.fig = plt.Figure(figsize=(5, 3))
        self.ax = self.fig.add_subplot(111)

        # Match background
        self.fig.patch.set_facecolor(bg)
        self.ax.set_facecolor(bg)

        # Get absolute path to image next to this .py file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(script_dir, "GroundTrackBackground.png")

        # Load image safely
        img = mpimg.imread(img_path)
        # Draw it behind the lat/lon grid
        self.ax.imshow(
            img,
            extent=[-180, 180, -90, 90],
            origin="upper",     # keeps north on top
            aspect="auto"       # avoids stretching
        )

        # Reduce margins
        self.fig.subplots_adjust(left=0.07, right=0.97, top=0.95, bottom=0.1)

        # Axes labels
        self.ax.set_xlabel("Longitude (°)")
        self.ax.set_ylabel("Latitude (°)")
        self.ax.set_title("Groundtrack")

        # Limits for world map
        self.ax.set_xlim(-180, 180)
        self.ax.set_ylim(-90, 90)

        # Track line
        self.lats = []
        self.lons = []
        self.line, = self.ax.plot([], [], "g-", linewidth=2)   # green track
        self.point, = self.ax.plot([], [], "ro")                # current pos

        # Embed in Tkinter grid
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()

        # You choose the exact position; example:
        self.canvas_widget.grid(row=4, column=2, rowspan=2, columnspan=2, sticky="nsew")

    def update_track(self, x, y, z):
        lat, lon = ecef_to_latlon(x, y, z)

        # Append new point
        self.lats.append(lat)
        self.lons.append(lon)

        # Keep max track length
        if len(self.lats) > 2000:
            self.lats.pop(0)
            self.lons.pop(0)

        # Update line + point
        self.line.set_data(self.lons, self.lats)
        self.point.set_data([lon], [lat])   # <-- FIX HERE

        # Redraw
        self.canvas.draw()

def ecef_to_latlon(x, y, z):
    # WGS84 ellipsoid constants
    a = 6378137.0          # semi-major axis
    e2 = 0.00669437999014  # eccentricity squared

    lon = math.atan2(y, x)

    # Intermediate values
    b = a * math.sqrt(1 - e2)
    ep = math.sqrt((a*a - b*b) / (b*b))
    p = math.sqrt(x*x + y*y)
    th = math.atan2(a * z, b * p)

    lat = math.atan2(z + ep*ep * b * math.sin(th)**3,
                     p - e2 * a * math.cos(th)**3)

    # Convert to degrees
    lat = math.degrees(lat)
    lon = math.degrees(lon)

    return lat, lon
# ---------- ALTRES FUNCIONS DE BOTONS ----------
def EntrarClick():
    text = fraseEntry.get()
    print(f'Has introduït: "{text}"')
    if text.upper().startswith("OBSERVACIO"): 
        parts = text.split(" ", 1)
        observacio = parts[1] if len(parts) > 1 else ""
        print("Guardant observació al registre:", observacio)
        RegistrarEvents("OBSERVACIO", observacio)
        fraseEntry.delete(0, tk.END)
        return
    
    if mySerial and mySerial.is_open:
        try:
            mySerial.write((text + "\n").encode('utf-8'))
            print("Enviat pel port sèrie:", text)
        except Exception as e:
            print("Error enviant:", e)
    fraseEntry.delete(0, tk.END)

def AClick():
    global transmissio_activa
    transmissio_activa = not transmissio_activa
    if mySerial and mySerial.is_open:
        try:
            if transmissio_activa:
                mySerial.write(b"TX1\n")
                estadoLabel.config(text="Transmissió: ACTIVA", fg="green")
                print("Enviat: TX1 (reanudar transmissió)")
                RegistrarEvents("COMANDO","Reanudar transmissió (TX1)")
            else:
                mySerial.write(b"TX0\n")
                estadoLabel.config(text="Transmissió: PARADA", fg="red")
                print("Enviat: TX0 (parar transmissió)")
                RegistrarEvents("COMANDO", "Parar transmissió (TX0)")
        except Exception as e:
            print("Error enviant:", e)

def BClick():
    global mitjana_satelit
    mitjana_satelit = not mitjana_satelit
    if mySerial and mySerial.is_open:
        try:
            if mitjana_satelit == 0:
                mySerial.write(b"MI0\n")
                mitjana_Label.config(text="Mitjana des del satèl·lit", fg="green")
                print("Enviat: MI0 (satèl·lt)")
                RegistrarEvents("COMANDO", "Mitjana des del satèl·lit (MI0)")
            else:
                mySerial.write(b"MI1\n")
                mitjana_Label.config(text="Mitjana des de terra", fg="green")
                print("Enviat: MI1 (terra)")
                RegistrarEvents("COMANDO", "Mitjana des de terra (MI1)")
        except Exception as e:
            print("Error enviant:", e)

def CClick():
    global maxtemp, mintemp, tempstx, maxhum, minhum
    new_window = Toplevel(window)  # Create a new window
    new_window.title("Menú de Configuració")
    new_window.geometry("800x200")
    new_window.rowconfigure([0], weight=0)
    new_window.rowconfigure([1,2,3,4], weight=1)
    new_window.columnconfigure([0,1,2], weight=1)  

    Label(new_window, text="Temperatura Màxima:").grid(row=0, column=0, sticky=N)
    maxtemp = Entry(new_window, width=5, font=('Arial', 8))
    maxtemp.grid(row=1, column=0, columnspan=1, rowspan=1, padx=5, pady=5, sticky=N+S+E+W)
    maxtemp.insert(0, str(max_temp))

    Label(new_window, text="Temperatura mínima:").grid(row=0, column=1, sticky=N)
    mintemp = Entry(new_window, width=5, font=('Arial', 8))
    mintemp.grid(row=1, column=1, columnspan=1, rowspan=1, padx=5, pady=5, sticky=N+S+E+W)
    mintemp.insert(0, str(min_temp))

    Label(new_window, text="Temps de Transmisió:").grid(row=0, column=2, sticky=N)
    tempstx = Entry(new_window, width=5, font=('Arial', 8))
    tempstx.grid(row=1, column=2, columnspan=1, rowspan=1, padx=5, pady=5, sticky=N+S+E+W)
    tempstx.insert(0, str(temps_tx))


    Label(new_window, text="Humitat Màxima:").grid(row=3, column=0, sticky=N)
    maxhum = Entry(new_window, width=5, font=('Arial', 8))
    maxhum.grid(row=4, column=0, columnspan=1, rowspan=1, padx=5, pady=5, sticky=N+S+E+W)
    maxhum.insert(0, str(max_hum))

    Label(new_window, text="Humitat mínima:").grid(row=3, column=1, sticky=N)
    minhum = Entry(new_window, width=5, font=('Arial', 8))
    minhum.grid(row=4, column=1, columnspan=1, rowspan=1, padx=5, pady=5, sticky=N+S+E+W)
    minhum.insert(0, str(min_hum))

    EnviarButton = Button(new_window, text="Enviar configuració", command=enviar_configuracio)
    EnviarButton.grid(row=5, column=2, padx=5, pady=5, sticky=N+S+E+W)

# ---------- FUNCIONS DE PARSING ACTUALITZADES ----------
def parse_trozos(trozos):
    """
    Parseja les dades rebudes del satèl·lit sense el checksum.

    Args:
        trozos (list[str]): Llista de valors separats per comes, **sense checksum**.

    Returns:
        tuple: (i, error_code, temp, hum, dist_list, angle_list, medt, medh, 
                temp_err, hum_err, ultra_err, median_on)
    """
    if len(trozos) < 3:
        # No hi ha prou dades
        return -1, -1, -1, -1, [], [], -1, -1, False, False, False, False

    i = int(trozos[0])
    error_code = int(trozos[1])
    bits = format(error_code, "04b")
    temp_err   = bits[-1] == "1"
    hum_err    = bits[-2] == "1"
    ultra_err  = bits[-3] == "1"
    median_on  = bits[-4] == "1"

    x_pos = float(trozos[2])
    y_pos = float(trozos[3])
    z_pos = float(trozos[4])
    groundtrack.update_track(x_pos, y_pos, z_pos)

    index = 5  # Comencem després de x, y, z
    temp = hum = -1
    medt = medh = -1

    # Lectura temperatura
    if not temp_err and index < len(trozos):
        try:
            temp = int(trozos[index])
        except:
            temp = -1
        index += 1

    # Lectura humitat
    if not hum_err and index < len(trozos):
        try:
            hum = int(trozos[index])
        except:
            hum = -1
        index += 1

    # Parells distància;angle
    dist_list = []
    angle_list = []
    while index < len(trozos) - 2:  # Evitem tocar els dos últims (medt, medh)
        entry = trozos[index].strip()
        if ":" in entry:
            parts = entry.split(":")
            if len(parts) == 2:
                try:
                    dist_list.append(int(parts[0]))
                    angle_list.append(int(parts[1]))
                except:
                    pass
        index += 1
        radar.update_plot(dist_list, angle_list)


    # Mitjanes
    try:
        medt = float(trozos[-2])
    except:
        medt = -1
    try:
        medh = float(trozos[-1])
    except:
        medh = -1

    return i, error_code, temp, hum, dist_list, angle_list, medt, medh, temp_err, hum_err, ultra_err, median_on

def mostrar_instruccions():
    instruccions = (
        "Instruccions Port sèrie amb el Satèl·lit:\n"
        " - TX0/TX1: Atura/Reanuda la transmissió\n"
        " - MI0/MI1: Càlcul de les mitjanes al satèl·lit/a terra\n"
        " - T X: Ajustar el temps de transmissió (ex. T 2)"
    )
    messagebox.showinfo("Instruccions", instruccions)

def enviar_configuracio():
    max_temp = int(maxtemp.get())
    min_temp = int(mintemp.get())
    temps_tx = int(tempstx.get())
    max_hum = int(maxhum.get())
    min_hum = int(minhum.get())

    if max_temp > min_temp and max_hum > min_hum and temps_tx > 2:
        config_text = ",".join(map(str, [
            max_temp,
            min_temp,
            temps_tx,
            max_hum,
            min_hum
        ]))
        if mySerial and mySerial.is_open:
            try:
                mySerial.write((config_text + "\n").encode('utf-8'))
                print("Enviat pel port sèrie:", config_text)
            except Exception as e:
                print("Error enviant:", e)
        # Send config_text trough serial port   
    else:
        config_text = "N/A"
        messagebox.showerror("Error de Configuració", "Paràmetres invàlids. Si us plau, revisa les teves entrades.")


# ---------- FIL DE LECTURA SÈRIE ACTUALITZAT ----------
def serial_thread():
    global temps_ultima_dada
    timer_actualitzacio_grafica = time.time() + 0.1
    while True:
        if mySerial and mySerial.in_waiting > 0:
            try:
                linea = mySerial.readline().decode('utf-8').rstrip()
                if linea:
                    global time_control, temp_err, hum_err, ultra_err
                    error_Label.config(text="Sense errors", fg="green")
                    time_control = 0
                    print("Rebut:", linea)

                    trozos = linea.split(',')
                    if len(trozos) >= 4:
                        try:
                            # ---------- CHECKSUM ----------
                            received_checksum = int(trozos[0])
                            data_str = "," + ",".join(trozos[1:])  # incloem coma inicial
                            if verify_checksum(received_checksum, data_str):
                                print("Checksum correcte ✅")
                                dades = trozos[1:]  # Excloem checksum
                                i, error_code, temp, hum, dist_list, angle_list, medt, medh, temp_err, hum_err, ultra_err, median_on = parse_trozos(dades)
                            else:
                                print("Mensaje corrupto ❌")
                                RegistrarEvents("ALARMA", "Mensaje corrupto")
                                continue
                        except Exception as e:
                            print("Error en verificar checksum o parseig:", e)
                            continue

                        print(f"Index: {i}, Error Code: {error_code}, Temp: {temp}, Hum: {hum}, Med Temp: {medt}, Med Hum: {medh}")
                        dist_list_global[:] = dist_list
                        angle_list_global[:] = angle_list
                        temperatura.set(f"{temp} ºC")
                        humitat.set(f"{hum} %")
                        transmissio.set(i)

                        control = 0
                        med_temp_list[i % 10] = temp
                        med_hum_list[i % 10] = hum

                        # Recalcular mitjanes si no venen del satèl·lit
                        if not median_on:
                            medt = sum(med_temp_list) / 10
                            medh = sum(med_hum_list) / 10

                        # Errors
                        if temp_err:
                            print("Error Temperatura")
                            control = 1
                            error_Label.config(text="Error Temperatura", fg="red")
                            RegistrarEvents("ALARMA", "Error de temperatura")
                        if hum_err:
                            print("Error Humitat")
                            control = 1
                            error_Label.config(text="Error Humitat", fg="red")
                            RegistrarEvents("ALARMA", "Error d'humitat")
                        if ultra_err:
                            print("Error Ultrasons")
                            control = 1
                            error_Label.config(text="Error Ultrasons", fg="red")
                            RegistrarEvents("ALARMA", "Error d'ultrasons")
                        elif control == 0:
                            window.after(0, actualitza_grafiques, temp, hum, medt, medh)
                            window.after(0, lambda: error_Label.config(text="Sense errors", fg="green"))

                            temps_ultima_dada = time.time()
            except Exception as e:
                print("Error en la lectura sèrie:", e)

        if time.time() - temps_ultima_dada >= 7 and time_control == 0:
            if not valors_temp or valors_temp[-1] is not None:
                pass
            print("No es reben dades des de fa mes de 5 segons!")
            RegistrarEvents("ALARMA","No es reben dades des de fa mes de 5 segons!")
            error_Label.config(text="Sense recepció", fg="red")
            time_control = 1

        if time.time() >= timer_actualitzacio_grafica:
            canvas1.draw()
            canvas2.draw()
            timer_actualitzacio_grafica = time.time() + 0.1
        time.sleep(0.1)


# ---------- ACTUALITZAR GRÀFIQUES ----------
def actualitza_grafiques(temp, hum, medt, medh):
    global temps_ultima_dada
    temps_actual = time.time() - temps_inicial
    temps.append(temps_actual)
    temps_ultima_dada = time.time()
    valors_temp.append(np.nan if temp == -1 or temp is None else temp)
    valors_hum.append(np.nan if hum == -1 or hum is None else hum)
    valors_med_temp.append(np.nan if medt is None else medt)
    valors_med_hum.append(np.nan if medh is None else medh)


    if len(temps) > temps_max_punts:   # Desplacem la gràfica del temps quan arribi a un determinat instant per tal de no comprimir la gràfica
        temps.pop(0)
        valors_temp.pop(0)
        valors_hum.pop(0)
        valors_med_temp.pop(0)
        valors_med_hum.pop(0)

    while temps and temps_actual - temps[0] > temps_max:
        temps.pop(0)
        valors_temp.pop(0)
        valors_hum.pop(0)
        valors_med_temp.pop(0)
        valors_med_hum.pop(0)

    # Temperatura
    ax1.clear()
    ax1.plot(temps, valors_temp, color='red')
    ax1.plot(temps, valors_med_temp, color ='red', alpha=0.4)
    ax1.set_title("Temperatura (ºC)")
    ax1.set_xlabel("Temps (s)")
    ax1.set_ylabel("ºC")
    ax1.grid(True)


    # Humitat
    ax2.clear()
    ax2.plot(temps, valors_hum, color='blue')
    ax2.plot(temps, valors_med_hum, color = 'blue', alpha = 0.4)
    ax2.set_title("Humitat (%)")
    ax2.set_xlabel("Temps (s)")
    ax2.set_ylabel("%")
    ax2.grid(True)

    canvas1.draw()
    canvas2.draw()

# ---------- CREACIÓ DE LA FINESTRA ----------
window = Tk()
menu_bar = Menu(window)
window.config(menu=menu_bar)
window.geometry("900x600")
window.title("Monitor de Recepció de Dades del Satèl·lit")
window.rowconfigure([0,1,2,3,4,5,6], weight=1)
window.columnconfigure([0,1,2,3,4,5,6], weight=1) 
radar = RadarPlot(window)
groundtrack = GroundTrackPlot(window)



tituloLabel = Label(window, text="Monitor de dades del Satèl·lit", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky=N+S+E+W)

fraseEntry = Entry(window)
fraseEntry.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=N+S+E+W)

EntrarButton = Button(window, text="Entrar", bg='red', fg="white", command=EntrarClick)
EntrarButton.grid(row=1, column=3, padx=5, pady=5, sticky=N+S+E+W)

AButton = Button(window, text="Parar/Reanudar Transmissió", bg='red', fg="white", command=AClick)
AButton.grid(row=2, column=0, padx=5, pady=5, sticky=N+S+E+W)

BButton = Button(window, text="Mitjana satèl·lit/terra", bg='yellow', fg="black", command=BClick)
BButton.grid(row=2, column=1, padx=5, pady=5, sticky=N+S+E+W)

CButton = Button(window, text="Menú Configuració", bg='blue', fg="white", command=CClick) # Placeholder
CButton.grid(row=2, column=2, padx=5, pady=5, sticky=N+S+E+W)

DButton = Button(window, text="PLACEHOLDER (D)", bg='orange', fg="black") # Placeholder
DButton.grid(row=2, column=3, padx=5, pady=5, sticky=N+S+E+W)
# ---------- GRÀFIQUES ----------
fig1 = Figure(figsize=(3.5, 2.5), dpi=100)
ax1 = fig1.add_subplot(111)
canvas1 = FigureCanvasTkAgg(fig1, master=window)
canvas1.get_tk_widget().grid(row=0, rowspan=3, column=4, columnspan=3, padx=5, pady=5, sticky=N+S+E+W)
fig1.patch.set_facecolor('#f0f0f0')

fig2 = Figure(figsize=(3.5, 2.5), dpi=100)
ax2 = fig2.add_subplot(111)
canvas2 = FigureCanvasTkAgg(fig2, master=window)
canvas2.get_tk_widget().grid(row=3, rowspan=3, column=4, columnspan=3, padx=5, pady=5, sticky=N+S+E+W)
fig2.patch.set_facecolor('#f0f0f0')

# ---------- ETIQUETES DE DADES ----------
temperatura = StringVar(value="-- ºC")
humitat = StringVar(value="-- %")
transmissio = StringVar(value="--")

# Assignem les posicions de cada dada/text
Label(window, text="Temperatura:").grid(row=3, column=0, sticky=E)
Label(window, textvariable=temperatura).grid(row=3, column=1, sticky=W)
Label(window, text="Humitat:").grid(row=3, column=2, sticky=E)
Label(window, textvariable=humitat).grid(row=3, column=3, sticky=W)
Label(window, textvariable=transmissio).grid(row=6, column=6, sticky=E)

estadoLabel = Label(window, text="Transmissió: ACTIVA", fg="green")
estadoLabel.grid(row=6, column=0, columnspan=2, pady=10)
mitjana_Label = Label(window, text="Mitjana des del satèl·lit", fg="green")
mitjana_Label.grid(row=6, column=2, columnspan=2, pady=10)
error_Label = Label(window, text="Sense errors", fg="green")
error_Label.grid(row=6, column=4, columnspan=2, pady=10)

# ---------- MENÚ D'AJUDA (HELP) ----------
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Instruccions Satèl·lit", command=mostrar_instruccions)
menu_bar.add_cascade(label="Ajuda", menu=help_menu)


# ---------- EXECUCIÓ DEL FIL DE LECTURA ----------
thread = threading.Thread(target=serial_thread, daemon=True)
thread.start()


window.mainloop()