import time

# ---------- VARIABLES GLOBALS ----------
temps_ultima_dada = time.time()
valors_temp = []
valors_hum = []
a = 0  # Índex per a mitjana mòbil
med_temp = [0]*10
med_hum = [0]*10

# ---------- FUNCIONS ----------

def parse_trozos(trozos):
    """
    Rep una llista de strings separats per ',' i extreu les dades.
    Retorna:
    i, error_code, temp, hum, dist_list, angle_list, med_temp, med_hum, temp_err, hum_err, ultra_err, median_on
    """
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
    dist_list = []
    angle_list = []

    # Temperatura
    if not temp_err and index < len(trozos):
        temp = int(trozos[index])
        index += 1

    # Humitat
    if not hum_err and index < len(trozos):
        hum = int(trozos[index])
        index += 1

    # Ultrasons: tot el que segueix amb format "dist;angle"
    while index < len(trozos):
        entry = trozos[index].strip()
        if ";" in entry:
            parts = entry.split(";")
            try:
                dist_list.append(int(parts[0]))
                angle_list.append(int(parts[1]))
            except:
                # Si algun valor no és enter, el saltem
                pass
            index += 1
        else:
            break  # S'ha acabat la seqüència de dist;angle

    # Mitjana del satèl·lit si existeix
    if median_on and index+1 < len(trozos):
        try:
            medt = int(trozos[index])
            medh = int(trozos[index+1])
        except:
            medt = medh = -1

    return i, error_code, temp, hum, dist_list, angle_list, medt, medh, temp_err, hum_err, ultra_err, median_on


def processar_linea(linea):
    """
    Processa una línia de dades, actualitza mitjanes i mostra resultats.
    """
    global temps_ultima_dada, a, med_temp, med_hum, valors_temp, valors_hum

    linea = linea.strip()
    if not linea:
        return

    trozos = linea.split(',')
    if len(trozos) < 4:
        print("Dades insuficients:", linea)
        return

    i, error_code, temp, hum, dist_list, angle_list, medt, medh, temp_err, hum_err, ultra_err, median_on = parse_trozos(trozos)

    print(f"\n--- Lectura {i} ---")
    print(f"Temperatura: {temp} ºC, Humitat: {hum} %")
    print(f"Error Code: {error_code} -> bits: {format(error_code,'04b')}")
    if temp_err: print("⚠️ Error Temperatura")
    if hum_err: print("⚠️ Error Humitat")
    if ultra_err: print("⚠️ Error Ultrasons")
    if median_on: print("Mitjana activada des de satèl·lit")

    # Mostrar totes les distàncies i angles
    if dist_list and angle_list:
        print("Ultrasons:")
        for d, ang in zip(dist_list, angle_list):
            print(f"  Distància={d} cm, Angle={ang} º")

    # Actualitza mitjana mòbil
    if temp != -1:
        med_temp[a] = temp
        valors_temp.append(temp)
    if hum != -1:
        med_hum[a] = hum
        valors_hum.append(hum)
    a += 1
    if a == 10:
        a = 0

    # Càlcul mitjana si no està activada la mitjana des del satèl·lit
    if not median_on:
        mitjana_temp = sum(med_temp)/10
        mitjana_hum  = sum(med_hum)/10
        print(f"Mitjana mòbil (últims 10 punts): Temp={mitjana_temp:.1f} ºC, Hum={mitjana_hum:.1f} %")
    else:
        print(f"Mitjana satèl·lit: Temp={medt}, Hum={medh}")

    temps_ultima_dada = time.time()


# ---------- BUCLE PRINCIPAL ----------
print("Introduïu dades simulant la transmissió del satèl·lit. Escriviu 'exit' per sortir.")
while True:
    linea = input("Dada> ")
    if linea.lower() == 'exit':
        break
    processar_linea(linea)

print("\nFinalitzant programa.")
