#include <BME280I2C.h>
#include <Wire.h>
#include <Servo.h>
#include <OrbitSim.h>
#include <SoftwareSerial.h>
#include <TinyGPSPlus.h>

// ======================= COMUNICACIÓ PC =======================
static const int PC_RX = 12;   // RX Arduino
static const int PC_TX = 11;   // TX Arduino
SoftwareSerial pcSerial(PC_RX, PC_TX);

// ======================= GPS =======================
static const int GPS_RX = 3;   // RX Arduino (TX GPS)
static const int GPS_TX = 4;   // TX Arduino (RX GPS)
SoftwareSerial gpsSerial(GPS_RX, GPS_TX);
TinyGPSPlus gps;

// ======================= SENSORS ====================
BME280I2C bme;
const int trigPin = 5;
const int echoPin = 6;
const int servoPin = 9;

Servo myservo;

// ======================= VARIABLES ==================
int i = 1;
unsigned long lasttime = 0;

float temp_vec[10] = {0};
float hum_vec[10]  = {0};
float pres_vec[10] = {0};
int vec = 0;

// ======================= STRUCTS ====================
struct DHT_Data {
  int temp;
  int hum;
  int pres;
  int bat;
  float temp_avg;
  float hum_avg;
  float pres_avg;
  float bat_avg;
};

struct ULTRA_Data {
  int angle[10];
  int distance[10];
  int count;
};

struct Commands {
  int maxTemp = 30;
  int minTemp = -10;
  int maxHum  = 100;
  int minHum  = 20;
  int maxPres = 110;
  int minPres = 98;
  int tempsTx = 5;
  int tx_mode = 1;
  int mitj_mode = 1;
  int pos_mode = 1;   // 1 = simulació, 0 = GPS
  int angleFixat = -1;
};

Commands conf;

// ======================= SETUP ======================
void setup() {

  Serial.begin(9600);      // LORA
  gpsSerial.begin(9600);  // GPS
  pcSerial.begin(9600);
  Wire.begin();

  while (!bme.begin()) {
    delay(500);
  }

  int t = bme.temp();
  int h = bme.hum();
  int p = bme.pres() * 0.1;

  for (int k = 0; k < 10; k++) {
    temp_vec[k] = t;
    hum_vec[k]  = h;
    pres_vec[k] = p;
  }

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  myservo.attach(servoPin);

  orbitSetup();
}

// ======================= LOOP =======================
void loop() {

  // --- Lectura contínua GPS ---
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  // --- Rebre comandes per LoRa ---
  if (pcSerial.available()) {
    String linia = pcSerial.readStringUntil('\n');
    conf = decodificaDades(linia);
  }

  // --- Transmissió ---
  if (conf.tx_mode == 1 && millis() - lasttime >= conf.tempsTx * 1000UL) {
    lasttime = millis();

    ULTRA_Data ultra = ULTRA_Read(conf.angleFixat);
    DHT_Data dht = DHT_Read();

    double pos[3];

    if (conf.pos_mode == 1) {
      // ===== SIMULACIÓ =====
      double* p = orbitLoop();
      pos[0] = p[0];
      pos[1] = p[1];
      pos[2] = p[2];
    } else {
      // ===== GPS REAL (ECEF) =====
      if (gps.location.isValid() && gps.altitude.isValid()) {
        gpsToECEF(
          gps.location.lat(),
          gps.location.lng(),
          gps.altitude.meters(),
          pos[0], pos[1], pos[2]
        );
      }
    }

    int error_code = ErrorCode(dht, ultra, conf);
    String data = prepareDataLine(dht, ultra, error_code, conf, pos);
    int checksum = ChecksumTransmissio(data);

    pcSerial.println(String(checksum) + data);
    Serial.println(String(checksum) + data);

    i++;
  }
}

// ======================= GPS → ECEF =================
void gpsToECEF(double lat, double lon, double alt,
               double &x, double &y, double &z) {
  const double a = 6378137.0;
  const double e2 = 6.69437999014e-3;

  lat = radians(lat);
  lon = radians(lon);

  double N = a / sqrt(1 - e2 * sin(lat) * sin(lat));

  x = (N + alt) * cos(lat) * cos(lon);
  y = (N + alt) * cos(lat) * sin(lon);
  z = ((1 - e2) * N + alt) * sin(lat);
}

