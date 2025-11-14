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
except Exception as e:                  # Si no es pot, surt un missatg e d'error
    print("No s'ha pogut obrir el port sèrie:", e)
    mySerial = None

# ---------- VARIABLES GLOBALS ----------
transmissio_activa = True
temps = []
temps_inicial = time.time()
temps_max=30
temps_max_punts = 50
temps_ultima_dada=time.time()
valors_temp = []
valors_hum = []
time_control = 0
mitjana_satelit = 0
dist_list_global = []   # Per guardar totes les distàncies
angle_list_global = []  # Per guardar tots els angles corresponents
med_temp_list = [0]*10
med_hum_list  = [0]*10


# ---------- FUNCIONS ----------
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

def BClick():
    global mitjana_satelit
    mitjana_satelit = not mitjana_satelit
    if mySerial and mySerial.is_open:
        try:
            if mitjana_satelit == 0:
                mySerial.write(b"MI0\n")
                mitjana_Label.config(text="Mitjana des del satèl·lit", fg="green")
                print("Enviat: MI0 (satèl·lt)")
            else:
                mySerial.write(b"MI1\n")
                mitjana_Label.config(text="Mitjana des de terra", fg="green")
                print("Enviat: MI1 (terra)")
        except Exception as e:
            print("Error enviant:", e)


# Extraure dades rebudes:
def parse_trozos(trozos):
    i = int(trozos[0])
    error_code = int(trozos[1])
    bits = format(error_code, "04b")

    temp_err   = bits[-1] == "1"
    hum_err    = bits[-2] == "1"
    ultra_err  = bits[-3] == "1"
    median_on  = bits[-4] == "1"

    index = 2
    temp = hum = -1
    medt = medh = -1

    # Temps i humitat
    if not temp_err and index < len(trozos):
        try:
            temp = int(trozos[index])
        except:
            temp = -1
        index += 1

    if not hum_err and index < len(trozos):
        try:
            hum = int(trozos[index])
        except:
            hum = -1
        index += 1

    # Parells distància;angle
    dist_list = []
    angle_list = []
    while index < len(trozos):
        entry = trozos[index].strip()
        if ";" in entry:
            parts = entry.split(";")
            try:
                dist_list.append(int(parts[0]))
                angle_list.append(int(parts[1]))
            except:
                pass  # Si algun valor és invàlid, simplement l'ignorem
            index += 1
        else:
            break  # Els camps que no tenen ";" són finals

    # Variables finals (mitjana, etc.)
    if median_on == 1 and index < len(trozos):
        try:
            medt = int(trozos[index])
            medh = int(trozos[index + 1])
        except:
            medt = medh = -1

    return i, error_code, temp, hum, dist_list, angle_list, medt, medh, temp_err, hum_err, ultra_err, median_on

def mostrar_instruccions():
    instruccions = (
        "Instruccions Port sèrie amb el Satèl·lit:\n"
        " - TX0/TX1: Atura/Reanuda la transmissió (igual que el botó corresponent)\n"
        " - MI0/MI1: Càlcul de les mitjanes al satèl·lit/a terra (igual que el botó corresponent)\n"
        " - T X: Ajustar el temps de transmissió, on X representa el temps en segons\n"
        "   entre cada transmissió (ex. T 2) (pot haver-hi errors per a intervals inferiors a 1 segon)"
    )
    messagebox.showinfo("Instruccions", instruccions)

