import tkinter as tk
from tkinter import messagebox
import threading
import time
import pygame
import os
import sys

# --- CONFIGURACIÓ DEL FITXER ---
# Detecta automàticament el directori de l’script
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
ALARMA_PATH = os.path.join(BASE_DIR, "alarma.mp3")

# --- CONFIGURACIÓ DEL SO ---
pygame.mixer.init()

# --- VARIABLES GLOBALS ---
alarma_activada = False
fi_alarma = False

# --- FUNCIONS ---
def reproduir_alarma():
    """Reprodueix el fitxer d'alarma en bucle"""
    if not os.path.exists(ALARMA_PATH):
        messagebox.showerror("Error", f"No s'ha trobat el fitxer:\n{ALARMA_PATH}")
        return
    pygame.mixer.music.load(ALARMA_PATH)
    pygame.mixer.music.play(loops=-1)

def aturar_alarma():
    """Atura el so"""
    pygame.mixer.music.stop()

def parpelleig_label():
    """Canvia el color del label per simular parpelleig"""
    if not alarma_activada:
        return
    color_actual = label.cget("fg")
    nou_color = "red" if color_actual == "black" else "black"
    label.config(fg=nou_color)
    label.after(500, parpelleig_label)  # repeteix cada 500 ms

def toggle_alarma():
    """Activa o desactiva l'alarma"""
    global alarma_activada, fi_alarma
    if not alarma_activada:
        alarma_activada = True
        fi_alarma = False
        label.config(text="🚨 ALARMA ACTIVADA! 🚨", fg="red")
        alarma_activada = True
        reproduir_alarma()
        parpelleig_label()
        threading.Thread(target=temporitzador, daemon=True).start()
    else:
        fi_alarma = True
        desactivar()

def desactivar():
    """Desactiva l'alarma completament"""
    global alarma_activada
    alarma_activada = False
    aturar_alarma()
    label.config(text="Alarma desactivada", fg="black")

def temporitzador():
    """Desactiva automàticament l'alarma després de 10 segons"""
    global fi_alarma
    temps_inici = time.time()
    while time.time() - temps_inici < 10:
        if fi_alarma:
            return
        time.sleep(0.1)
    if not fi_alarma:
        fi_alarma = True
        desactivar()

# --- INTERFÍCIE TKINTER ---
root = tk.Tk()
root.title("Alarma Tkinter")
root.geometry("320x160")

label = tk.Label(root, text="Alarma desactivada", font=("Arial", 14))
label.pack(pady=20)

boto = tk.Button(root, text="Activar / Desactivar", command=toggle_alarma, font=("Arial", 12))
boto.pack()

root.mainloop()
