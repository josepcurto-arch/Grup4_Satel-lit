import serial
import matplotlib.pyplot as plt
import numpy as np

#CONFIGURACIÓ DEL PORT SÈRIE
arduino = serial.Serial('COM5', 9600, timeout=1) #modificar port depenent de cadascú

#CONFIGURACIÓ DE LA GRÀFICA
plt.ion()
fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(111, polar=True)
ax.set_ylim(0, 200)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
line, = ax.plot([], [], 'go-', linewidth=2)

angles = []
distancies = []

while True:
    data = arduino.readline().decode().strip()
    if data:
        try:
            angle_str, dist_str = data.split(',')
            angle = float(angle_str)
            dist = float(dist_str)

            theta = np.deg2rad(angle)
            angles.append(theta)
            distancies.append(dist)

            if len(angles) > 181:
                angles.pop(0)
                distancies.pop(0)

            line.set_data(angles, distancies)
            ax.set_title("Radar amb HC-SR04", va='bottom', fontsize=14)
            plt.pause(0.001)

        except ValueError:
            pass

