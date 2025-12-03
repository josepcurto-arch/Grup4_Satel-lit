#include <SoftwareSerial.h>
int i;
SoftwareSerial mySerial(10, 11); // RX, TX 
void setup() {
   Serial.begin(9600);
   mySerial.begin(9600);
   mySerial.println("Empezamos");
   i=1;
}
void loop() {
   delay (1000);
   Serial.println(i);
   mySerial.print("Envío: ");
   mySerial.println(i);
   i=i+1;
}