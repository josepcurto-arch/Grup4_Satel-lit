#include <DHT11.h>

DHT11 dht11(2); // Pin de datos (S) al D2
int result = 0;
int t; int h;
void setup() {
  Serial.begin(9600);
  result = dht11.readTemperatureHumidity(t, h);

  if(result != 0) {
    Serial.println(DHT11::getErrorString(result));
  }

}

void loop() {
  Serial.print(dht11.readTemperature());
  Serial.print(" // ");
  Serial.println(dht11.readHumidity());

  delay(1000);

}
