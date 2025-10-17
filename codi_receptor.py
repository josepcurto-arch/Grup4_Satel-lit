from tkinter import *
from tkinter import messagebox
import tkinter as tk
import serial
import threading
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------- CONFIGURACIÓ DEL PORT SÈRIE ----------
device = 'COM6'   # Canvia-ho segons el teu cas
baudrate = 9600

try:              # Intentem establir comunicació amb el port sèrie
    mySerial = serial.Serial(device, baudrate, timeout=1)
    print("Port sèrie obert:", device)
except Exception as e:                  # Si no es pot, surt un missatge d'error
    print("No s'ha pogut obrir el port sèrie:", e)
    mySerial = None

# ---------- VARIABLES GLOBALS ----------
transmissio_activa = True
temps = []
temps_inicial = time.time()
temps_max_punts = 50
valors_temp = []
valors_hum = []

# ---------- FUNCIONS DE BOTONS ----------
def EntrarClick():
    text = fraseEntry.get()
    print(f'Has introduït: "{text}"')
    if mySerial and mySerial.is_open:
        try:
            mySerial.write((text + "\n").encode('utf-8'))
            print("Enviat pel port sèrie:", text)
        except Exception as e:
            print("Error enviant:", e)

def AClick():
    global transmissio_activa
    transmissio_activa = not transmissio_activa
    if mySerial and mySerial.is_open: 
        try:
            if transmissio_activa:
                mySerial.write(b"TX1\n")
                estadoLabel.config(text="Transmissió: ACTIVA", fg="green")
                print("Enviat: TX1 (reanudar transmissió)")
            else:
                mySerial.write(b"TX0\n")
                estadoLabel.config(text="Transmissió: PARADA", fg="red")
                print("Enviat: TX0 (parar transmissió)")
        except Exception as e:
            print("Error enviant:", e)

# ---------- FUNCIONS DE LECTURA SÈRIE ----------
def serial_thread():
    while True:
        if mySerial and mySerial.in_waiting > 0:
            try:
                linea = mySerial.readline().decode('utf-8').rstrip()
                if linea:
                    print("Rebut:", linea)
                    trozos = linea.split(',')
                    if len(trozos) == 3:                      # Assignem les variables a cada tros de les dades rebudes
                        temperatura.set(f"{trozos[0]} ºC")
                        humitat.set(f"{trozos[1]} %")
                        transmissio.set(trozos[2])
                        control = 0
                        if float(trozos[0]) < 0 or float(trozos[0]) > 40:
                            root = tk.Tk()
                            root.withdraw()
                            messagebox.showwarning("Advertència", "Dada de Temperatura fora de rang: T: " + trozos[0] + "ºC")
                            control = 1
                        if float(trozos[1]) < 20 or float(trozos[1]) > 90:
                            root = tk.Tk()
                            root.withdraw()
                            messagebox.showwarning("Advertència", "Dada d'Humitat fora de rang: H: " + trozos[1] + "%")  
                        elif control == 0:
                            actualitza_grafiques(float(trozos[0]), float(trozos[1]))
            except Exception as e:
                print("Error en la lectura sèrie:", e)
        time.sleep(0.1)

# ---------- ACTUALITZAR GRÀFIQUES ----------
def actualitza_grafiques(temp, hum):
    temps_actual = time.time() - temps_inicial
    temps.append(temps_actual)
    valors_temp.append(temp)
    valors_hum.append(hum)

    if len(temps) > temps_max_punts:   # Desplacem la gràfica del temps quan arribi a un determinat instant per tal de no comprimir la gràfica
        temps.pop(0)
        valors_temp.pop(0)
        valors_hum.pop(0)

    # Temperatura
    ax1.clear()
    ax1.plot(temps, valors_temp, color='red')
    ax1.set_title("Temperatura (ºC)")
    ax1.set_xlabel("Temps (s)")
    ax1.set_ylabel("ºC")
    ax1.grid(True)

    # Humitat
    ax2.clear()
    ax2.plot(temps, valors_hum, color='blue')
    ax2.set_title("Humitat (%)")
    ax2.set_xlabel("Temps (s)")
    ax2.set_ylabel("%")
    ax2.grid(True)

    canvas1.draw()
    canvas2.draw()

# ---------- CREACIÓ DE LA FINESTRA ----------
window = Tk()
window.geometry("900x600")
window.title("Monitor de Recepció de Dades del Satèl·lit")
window.rowconfigure([0,1,2,3,4,5,6], weight=1)
window.columnconfigure([0,1,2,3,4,5,6], weight=1) 

tituloLabel = Label(window, text="Monitor de dades del Satèl·lit", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky=N+S+E+W)

fraseEntry = Entry(window)
fraseEntry.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=N+S+E+W)

EntrarButton = Button(window, text="Entrar", bg='red', fg="white", command=EntrarClick)
EntrarButton.grid(row=1, column=3, padx=5, pady=5, sticky=N+S+E+W)

AButton = Button(window, text="Parar/Reanudar Transmissió", bg='red', fg="white", command=AClick)
AButton.grid(row=2, column=0, padx=5, pady=5, sticky=N+S+E+W)

BButton = Button(window, text="PLACEHOLDER (B)", bg='yellow', fg="black")
BButton.grid(row=2, column=1, padx=5, pady=5, sticky=N+S+E+W)

CButton = Button(window, text="PLACEHOLDER (C)", bg='blue', fg="white") # Placeholder
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
estadoLabel.grid(row=6, column=0, columnspan=7, pady=10)

# ---------- EXECUCIÓ DEL FIL DE LECTURA ----------
thread = threading.Thread(target=serial_thread, daemon=True)
thread.start()

window.mainloop()