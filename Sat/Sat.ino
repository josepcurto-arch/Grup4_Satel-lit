#include <DHT11.h>
#include <Servo.h>
#include <OrbitSim.h> // Orbital simulation library

DHT11 dht11(3);                   // Pin de datos (S) al D2
const int trigPin = 5;
const int echoPin = 6;
const int servoPin = 9;
Servo myservo;

// ------- VARIABLES -------
int i = 1;
int temp = 0;
int hum = 0;
float temp_vec[10] = {0};
float hum_vec[10] = {0};
int vec = 0;
float duration;
float distance;
int error_code = 8;
String data = "0";
unsigned long lasttime = 0;
int checksum_value;

struct DHT_Data {
  int temp;
  int hum;
  float temp_avg;
  float hum_avg;
};

struct ULTRA_Data {
  int angle[18];
  int distance[18];
  int count; // number of valid pairs
};

struct Commands {
  int maxTemp = 30;
  int minTemp = 5;
  int tempsTx = 5;
  int maxHum = 100;
  int minHum = 20;
  int tx_mode = 1;
  int mitj_mode = 0; //SAT
};

DHT_Data DHT_Read();
ULTRA_Data ULTRA_Read();
Commands decodificaDades(String input);

// -------------------- SETUP --------------------
void setup() {
  Serial.begin(9600);

  // Initialize the temp/hum buffers with the first reading
  temp = dht11.readTemperature();
  hum = dht11.readHumidity();
  for(vec = 0; vec < 10; vec++){
    temp_vec[vec] = temp;
    hum_vec[vec] = hum;
  }
  vec = 0;

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  myservo.attach(servoPin);
  orbitSetup();
}

Commands conf;
// -------------------- LOOP --------------------
void loop() {

  // Read commands from serial
  if (Serial.available()) {
    String linia = Serial.readStringUntil('\n');
    conf = decodificaDades(linia);
  }

  // Send data periodically
  if(millis() - lasttime >= conf.tempsTx * 1000 && conf.tx_mode == 1){
    lasttime = millis();
    ULTRA_Data u = ULTRA_Read();
    DHT_Data d = DHT_Read();
    double* pos = orbitLoop(); // update orbit position

    error_code = ErrorCode(d, u, conf);
    data = prepareDataLine(d, u, error_code, conf, pos);
    checksum_value = ChecksumTransmissio(data);

    Serial.println(String(checksum_value) + data);

    i++;
  }
}

// -------------------- DHT Read --------------------
DHT_Data DHT_Read() {
  DHT_Data result;

  int currentTemp = dht11.readTemperature();
  int currentHum = dht11.readHumidity();

  temp_vec[vec] = currentTemp;
  hum_vec[vec] = currentHum;
  vec = (vec + 1) % 10;

  int sumTemp = 0, sumHum = 0;
  for(int k = 0; k < 10; k++){
    sumTemp += temp_vec[k];
    sumHum += hum_vec[k];
  }

  float avgTemp = float(sumTemp) / 10;
  float avgHum = float(sumHum) / 10;

  result.temp = currentTemp;
  result.hum = currentHum;
  result.temp_avg = avgTemp;
  result.hum_avg = avgHum;

  return result;
}

// -------------------- Ultrasonic Read --------------------
ULTRA_Data ULTRA_Read() {
  ULTRA_Data result;
  int validCount = 0;

  for(int angIndex = 0; angIndex < 18; angIndex++){
    myservo.write(angIndex * 10);
    delay(25);

    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    duration = pulseIn(echoPin, HIGH, 30000);
    distance = (duration * 0.0343) / 2.0;

    if(distance > 0){
      int dInt = int(distance + 0.5);
      if(dInt < 1) dInt = 1;         // enforce minimum 1 cm
      result.distance[validCount] = dInt;
      result.angle[validCount] = angIndex * 10;
      validCount++;
    }
  }

  result.count = validCount;
  return result;
}

// -------------------- Decode Commands --------------------
Commands decodificaDades(String input) {
  Commands data;
  input.trim();  
  int index = 0;
  int lastIndex = 0;
  float values[5];

  if(input == "TX1"){
    data.tx_mode = 1;
  }else if(input == "TX0"){
    data.tx_mode = 0;
  }else if(input == "MI0"){
    data.mitj_mode = 0; // SAT
  }else if(input == "MI1"){
    data.mitj_mode = 1; //GROUND
  }else if (input.startsWith("T ")) {
    data.tempsTx = input.substring(2).toInt();
  }else{
    for (int i = 0; i < 5; i++) {
      index = input.indexOf(',', lastIndex);
      String temp;
      if (index == -1) temp = input.substring(lastIndex);
      else temp = input.substring(lastIndex, index);
      values[i] = temp.toFloat();
      lastIndex = index + 1;
    }
    data.maxTemp = values[0];
    data.minTemp = values[1];
    data.tempsTx = values[2];
    data.maxHum = values[3];
    data.minHum = values[4];
  }
  return data;
}

// -------------------- Prepare Data Line --------------------
String prepareDataLine(DHT_Data dhtData, ULTRA_Data ultraData, int error_code, Commands dades, double position[3]) {
  String line = ","; // initial comma for checksum

  // Index, error, temp, hum
  line += String(i) + ",";
  line += String(error_code) + ",";
  line += String(position[0]) + ",";
  line += String(position[1]) + ",";
  line += String(position[2]) + ",";
  line += String(dhtData.temp) + ",";
  line += String(dhtData.hum);

  // Append distance:angle pairs (only valid)
  for(int j = 0; j < ultraData.count; j++){
    line += ",";
    line += ultraData.distance[j];
    line += ":";
    line += ultraData.angle[j];
  }

  // Append averages
  if(dades.mitj_mode == 0){
    line += "," + String(dhtData.temp_avg);
    line += "," + String(dhtData.hum_avg);
  }

  return line;
}

// -------------------- Checksum --------------------
int ChecksumTransmissio(String dades) {
  int checksum = 0;

  for (unsigned int i = 0; i < dades.length(); i++) {
    checksum += dades[i];  // add ASCII value of each character
  }

  checksum = checksum % 256; // keep it in 0-255 range
  return checksum;
}

// -------------------- Error Code --------------------
int ErrorCode(DHT_Data dhtData, ULTRA_Data &ultradata, Commands dades){
  int error_code = 0;

  if(dhtData.temp < dades.minTemp || dhtData.temp > dades.maxTemp) error_code += 1;
  if(dhtData.hum < dades.minHum || dhtData.hum > dades.maxHum) error_code += 2;
  if(dades.mitj_mode == 0) error_code += 8;

  // Remove invalid distances
  for(int j = 0; j < ultradata.count; j++){
    if(ultradata.distance[j] <= 0){
      if(error_code % 4 < 4) error_code += 4; // mark error first time

      // Shift left
      for(int a = j; a < ultradata.count - 1; a++){
        ultradata.distance[a] = ultradata.distance[a + 1];
        ultradata.angle[a] = ultradata.angle[a + 1];
      }
      ultradata.count--; // decrease valid count
      j--; // recheck current index
    }
  }

  return error_code;
}
