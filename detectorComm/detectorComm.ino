// These constants won't change. They're used to give names to the pins used:
const int analogInPin = A0;  // Analog input pin that the potentiometer is attached to

// max counter for run
const uint16_t maxCount = 65535;
// max number of bins
const uint16_t maxBins = 1024;

uint16_t histo[maxBins];
uint16_t histoTmp[maxBins];

void setup() {
  // initialize serial communications at 9600 bps:
  pinMode(0,OUTPUT);
  Serial.begin(9600);
}

// function for clearing data
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
  // clear both raw and filtered data arrays
  clearHisto();

  // init counter and read values
  uint16_t i;
  uint16_t tmp = 0;
  uint16_t val = 0;

  // main run for acquisition
  for(i = 0; i < maxCount; i++)
  {
    // reading data
    tmp = analogRead(analogInPin);
    
    // reset
    digitalWrite(0,HIGH);
    digitalWrite(0,LOW);

    // filter
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

  // printing filtered values
  uint16_t j;
  for(j = 0; j < maxBins; j++)
  {
    Serial.print(histo[j]);
    Serial.print(",");
  }
  Serial.println();
  // printing raw values
  for(j = 0; j < maxBins; j++)
  {
    Serial.print(histoTmp[j]);
    Serial.print(",");
  }
  Serial.println();
  // print of empty line for connecting
  Serial.println();
}
