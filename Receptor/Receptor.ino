#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)
float temperatura;
float humitat;
int check = 0;
unsigned long rxage = 0;
void setup() {
   pinMode(LED_BUILTIN, OUTPUT);
   Serial.begin(9600);
   mySerial.begin(9600);
   digitalWrite(LED_BUILTIN, LOW);
}
void loop() {
   // Si rep dades del satèl·lit, les envia al portàtil i analitza que siguen vàlides
   if (mySerial.available()) {
      String data = mySerial.readString();
      Serial.print(data);
   
   int comaIndex = data.indexOf(',');
   temperatura = data.substring(0, comaIndex).toFloat();
   humitat = data.substring(comaIndex + 1).toFloat();

   if (temperatura < 0 || temperatura > 40 || humitat < 20 || humitat > 90)  {
    digitalWrite(LED_BUILTIN, HIGH);  // fora del marge
    check = 1;
   } else {
    digitalWrite(LED_BUILTIN, LOW);   // dins del marge
    check = 0;
   }
   rxage = millis();
   }
   // Si no ha rebut dades en més de 4 segons (la transmisió es cada 3) també emet alarma
   unsigned long timerx = millis() - rxage;
   if(timerx > 4000 || check == 1) {
      digitalWrite(LED_BUILTIN, HIGH);
   } else {
      digitalWrite(LED_BUILTIN, LOW);
   }
   // Si rep ordre del portàtil, les envia al satèl·lit
   if (Serial.available()) {
      String data2 = Serial.readString();
      mySerial.print(data2);
      Serial.println(data2);
   }
}
