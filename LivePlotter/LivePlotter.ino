/*

Data logger with serial output for fast/live plotting on python

Analog input on pin A0 is read-in at a sampling rate of ~xyz kS/s
The sampling rate can be adjusted for more channels, or slower sampling rate, 
[channels must be enabled/disabled by setting the registers in the setup() method below],
by adjusting the sampling_time variable

The ADC data is buffered then sent quickly via SerialUSB. Since there is some overhead 
involved with Serial transfer, the data should be transferred in large quantities ( > 1 kB) so
as to minimise total transmission time. Buffering will be memory-limited at some point. The
largest buffer possible is currently untested!

PySerial is used to grab the data from the serial port and read it into python. For this,
the python module SixChannelReader.py has been written (in the same directory as this file), 
which provides class-based methods of reading in the data, as well as a method of 
synchronisation for triggering purposes.

************
** NOTE: the USB connection to the Arduino must be to the NATIVE port, not the programming port!
************



Author: James Keaveney
19/05/2015

*/

// set up variables
const int buffer_length = 2000; // length of data chunks sent at a time via SerialUSB

//const long acquisition_time = 90000; // in ms (~2 minutes in real experiment)
//const long settling_time_ms = 15000; // in ms

const int sampling_time_sleep = 0; // in micros

//const int TempAdjustPin = 2;

String strTime = "";
String strOut = "";
String strC1 = "";

unsigned long current_time;

void setup() {
  
  // set ADC resolution
  analogReadResolution(12);
  
  // manually set registers for faster analog reading than the normal arduino methods
  ADC->ADC_MR |= 0xC0; // set free running mode (page 1333 of the Sam3X datasheet)
  ADC->ADC_CHER = 0x80;  // enable channels  (see page 1338 of datasheet) on adc 7 (pin A0)
                       // see also http://www.arduino.cc/en/Hacking/PinMappingSAM3X for the pin mapping between Arduino names and SAM3X pin names
  ADC->ADC_CHDR = 0xFF7F; // disable all other channels
  ADC->ADC_CR=2;       // begin ADC conversion
  
  
  // initialise serial port
  SerialUSB.begin(115200); // baud rate is ignored for USB - always at 12 Mb/s
  while (!SerialUSB); // wait for USB serial port to be connected - wait for pc program to open the serial port
  
}



void loop() {

  // data acquisition will start with a synchronisation step:
  // python should send a single byte of data, the arduino will send one back to sync timeouts
  int incoming = 0;
  if (SerialUSB.available() > 0) // polls whether anything is ready on the read buffer - nothing happens until there's something there
  {
    incoming = SerialUSB.read();
    // after data received, send the same back
    SerialUSB.println(incoming);
    
    // measure start time - then acquire data for an amount of time set by the acquisition_time variable
    unsigned long start_micros = micros();
    unsigned long start_time = millis();
            
    // generate and concatenate strings
    for (int jj = 0; jj < buffer_length; jj++)
    {
      
      // ADC acquisition
      
      // can put this in a small loop for some averaging if required - takes ~ 60 microsec per read/concatenate cycle
      while((ADC->ADC_ISR & 0x80)!=0x80); // wait for conversion to complete - see page 1345 of datasheet     
      
      // concatenate strings
      current_time = micros()-start_micros;
      strTime.concat(current_time); // time axis
      strTime.concat(',');     
      strC1.concat(ADC->ADC_CDR[7]); // read data from the channel data register
      strC1.concat(',');
      
      //Serial.print(current_time);
      //Serial.print(",");
      
      delayMicroseconds(sampling_time_sleep); // limit sampling rate to something reasonable - a few kS/s
    }
      
    // send data via SerialUSB
    // perform a flush first to wait for the previous buffer to be sent, before overwriting it
    SerialUSB.flush();
    strOut = strTime + strC1; 
    SerialUSB.print(strOut); // doesn't wait for write to complete before moving on
    
    
    // clear string data - re-initialise
    strTime = "";
    strC1 = "";
    
  
    // finally, print end-of-data and end-of-line character to signify no more data will be coming
    SerialUSB.println("\0");
    
  }
}
