#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX,TX

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
}


void loop() {
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    mySerial.println(msg);
  }
  if (mySerial.available()) {
    String msg = Serial.readStringUntil('\n');
    Serial.println(msg);
  }
}