import time
from datetime import datetime
class Events:
    def __init__ (self, temps, tipus, descripcio):
        self.temps = temps
        self.tipus = tipus
        self.descripcio = descripcio

def RegistrarErrors(tipus, descripcio):
    temps = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    error = Events(temps, tipus, descripcio)
    EscriureEvents(error, "registro_eventos.txt")

def EscriureEvents(event, nombreFichero):
    salida = open(nombreFichero, "a")
    salida.write("{} {} {}\n".format(event.temps, event.tipus, event.descripcio))
    salida.close()

def Checksum(trozos):
    valor = 0
    for i in range(len(trozos)):
        suma = ord(trozos[i])
        valor = valor + suma
    checksum = valor%256
    return checksum

def verificarChecksum(trozos, checksum_original):
    nuevoChecksum = Checksum(trozos)
    if checksum_original == nuevoChecksum:
        print("Correcto")
        return True
    else:
        print("Mensaje corrupto!")
        RegistrarErrors("ALARMA:", "Mensaje corrupto")
        return False
