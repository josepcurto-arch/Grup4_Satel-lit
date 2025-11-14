# Grup4_Satèl·lit
Repositori amb els arxius del projecte del satèl·lit del grup 4, format per Alba Jarrett, Alex Minghao Tong i Josep Curto, per a l'assignatura de Ciències de la Computació.


 <b> Entrega actual publicada:  </b> Versió 2 (faltant el vídeo)

 <b> Video Versió 1:  </b> <br> 
 [![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/KC8rA3bHNaE/0.jpg)](https://www.youtube.com/watch?v=KC8rA3bHNaE)

 Funcionalitats disponibles:
 - 
   - El satèl·lit llegeix i envia correctament les dades de Temperatura i Humitat del DHT11
   - L'estació de terra rep les dades correctament i les mostra a una interficie gràfica.
   - A l'interficie, l'usuari pot para i reanudar la transmissió de dades, així com veure-les amb gràfiques.
   - L'estació de terra dectecta dades errònies de temperatura, humitat o si no s'ha rebut informació durant massa temps.

Parts importants del codi
- 

PYTHON: Rebre les dades pel port sèrie i analitzar-les en busca d'errors (Format: temp,hum,nºtransmissió):
```
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
```
PYTHON: Gràfiques integrades al Tkinter:
```
fig1 = Figure(figsize=(3.5, 2.5), dpi=100)
ax1 = fig1.add_subplot(111)
canvas1 = FigureCanvasTkAgg(fig1, master=window)
canvas1.get_tk_widget().grid(row=0, rowspan=3, column=4, columnspan=3, padx=5, pady=5, sticky=N+S+E+W)
fig1.patch.set_facecolor('#f0f0f0') // Color igual que el fons per defecte del Tkinter, sinó surt blanc
```
ARDUINO RECEPTOR: Controlar si s'ha perdut alguna recepció (fa més de 4 segons que no es rep res (amb temps de transmisió a 3 segons)):
```
// Al if (mySerial.available()), s'assigna rxage a millis();
unsigned long timerx = millis() - rxage;
   if(timerx > 4000 || check == 1) {
      digitalWrite(LED_BUILTIN, HIGH);
   } else {
      digitalWrite(LED_BUILTIN, LOW);
   }
```
