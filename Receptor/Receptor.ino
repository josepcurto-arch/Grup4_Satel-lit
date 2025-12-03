#include <SoftwareSerial.h>
SoftwareSerial portSat(10, 11); // RX, TX (blau, taronja)

const int pinBuzzer = 7;   //  Pin del buzzer
const int pinBoto = 8;     //  Pin del botó per silenciar (a GND)

bool alarmaSilenciada = false;
bool alarmaActiva = false;

unsigned long instantUltimaRecepcio = 0;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(pinBuzzer, OUTPUT);
  pinMode(pinBoto, INPUT_PULLUP);  // Botó connectat a GND
  
  Serial.begin(9600);
  portSat.begin(9600);
  digitalWrite(LED_BUILTIN, LOW);
  digitalWrite(pinBuzzer, LOW);
}

void loop() {
  // --- RECEPCIÓ DE DADES DEL SATÈL·LIT ---
  if (portSat.available()) {
    String dades = portSat.readString();
    Serial.print(dades);
    
    // Busquem la primera i segona coma per obtenir el segon valor
    int primeraComa = dades.indexOf(',');
    int segonaComa = dades.indexOf(',', primeraComa + 1);
    
    if (primeraComa != -1 && segonaComa != -1) {
      String segonValorStr = dades.substring(primeraComa + 1, segonaComa);
      int segonValor = segonValorStr.toInt();
      
      // --- CONDICIÓ D’ALARMA SEGONS EL SEGON ELEMENT (CODI ERROR)---
      if (segonValor != 8 && segonValor != 0) {
        alarmaActiva = true;
      } else {
        alarmaActiva = false;
        alarmaSilenciada = false; // Es reinicia quan torna a valors correctes
      }
    }
    instantUltimaRecepcio = millis(); // Actualitza el temps de recepció
  }

  // --- CONDICIÓ D’ALARMA PER TEMPS ---
  unsigned long tempsSenseRecepcio = millis() - instantUltimaRecepcio;
  if (tempsSenseRecepcio >= 5000) {  // Si han passat 5 segons sense dades
    alarmaActiva = true;
  }

  // --- BOTÓ DE SILENCI ---
  if (digitalRead(pinBoto) == LOW) {
    delay(200);  // petita pausa per anti-rebot
    alarmaSilenciada = true;
  }

  // --- LED I BUZZER INDICANT EL MATEIX ESTAT ---
  if (alarmaActiva && !alarmaSilenciada) {
    digitalWrite(LED_BUILTIN, HIGH);
    tone(pinBuzzer, 1000);  // So a 1 kHz
  } else {
    digitalWrite(LED_BUILTIN, LOW);
    noTone(pinBuzzer);
  }

  // --- REENVIA ORDRES AL SATÈL·LIT ---
  if (Serial.available()) {
    String dadesPC = Serial.readString();
    portSat.print(dadesPC);
    Serial.println(dadesPC);
  }
}
