#include <DHT11.h>
#include <SoftwareSerial.h>
#include <Servo.h>
DHT11 dht11(2);                   // Pin de datos (S) al D2
SoftwareSerial mySerial(10, 11);  // RX, TX

int t, h;
int tx = 1;  //comença en 1 perque comenci donant dades
int mitjan = 0;
int i = 1;
int a = 1;
int b = 0;
int c = 0;
int d = 0;
int e = 0;
String dades = "0";
String dades_dht = "0";
int error = 0;
const int trig = 9;
const int echo = 8;
float durada;
int distancia[18] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
Servo servo;
int angle[18] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
int angle_act = 0;
String dades_ultrasons = "0";
int errors = 0;
int error_dht = 0;
int error_ultrasons = 0;
String mitjanes = "0";
int medt;
int medh;
String msg = "s";

int med_temp[10];
int med_hum[10];

unsigned long interval = 5000;  // Default: 5 seconds
unsigned long lastTime = 0;     // Used for millis()

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
  servo.attach(3);

  med_temp[0] = dht11.readTemperature();
  med_hum[0] = dht11.readHumidity();
  while (a != 10) {
    med_temp[a] = med_temp[0];
    med_hum[a] = med_hum[0];
    a = a + 1;
  }
  a = 0;
}

void loop() {
  unsigned long now = millis();
  if (now - lastTime >= interval) {
    lastTime = now;
    // Llegir ordres del port sèrie
    if (mySerial.available() > 0) {
      msg = mySerial.readStringUntil('\n');
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
      } else if (msg == "MI0") {
        //mitjan = 0;
        Serial.println("Mitjana des del satèl·lit");
      } else if (msg == "MI1") {
        mitjan = 1;
        Serial.println("Mitjana des de terra");
      } else if (input.startsWith("T ")) {
        String numString = input.substring(2);  // Everything after "T "
        int seconds = numString.toInt();        // Convert to integer
        if (seconds > 0) {
            interval = (unsigned long)seconds * 1000;  // convert to ms
        }
      }
    }
  
    // Guardar valors al vector de les mitjanes
    int temp = dht11.readTemperature();
    int hum = dht11.readHumidity();
    med_temp[a] = temp;
    med_hum[a] = hum;
    a = a + 1;
    if(a == 10){
      a = 0;
    }
  
    // Enviar dades si la transmissió està activa
  
    if (tx == 1) {
  
      // Muntem String dades_dht:
      if (temp > 100 && hum > 100) {
        error_dht = 1;
  
      } else if (temp > 100) {
        error_dht = 2;
        dades_dht = String(hum);  // Mos saltem la temperatura
      } else if (hum > 100) {
        error_dht = 3;
        dades_dht = String(temp);  // Mos saltem la humitat
      } else {
        error_dht = 0;
        dades_dht = String(temp) + "," + String(hum);
      }
      Serial.print("Dades DHT: ");
      Serial.println(dades_dht);
      //Gestió d'error. Lo últim, abans d'enviar
      // Error DHT (0, tot bé; 1, temp i hum; 2, temps; 3, hum) => Posició 0 (temp) i 1 (hum)
      // Error ULTRASONS => Posició 2
      errors = 0;
      if (error_dht == 1) {
        // posició 0 a 1, posició 1 a 1
        errors += 1;  // 2^0
        errors += 2;  // 2^1
  
      } else if (error_dht == 2) {
        // posició 0 a 1, posició 1 a 0
        errors += 1;  // 2^1
      } else if (error_dht == 3) {
        // posició 0 a 0, posició 1 a 1
        errors += 2;  // 2^1
      }
      d = 0;
      c = 0;
      while(c != 18){
        error_ultrasons = 0;
        if(distancia[c] < 0 || distancia[c] > 400){
          error_ultrasons = 1;
          distancia[c] = -1;
          angle[c] = -1;
        } else if(d == 0){
          dades_ultrasons = "," + String(distancia[c]) + ";" + String(angle[c]);
          d = 1;
        } else{
          dades_ultrasons += "," + String(distancia[c]) + ";" + String(angle[c]);
        }
        c++;
  
      }
      if (error_ultrasons == 1) {
        errors += 4;  // 2^2
      }
      if (mitjan == 0) {
        errors += 8;  // 2^3
        while (b != 10) {
          medt += med_temp[b];
          medh += med_hum[b];
          b++;
        }
        b = 0;
        medt = medt / 10;
        medh = medh / 10;
        
        mitjanes = "," + String(medt) + "," + String(medh); // Temporal
      }
  
      dades = String(i) + "," + errors;
      if (error_dht != 1) {
        dades += "," + dades_dht;
      }
      if (d == 1) { // Alguna dada és vàlida
        dades += dades_ultrasons;
      }
      if (mitjan != 1) {
        dades += mitjanes;
      }
      Serial.println(dades);
      mySerial.println(dades);
      i++;
    }
  
    angle_act = 0;
    for (e = 0; e != 18; e++) {
      servo.write(angle_act);
      delay(30);
      digitalWrite(trig, LOW);
      delay(2);
      digitalWrite(trig, HIGH);
      delay(10);
      digitalWrite(trig, LOW);
      durada = pulseIn(echo, HIGH);
      distancia[e] = int(durada) * 0.034 / 2;
      angle[e] = angle_act;
      angle_act += 10;
    }
  }
}