// ======================= DHT ========================
DHT_Data DHT_Read() {
  DHT_Data r;

  r.temp = bme.temp();
  r.hum  = bme.hum();
  r.pres = bme.pres() * 0.1;

  temp_vec[vec] = r.temp;
  hum_vec[vec]  = r.hum;
  pres_vec[vec] = r.pres;
  vec = (vec + 1) % 10;

  int st = 0, sh = 0, sp = 0;
  for (int k = 0; k < 10; k++) {
    st += temp_vec[k];
    sh += hum_vec[k];
    sp += pres_vec[k];
  }

  int sb = 0;
  for (int j = 0; j < 30; j++) {
    int adc = analogRead(A0);
    float v = ((adc * 5.0) / 1024) * 37500 / 7500;
    r.bat = constrain(map(v * 100, 600, 880, 0, 100), 0, 100);
    sb += r.bat;
  }

  r.temp_avg = st / 10.0;
  r.hum_avg  = sh / 10.0;
  r.pres_avg = sp / 10.0;
  r.bat_avg  = sb / 30.0;

  return r;
}

// ======================= ULTRASONS ==================
ULTRA_Data ULTRA_Read(int an) {
  ULTRA_Data r;
  r.count = 0;

  if (an == -1) {
    for (int a = 0; a <= 9; a++) {
      myservo.write(a * 20);
      delay(50);

      digitalWrite(trigPin, LOW); delayMicroseconds(2);
      digitalWrite(trigPin, HIGH); delayMicroseconds(10);
      digitalWrite(trigPin, LOW);

      long d = pulseIn(echoPin, HIGH, 50000);
      int dist = (d * 0.0343) / 2;

      if (dist > 0) {
        r.distance[r.count] = dist;
        r.angle[r.count] = a * 20;
        r.count++;
      }
    }
  } else {
    myservo.write(an);
    delay(50);

    digitalWrite(trigPin, LOW); delayMicroseconds(2);
    digitalWrite(trigPin, HIGH); delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    long d = pulseIn(echoPin, HIGH, 30000);
    int dist = (d * 0.0343) / 2;

    if (dist > 0) {
      r.distance[0] = dist;
      r.angle[0] = an;
      r.count = 1;
    }
  }
  return r;
}

// ======================= COMMANDS ===================
Commands decodificaDades(String input) {
  Commands d = conf;
  input.trim();

  if (input == "TX1") d.tx_mode = 1;
  else if (input == "TX0") d.tx_mode = 0;
  else if (input == "MI0") d.mitj_mode = 0;
  else if (input == "MI1") d.mitj_mode = 1;
  else if (input == "POS0") d.pos_mode = 0;
  else if (input == "POS1") d.pos_mode = 1;
  else {
    int v[8], idx = 0, last = 0;
    for (int k = 0; k < 8; k++) {
      idx = input.indexOf(',', last);
      v[k] = (idx == -1) ? input.substring(last).toInt()
                         : input.substring(last, idx).toInt();
      last = idx + 1;
    }
    d.maxTemp = v[0]; d.minTemp = v[1];
    d.maxHum  = v[2]; d.minHum  = v[3];
    d.maxPres = v[4]; d.minPres = v[5];
    d.tempsTx = v[6]; d.angleFixat = v[7];
  }
  return d;
}

// ======================= DATA =======================
String prepareDataLine(DHT_Data d, ULTRA_Data u,
                       int err, Commands c, double p[3]) {
  String s = ",";
  s += String(i) + "," + String(err) + ",";
  s += String(p[0], 2) + "," + String(p[1], 2) + "," + String(p[2], 2) + ",";
  s += String(d.bat) + "," + String(d.temp) + "," +
       String(d.hum) + "," + String(d.pres);

  for (int k = 0; k < u.count; k++) {
    s += "," + String(u.distance[k]) + ":" + String(u.angle[k]);
  }

  if (c.mitj_mode == 1) {
    s += "," + String(d.temp_avg, 1) + "," +
         String(d.hum_avg, 1) + "," +
         String(d.pres_avg, 1);
  }
  return s;
}

// ======================= CHECKSUM ===================
int ChecksumTransmissio(String s) {
  int c = 0;
  for (unsigned int k = 0; k < s.length(); k++) c += s[k];
  return c % 256;
}

// ======================= ERRORS =====================
int ErrorCode(DHT_Data d, ULTRA_Data &u, Commands c) {
  int e = 0;
  if (d.temp < c.minTemp || d.temp > c.maxTemp) e |= 1;
  if (d.hum  < c.minHum  || d.hum  > c.maxHum)  e |= 2;
  if (d.pres < c.minPres || d.pres > c.maxPres) e |= 16;
  if (c.mitj_mode == 0) e |= 8;

  if (c.angleFixat == -1) {
    if (u.count < 9) e |= 4;
  } else {
    if (u.count != 1) e |= 4;
  }
  return e;
}
