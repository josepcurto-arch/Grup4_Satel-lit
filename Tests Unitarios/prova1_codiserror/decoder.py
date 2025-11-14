import serial
device = 'COM3' 
baudrate = 9600
try:              # Intentem establir comunicació amb el port sèrie
    mySerial = serial.Serial(device, baudrate, timeout=1)
    print("Port sèrie obert:", device)
except Exception as e:                  # Si no es pot, surt un missatge d'error
    print("No s'ha pogut obrir el port sèrie:", e)
    mySerial = None

# Rebem a linea
linea = mySerial.readline().decode('utf-8').rstrip()
trozos = linea.split(',')
