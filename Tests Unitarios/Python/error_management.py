def parse_trozos(trozos):
    i = trozos[0]
    error_code = trozos[1]

    bits = format(error_code, "04b")

    temp_err   = bits[-1] == "1"
    hum_err    = bits[-2] == "1"
    ultra_err  = bits[-3] == "1"
    median_on  = bits[-4] == "1"

    index = 2
    temp = hum = angle = dist = med_temp = med_hum = -1

    if not temp_err:
        temp = trozos[index]; index += 1
    if not hum_err:
        hum = trozos[index]; index += 1
    if not ultra_err:
        angle = trozos[index]; dist = trozos[index + 1]; index += 2
    if median_on:
        med_temp = trozos[index]; med_hum = trozos[index + 1]; index += 2

    return i, error_code, temp, hum, angle, dist, med_temp, med_hum


if __name__ == "__main__":
    entrada = input("Enter the values separated by commas: ")
    trozos = [int(x) for x in entrada.split(",")]

    i, error_code, temp, hum, angle, dist, med_temp, med_hum = parse_trozos(trozos)

    print("\n--- Parsed Values ---")
    print(f"i: {i}")
    print(f"Error code: {error_code} (binary: {format(error_code, '04b')})")
    print(f"Temperature: {temp}")
    print(f"Humidity: {hum}")
    print(f"Angle: {angle}")
    print(f"Distance: {dist}")
    print(f"Median Temperature: {med_temp}")
    print(f"Median Humidity: {med_hum}")
