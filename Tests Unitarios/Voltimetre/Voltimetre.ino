// define analog input
#define ANALOG_IN_PIN  A0
#define REF_VOLTAGE    5.0
#define ADC_RESOLUTION 1024.0
#define R1 30000.0 // resistor values in voltage sensor (in ohms)
#define R2 7500.0  // resistor values in voltage sensor (in ohms)
int percentatge;

void setup() {
  Serial.begin(9600);
}

void loop() {
  // read the analog input
  int adc_value = analogRead(ANALOG_IN_PIN);

  // determine voltage at adc input
  float voltage_adc = ((float)adc_value * REF_VOLTAGE) / ADC_RESOLUTION;

  // calculate voltage at the sensor input
  float voltage_in = voltage_adc * (R1 + R2) / R2;

  //convert voltage to percentage of battery
  if(voltage_in<0){
    voltage_in=-voltage_in;
  }

  if(voltage_in==0){
    percentatge=0;
  }

  else if(voltage_in>=8.8){
    percentatge = 75+((voltage_in-8.8)/0.7)*25;
  }
  
  else if(8.8>voltage_in&&voltage_in>=7.2){
    percentatge = 25+((voltage_in-7.2)/1.6)*50;
  }

  else if(7.2>voltage_in&&voltage_in>=6){
    percentatge=((voltage_in-6)/1.2)*25;
  }

  if(percentatge>100){
    percentatge=100;
  }

  Serial.print(percentatge);
  Serial.println("%");

  delay(500);
}
