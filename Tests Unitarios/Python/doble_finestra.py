from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

# Create the main window
window = Tk()
window.geometry("600x600")  # Set window size
window.title("Main Window")

# Variables that the main code will have
max_temp = 30
min_temp = 5
max_hum = 80
min_hum = 10
temps_tx = 5 # Segons


# Function to open a new window
def open_new_window():
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


# Create a label and a button to open the new window
Label(window, text="This is the main window").pack(pady=10)
Button(window, text="Open New Window", command=open_new_window).pack(pady=10)

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
        # Send config_text trough serial port
    else:
        config_text = "N/A"
        messagebox.showerror("Error de Configuració", "Paràmetres invàlids. Si us plau, revisa les teves entrades.")
# Run the Tkinter event loop
window.mainloop()