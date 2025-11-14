#include <DHT11.h>
#include <SoftwareSerial.h>

int temp = 0;
int hum = 0;
String dades_dht = "0";
String dades = "0";
String mitjanes = "0";
int error_dht = 0;
int error_ultrasons = 0;
int mitjana = 0; // 0 sat, 1 terra
int errors = 0;
DHT11 dht11(2);

int med_temp[10];
int med_hum[10];

void setup() {
  Serial.begin(9600);
  // Primeres lectures:
  temp = dht11.readTemperature();
  hum = dht11.readHumidity();
}

void loop() {
  dades_dht = "0";
  temp = dht11.readTemperature();
  hum = dht11.readHumidity();
  // Muntem String dades_dht:
  if(temp > 100 && hum > 100){
    error_dht = 1;
  }else if(temp > 100){
    error_dht = 2;
    dades_dht = String(hum); // Mos saltem la temperatura
  }else if(hum > 100){
    error_dht = 3;
    dades_dht = String(temp); // Mos saltem la humitat
  }else{
    error_dht = 0;
    dades_dht = String(temp) + "," + String(hum);
  }

  //Gestió d'error. Lo últim, abans d'enviar
  // Error DHT (0, tot bé; 1, temp i hum; 2, temps; 3, hum) => Posició 0 (temp) i 1 (hum)
  // Error ULTRASONS => Posició 2
  errors = "0";
  if (error_dht == 1) {
    // posició 0 a 1, posició 1 a 1
    errors += 1; // 2^0
    errors += 2; // 2^1

  } else if (error_dht == 2) {
    // posició 0 a 1, posició 1 a 0
    errors += 1; // 2^1
  } else if (error_dht == 3) {
    // posició 0 a 0, posició 1 a 1
    errors += 2; // 2^1
  }
  if (error_ultrasons == 1){
    errors += 4; // 2^2
  }
  if (mitjana == 0){
    errors += 8; // 2^3
    mitjanes = String()

  }

}
