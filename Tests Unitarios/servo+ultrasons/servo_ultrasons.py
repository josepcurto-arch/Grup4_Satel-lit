import matplotlib.pyplot as plt
import numpy as np

# SEMICIRCUMFERÈNCIA DE FONS
theta = np.linspace(0, np.pi, 181)   # Angles de 0 a 180 graus
r = np.full_like(theta, 200)         # Radi màxim

fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(111, polar=True)

# Dibuixar semicircumferència com a scatter o línia
ax.plot(theta, r, color='lightgray', linewidth=2, linestyle='--')

# Configuració semicercle
ax.set_thetamin(0)
ax.set_thetamax(180)
ax.set_theta_zero_location("W")
ax.set_theta_direction(-1)
ax.set_ylim(0, 200)

# Dades de radar inicials (vacies)
line, = ax.plot([], [], 'go-', linewidth=2)

angles = []
distancies = []

print("Introdueix les dades en format: distancia:angle,distancia:angle,...")

for _ in range(10):  # Llegir 10 vegades
    data = input("Dades: ").strip()
    if data:
        try:
            parelles = data.split(',')
            angles.clear()
            distancies.clear()
            for p in parelles:
                dist_str, angle_str = p.split(':')
                dist = float(dist_str)
                angle = float(angle_str)
                if 0 <= angle <= 180:
                    theta_point = np.deg2rad(angle)
                    angles.append(theta_point)
                    distancies.append(dist)

            line.set_data(angles, distancies)
            plt.draw()
            plt.pause(0.5)

        except ValueError:
            print("Format incorrecte! Usa distancia:angle,...")
