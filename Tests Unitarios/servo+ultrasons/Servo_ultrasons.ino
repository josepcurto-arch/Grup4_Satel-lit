#include <Servo.h>

const int trig = 9;
const int echo = 10;
float durada, distancia;
Servo servo;

void setup() {
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
  Serial.begin(9600);
  servo.attach(3);

}

void loop() {
  for(int angle=0; angle<=180; angle++){
    servo.write(angle);
    delay(30);
    digitalWrite(trig, LOW);
    delay(2);
    digitalWrite(trig, HIGH);
    delay(10);
    digitalWrite(trig, LOW);
    durada = pulseIn(echo, HIGH);
    distancia = durada*0.034/2;
  
    Serial.print(angle);
    Serial.print(",");
    Serial.println(distancia);
  }

  for(int angle=180; angle>=0; angle--){
    servo.write(angle);
    delay(30);
    digitalWrite(trig, LOW);
    delay(2);
    digitalWrite(trig, HIGH);
    delay(10);
    digitalWrite(trig, LOW);
    durada = pulseIn(echo, HIGH);
    distancia = durada*0.034/2;
  
    Serial.print(angle);
    Serial.print(",");
    Serial.println(distancia);
  }

  delay(3000);

}
