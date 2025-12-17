#include <SoftwareSerial.h>
#include <math.h>

/* ================== PINS ================== */
#define RX_PIN 10
#define TX_PIN 11
#define BUZZER_PIN 7
#define BUTTON_PIN 8

/* ================== SERIAL ================== */
SoftwareSerial satSerial(RX_PIN, TX_PIN);

/* ================== CONSTANTS ================== */
const float R_EARTH = 6371.0; // km

/* ================== VARIABLES ================== */
unsigned long lastRxTime = 0;
unsigned long tempstx = 6000;   // ms

bool txEnabled = true;
bool buzzerMuted = false;
bool buzzerOn = false;

/* ================== BUZZER ================== */
void startBuzzer() {
  if (!buzzerOn) {
    tone(BUZZER_PIN, 2000);
    buzzerOn = true;
  }
}

void stopBuzzer() {
  if (buzzerOn) {
    noTone(BUZZER_PIN);
    buzzerOn = false;
  }
}

/* ================== CONFIG ================== */
void processConfig(String cfg) {
  int values[7];
  int idx = 0;

  while (cfg.length() && idx < 7) {
    int comma = cfg.indexOf(',');
    if (comma == -1) {
      values[idx++] = cfg.toInt();
      break;
    } else {
      values[idx++] = cfg.substring(0, comma).toInt();
      cfg = cfg.substring(comma + 1);
    }
  }

  if (idx == 7) {
    tempstx = (unsigned long)values[6] * 1000UL;
  }
}

/* ================== PARSE ECEF ================== */
void parseAndDisplayECEF(String line) {
  int field = 0;
  float x = 0, y = 0, z = 0;

  while (line.length()) {
    int comma = line.indexOf(',');
    String token;

    if (comma == -1) {
      token = line;
      line = "";
    } else {
      token = line.substring(0, comma);
      line = line.substring(comma + 1);
    }

    field++;
    if (field == 4) x = token.toFloat();
    if (field == 5) y = token.toFloat();
    if (field == 6) z = token.toFloat();
  }
}

/* ================== SETUP ================== */
void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.begin(9600);
  satSerial.begin(9600);
  satSerial.setTimeout(2000);

  noTone(BUZZER_PIN);
  lastRxTime = millis();
}

/* ================== LOOP ================== */
void loop() {

  /* --- Dades LoRa --- */
  if (satSerial.available()) {
      String line = satSerial.readStringUntil('\n');
      line.trim();

      if (!(line.startsWith("9600") || line.indexOf("YL_800T") != -1)) {
          if (line.length() > 0 && line.indexOf(',') != -1) { // <-- només línies amb coma
              lastRxTime = millis();
              Serial.println(line);

              buzzerMuted = false;
              stopBuzzer();

              parseAndDisplayECEF(line);  // processa només dades amb coma
          }
      }
  }

  /* --- Comandes PC --- */
  if (Serial.available()) {
      String cmd = Serial.readStringUntil('\n');
      cmd.trim();

      // Reenviem sempre al LoRa
      satSerial.println(cmd);

      if (cmd == "TX0") {
          txEnabled = false;
          stopBuzzer();
      } else if (cmd == "TX1") {
          txEnabled = true;
      } 
      if(cmd.indexOf(',') != -1) {
          processConfig(cmd); // processa qualsevol altra cosa del port sèrie
      }
  }


  /* --- Botó silenci --- */
  if (digitalRead(BUTTON_PIN) == LOW) {
    buzzerMuted = true;
    stopBuzzer();
    delay(300);
  }

  /* --- Timeout --- */
  if (txEnabled) {
    if (millis() - lastRxTime > tempstx && !buzzerMuted) {
      startBuzzer();
    }
  } else {
    stopBuzzer();
  }
}