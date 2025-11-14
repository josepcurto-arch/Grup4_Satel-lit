#include <Servo.h>
#include <HCSR04.h>
#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX 

byte trig = 9;
byte echo = 8;
Servo servo;
int angle=0;

long readUltrasonic() {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  long duration = pulseIn(echo, HIGH, 20000); // 20 ms màxim
  long distance = duration * 0.034 / 2;       // cm
  return distance;
}

void setup() {
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
  Serial.begin(9600);
  mySerial.begin(9600);
  servo.attach(3);

}

void loop() {
  for(angle=0; angle<=180; angle+=5){
    servo.write(angle);

    long distance = readUltrasonic();
    mySerial.print(angle);
    mySerial.print(",");
    mySerial.println(distance);
  }

  for(angle=180; angle>=0; angle-=5){
    servo.write(angle);
    
    long distance = readUltrasonic();
    mySerial.print(angle);
    mySerial.print(",");
    mySerial.println(distance);
  }

}
