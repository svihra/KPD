/*
  Analog input, analog output, serial output

  Reads an analog input pin, maps the result to a range from 0 to 255 and uses
  the result to set the pulse width modulation (PWM) of an output pin.
  Also prints the results to the Serial Monitor.

  The circuit:
  - potentiometer connected to analog pin 0.
    Center pin of the potentiometer goes to the analog pin.
    side pins of the potentiometer go to +5V and ground
  - LED connected from digital pin 9 to ground

  created 29 Dec. 2008
  modified 9 Apr 2012
  by Tom Igoe

  This example code is in the public domain.

  http://www.arduino.cc/en/Tutorial/AnalogInOutSerial
*/

// These constants won't change. They're used to give names to the pins used:
const int analogInPin = A0;  // Analog input pin that the potentiometer is attached to
const int analogOutPin = 9; // Analog output pin that the LED is attached to

int sensorValue = 0;        // value read from the pot
int outputValue = 0;        // value output to the PWM (analog out)

const uint16_t maxCount = 65535;
const uint16_t maxBins = 1024;

uint16_t histo[maxBins];
uint16_t histoTmp[maxBins];

void setup() {
  // initialize serial communications at 9600 bps:
  pinMode(0,OUTPUT);
  Serial.begin(9600);
}

void clearHisto()
{
  uint16_t i;
  for(i = 0; i < maxBins; i++)
  {
    histo[i] = 0;
    histoTmp[i] = 0;
  }  
}

void loop() {
  // read the analog in value:
  // map it to the range of the analog out:
  //outputValue = map(sensorValue, 0, 1023, 0, 255);
  // change the analog out value:
  //analogWrite(analogOutPin, outputValue);
  
  clearHisto();
  uint16_t i;
  uint16_t tmp = 0;
  uint16_t val = 0;
  for(i = 0; i < maxCount; i++)
  {
    tmp = analogRead(analogInPin);
    digitalWrite(0,HIGH);
    digitalWrite(0,LOW);
    
    histoTmp[tmp]++;
    if (tmp > val)
    {
      val = tmp;
    }
    else
    {
      histo[val]++;   
      val = 0;   
    }
    delayMicroseconds(100);
  }

  uint16_t j;
  for(j = 0; j < maxBins; j++)
  {
    Serial.print(histo[j]);
    Serial.print(",");
  }
  Serial.println();
  for(j = 0; j < maxBins; j++)
  {
    Serial.print(histoTmp[j]);
    Serial.print(",");
  }
  Serial.println();
  Serial.println();
}