# ---------- FUNCIONS DE LECTURA SÈRIE ----------
def serial_thread():
    global temps_ultima_dada
    timer_actualitzacio_grafica = time.time() + 0.1
    while True:
        #if mySerial and mySerial.in_waiting > 0:
        try:
            #linea = mySerial.readline().decode('utf-8').rstrip()
            linea = "129,8,22,53,23;0,22;10,23;20,22;30,23;40,22;50,22;60,23;70,23;80,22;90,23;100,23;110,22;120,23;130,23;140,22;150,23;160,23;170,24,58"
            if linea:
                global time_control; global alarma_activada
                global temp_err; global hum_err; global ultra_err
                error_Label.config(text="Sense errors", fg="green")
                time_control = 0
                print("Rebut:", linea)
                trozos = linea.split(',')
                print("Trozos:", trozos)
                if len(trozos) >= 4:                      # Assignem les variables a cada tros de les dades rebudes
                    i, error_code, temp, hum, dist_list, angle_list, medt, medh, temp_err, hum_err, ultra_err, median_on = parse_trozos(trozos)
                    print(f"Index: {i}, Error Code: {error_code}, Temp: {temp}, Hum: {hum}, Med Temp: {medt}, Med Hum: {medh}")
                    dist_list_global = dist_list
                    angle_list_global = angle_list
                    temperatura.set(f"{temp} ºC")
                    humitat.set(f"{hum} %")
                    transmissio.set(i)
                    control = 0
                    bits = format(error_code, "04b")
                    median_on  = bits[-4] == "1"
                    if i == 1:     #Primera lectura per posar-ho tot al valor inicial
                        med_temp_list[0] = temp
                        med_hum_list[0] = hum

                        a = 0
                        while a!=10:
                            med_temp_list[i]=med_temp_list[0]
                            med_hum_list[i]=med_hum_list[0]
                            a=a+1
                    a = 0
                    #Cada vegada:
                    med_temp_list[a] = temp
                    med_hum_list[a] = hum
                    a = a+1                        
                    if a == 10:
                        a = 0
                    if not median_on:
                        while b != 10:
                            medt = medt[b]
                            medh = medh[b]
                            b = b + 1
                        medt = medt / 10
                        medh = medh / 10 # Les variables medt i medh contenen l'última mitjana calculada
                    if temp_err != 0:
                        print("Error Temperatura")
                        control = 1
                        error_Label.config(text="Error Temperatura", fg="red")
                            
                    if hum_err != 0:
                        print("Error Humitat")
                        control = 1
                        error_Label.config(text="Error Humitat", fg="red")

                    if ultra_err != 0:
                        print("Error Ultrasons")
                        control = 1 
                        error_Label.config(text="Error Ultrasons", fg="red")

                    elif control == 0:
                        actualitza_grafiques(temp, hum)
                        error_Label.config(text="Sense errors", fg="green")
                        temps_ultima_dada = time.time()
        except Exception as e:
            print("Error en la lectura sèrie:", e)

        if time.time() - temps_ultima_dada >= 5 and time_control == 0:
            if not valors_temp or valors_temp[-1] is not None:
                actualitza_grafiques(None, None)
            print("No es reben dades des de fa mes de 5 segons!")
            error_Label.config(text="Sense recepció", fg="red")
            time_control = 1
            

        if time.time() >= timer_actualitzacio_grafica:
            canvas1.draw()
            canvas2.draw()
            timer_actualitzacio_grafica = time.time() + 0.1
        time.sleep(0.1)

# ---------- ACTUALITZAR GRÀFIQUES ----------
def actualitza_grafiques(temp, hum):
    global temps_ultima_dada
    temps_actual = time.time() - temps_inicial
    temps.append(temps_actual)
    temps_ultima_dada = time.time()
    valors_temp.append(temp)
    valors_hum.append(hum)

    if len(temps) > temps_max_punts:   # Desplacem la gràfica del temps quan arribi a un determinat instant per tal de no comprimir la gràfica
        temps.pop(0)
        valors_temp.pop(0)
        valors_hum.pop(0)

    while temps and temps_actual - temps[0] > temps_max:
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
menu_bar = Tk.Menu(root)
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

BButton = Button(window, text="Mitjana satèl·lit/terra", bg='yellow', fg="black", command=BClick)
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
estadoLabel.grid(row=6, column=0, columnspan=2, pady=10)
mitjana_Label = Label(window, text="Mitjana des del satèl·lit", fg="green")
mitjana_Label.grid(row=6, column=2, columnspan=2, pady=10)
error_Label = Label(window, text="Sense errors", fg="green")
error_Label.grid(row=6, column=4, columnspan=2, pady=10)

# ---------- MENÚ D'AJUDA (HELP) ----------
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Instruccions Satèl·lit", command=mostrar_instruccions)

# ---------- EXECUCIÓ DEL FIL DE LECTURA ----------
thread = threading.Thread(target=serial_thread, daemon=True)
thread.start()


window.mainloop()


