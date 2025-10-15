#include <DHT11.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11); // RX, TX 
DHT11 dht11(2); // Pin D2

int t, h;
int tx = 1; //comença en 1 perque comenci donant dades 
int i = 1;

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
}

void loop() {
  // Enviar dades si la transmissió està activa
  if (tx == 1) {
    int temp = dht11.readTemperature();
    int hum = dht11.readHumidity();
    String dades = String(temp) + "," + String(hum) + "," + String(i);
    Serial.println(dades);
    mySerial.println(dades);
    i++;
  }

  // Llegir ordres del port sèrie
  if (mySerial.available() > 0) {
    String msg = mySerial.readStringUntil('\n');
    msg.trim();

    //parar la transmissió
    if (msg == "TX0") {
      tx = 0;
      Serial.println("Transmissió parada");
    } 
    //reanudar la transmissió
    else if (msg == "TX1") {
      tx = 1;
      Serial.println("Transmissió reanudada");
    } 
  }

  delay(3000);
}


