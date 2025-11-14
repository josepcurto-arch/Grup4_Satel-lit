
med_temp = [0]
med_hum = [0]
a = 1
#Primera lectura per posar-ho tot al valor inicial
med_hum[0] = temp
med_temp[0] = hum

while a!=10:
    med_temp[i]=med_temp[0]
    med_temp[i]=med_temp[0]
    a=a+1
a = 0

while a:
    hum, temp = Adafruit_DHT.read_rentry(sensor, pin)
    med_temp[a] = temp
    med_hum[a] = hum
    a = a+1
    if a == 10:
        a = 0