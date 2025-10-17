import serial
import matplotlib.pyplot as plt

device = 'COM3'
mySerial = serial.Serial(device, 9600)
plt.ion()
plt.axis([0,100,20,30])

temperaturas=[]
eje_x=[]
i=0

while True:
   if mySerial.in_waiting > 0:
      linea = mySerial.readline().decode('utf-8').rstrip()
      print(linea)
      trozos = linea.split(',')
      eje_x.append(i)
      temp = float(trozos[0])
      temperaturas.append(temp)
      plt.plot(eje_x, temperaturas)
      plt.title(str(i))
      i = i+1
      plt.draw()
      plt.pause(0.5)