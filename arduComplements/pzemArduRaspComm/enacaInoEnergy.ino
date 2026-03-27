//                    GNU GENERAL PUBLIC LICENSE
//                       Version 3, 29 June 2007
//
// Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
// Everyone is permitted to copy and distribute verbatim copies
//of this license document, but changing it is not allowed.

//Enacaino-energy V1.0
//Last modification 01-feb-2026
//This code applies for energy monitoring device PZEM-004 V3 with Arduino Mega 2560.
//Created by: William Jiménez

#include <PZEM004Tv30.h>
#include <SoftwareSerial.h>

SoftwareSerial pzemSWSerial(10, 11);  //Pins to connect to A/C energy monitors


byte disabled = 150;  //My own statement for True value in serial transmission
byte enabled = 180;   //My own statement for False value in serial transmission


bool flagForPzemReset = false;  //Temp flag to ensure reset condition
float windSpeed = 0.00;         //Variable assignment for windspeed sensor
char raspCommand;               //char command that will be received from raspberry
byte busyIndex = 0;             //To ensure arduino mega is not busy before sending float array from PZEM
#define floatsToSend 8
//============Arrays definition to be reported to raspberry through serial connection

float frameSensors1[floatsToSend];   //Data frame that belongs to energy monitoring from the apt2
float frameTransfer[floatsToSend];   //Data frame to be copied from pzem lecture
float fFrameToSerial[floatsToSend];  //Interchange frame before transfer array of floats to serial port
float pzemGroup[10][8];              //Max allowable 2D array size for ardo mega in this case [165][8]
float sensorsGroup[5][8];            //A testing way to group sensors modules into array of arrays
byte statusArray[32];                //Under this test for general purpose
byte statusArray2[32];               //Status related to pzem working on zeroing and others
byte statusArrayFdb[32];             //Status Array Feedback from Raspnerry
byte statusArray100[3][32];          //Will be used for redesign purpose status indicador for max 2D pzemGroup max [55][32]
//--------------------------
//===========Timing variables defined to scan energy modules according to priority assigned
unsigned long previousMillis1 = 50;  // will store last time for priority 1 group
const long interval1 = 2100;         // interval at which to scan pzem group #1 (milliseconds)
unsigned long previousMillis2 = 50;  // will store last time for priority 2 group
const long interval2 = 2100;         // interval at which to scan pzem group #2 (milliseconds)
unsigned long previousMillis3 = 50;  // will store last time for serial monitoring priority
const long interval3 = 2100;         // interval at which serial monitoring updates values for IDE
unsigned long previousMillis4 = 50;  // will store last time for serial monitoring priority
const long interval4 = 2100;         // interval at which serial monitoring updates values for IDE


//--------------------------
//===========Energy monitoring's address device is defined with another separate code for using with one at a time
PZEM004Tv30 pzemBdcst2(&Serial2, 0x00);      //This port for 0x42, 0x43, 0x44 and 0x45 modules
PZEM004Tv30 pzemBdcst3(&Serial3, 0x00);      //This port for 0x46, 0x47, 0x48 and 0x49 modules
PZEM004Tv30 pzemBdcst4(pzemSWSerial, 0x00);  //This port for 0x50 and 0x51 modules that monitor A/C

//pzemFrameGroup must be sized to 8 elements maximum
byte pzemFrameGroup[] = { 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x50, 0x51 };  //List of pzem addresses in communication bus
unsigned int prevMilForZeroingPzem[] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
unsigned int intervalForZeroingPzem[] = { 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000 };
byte workingResetPzem[] = { disabled, disabled, disabled, disabled, disabled, disabled, disabled, disabled, disabled, disabled };
byte doneResetPzem[] = { enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled };



unsigned int numParam01[] = { 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000 };  //List of numerical parameters for internal flag control
//Configuration function
void setup() {
  pinMode(9, OUTPUT);    //Contactor A/C V2 NO
  pinMode(8, OUTPUT);    //Contactor A/C V1 NO
  pinMode(7, OUTPUT);    //Permisivo Energia V2 NO
  pinMode(6, OUTPUT);    //Permisivo Energia V1 NO
  pinMode(5, OUTPUT);    //Luz 1 Corredor V2 NO
  pinMode(4, OUTPUT);    //Luz 2 Corredor V2 NO
  pinMode(5, OUTPUT);    //Luz 1 Corredor V1 NO
  pinMode(4, OUTPUT);    //Luz 2 Corredor V1 NO
  Serial.begin(115200);  //This is the speed for serial monitoring
  Serial1.begin(9600);   //Speed for serial comm with raspberry pi through USB Serial FTDI adapter
  delay(50);
  statusArray[30] = enabled;  //Status flag to always check serial available

  for (int blockFrame1 = 0; blockFrame1 < 32; blockFrame1++) {
    statusArray2[blockFrame1] = disabled;  //Status flag to always check serial available
  }
  statusArray2[30] = enabled;
  //pzemBdcst2.resetEnergy();
  //pzemBdcst3.resetEnergy(); Global reset for Serial2
  //pzemBdcst4.resetEnergy(); Global reset for softwareSerial instance
}

//Loop function
void loop() {
  unsigned long currentMillis = millis();
  windSpeed = (analogRead(A0));         //Read wind speed (0-5V) connected to analog input A0
  windSpeed = (windSpeed * 30) / 1023;  //According to manual max speed range is around 30m/s WARNING
  sensorsGroup[0][0] = windSpeed;       //wind speed sensor location in float Sensor Array
  frameSensors1[1] = windSpeed;         //wind speed sensor location in float Sensor Array
  frameSensors1[2] = windSpeed + .5;    //Definition pending
  frameSensors1[3] = windSpeed + .7;    //Definition pending
  frameSensors1[4] = windSpeed + .8;    //Definition pending
  frameSensors1[5] = windSpeed + 1.1;   //Definition pending
  frameSensors1[6] = windSpeed + 1.3;   //Definition pending

  Serial2.begin(9600);
  //First block of PZEM modules (Main feed and V1)
  if (currentMillis - previousMillis2 >= interval2) {
    previousMillis2 = currentMillis;  // save the last time you scan this group
    for (int blockFrame1 = 0; blockFrame1 < 4; blockFrame1++) {
      if (workingResetPzem[blockFrame1] == disabled) {
        //This conditional row has been added in order to prevent readings while zeroing is in progress
        PZEM004Tv30 pzemM(&Serial2, pzemFrameGroup[blockFrame1]);                     //Define object at specific address according to pzemFrameGroup position
        pzemGetter(frameTransfer, pzemM, statusArray, busyIndex = blockFrame1 + 16);  //busyFlag position according to definition Table
        statusArray[blockFrame1] = voltageDetect(frameTransfer[1]);                   //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
        for (int elementIndex = 0; elementIndex < 8; elementIndex++) {
          pzemGroup[blockFrame1][elementIndex] = frameTransfer[elementIndex];  //Trannsfer from 1D array to specifc block in 2D array
        }
      }
    }
  }
  Serial2.end();

  Serial3.begin(9600);
  //Second block of PZEM modules (V2 and me)
  if (currentMillis - previousMillis1 >= interval1) {
    previousMillis1 = currentMillis;  // save the last time you scan this group
    for (int blockFrame1 = 4; blockFrame1 < 8; blockFrame1++) {
      if (workingResetPzem[blockFrame1] == disabled) {
        //This conditional row has been added in order to prevent readings while zeroing is in progress
        PZEM004Tv30 pzemM(&Serial3, pzemFrameGroup[blockFrame1]);                     //Define object at specific address according to pzemFrameGroup position
        pzemGetter(frameTransfer, pzemM, statusArray, busyIndex = blockFrame1 + 16);  //Call to upgrade values inside especific pzem module
        statusArray[blockFrame1] = voltageDetect(frameTransfer[1]);                   //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
        for (int elementIndex = 0; elementIndex < 8; elementIndex++) {
          pzemGroup[blockFrame1][elementIndex] = frameTransfer[elementIndex];  //Trannsfer from 1D array to specifc block in 2D array
        }
      }
    }
  }
  Serial3.end();

  pzemSWSerial.begin(9600);
  //Third block of PZEM modules for A/C Machines. Only two modules are actually (2025-07-11) installed in this group
  if (currentMillis - previousMillis3 >= interval3) {
    previousMillis3 = currentMillis;                              // save the last time you scan this group
    for (int blockFrame1 = 8; blockFrame1 < 10; blockFrame1++) {  //PZEM Modules por A/C located at pzemFrameGroup[8][8] and [9][8]
      if (workingResetPzem[blockFrame1] == disabled) {
        PZEM004Tv30 pzemM(pzemSWSerial, pzemFrameGroup[blockFrame1]);  //Define object at specific address according to pzemFrameGroup position
        pzemGetter(frameTransfer, pzemM, statusArray, busyIndex = blockFrame1 + 16);
        statusArray[blockFrame1] = voltageDetect(frameTransfer[1]);  //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
        for (int elementIndex = 0; elementIndex < 8; elementIndex++) {
          pzemGroup[blockFrame1][elementIndex] = frameTransfer[elementIndex];  //Trannsfer from 1D array to specifc block in 2D array
        }
      }
    }
  }
  pzemSWSerial.end();

  //Print results in serial monitor for debugging purposes
  if (currentMillis - previousMillis4 >= interval4) {
    previousMillis4 = currentMillis;  // save the last time printed values in serial monitor
    for (int i = 0; i < 10; i++) {
      for (int j = 0; j < 8; j++) {
        //Serial.print(pzemGroup[i][j]);
        //Serial.print(" ");
      }
      //Serial.println();
    }
    //BEGINING OF DEBUG
    //  Serial.println("/");
    for (int rr = 0; rr < 32; rr++) {
      //    Serial.print(statusArray[rr]);
      //    Serial.print(" ");
    }
    //  Serial.println();
    for (int rr = 0; rr < 32; rr++) {
      //    Serial.print(statusArray2[rr]);
      //    Serial.print(" ");
    }
    //  Serial.println();
    for (int rr = 0; rr < 32; rr++) {
      //     Serial.print(statusArrayFdb[rr]);
      //    Serial.print(" ");
    }
    //  Serial.println();
    //  Serial.println("======================================");
  }


  //Here the idea is to reflect command for global zeroing pzems
  byte countToGlobalResetPzem = 0;
  for (byte pzemZeroScan = 0; pzemZeroScan < 8; pzemZeroScan++) {
    if (statusArrayFdb[pzemZeroScan] == enabled) {
      countToGlobalResetPzem++;
    }
  }
  if (countToGlobalResetPzem == 8) {
    statusArray[28] = enabled;  //Reflect command to zeroing pzems received
  } else {
    statusArray[28] = disabled;  //REMEMBER TO SET AS DISABLED
  }

  //This block to individually evaluate A/C V1 Contactor
  if (statusArrayFdb[10] == enabled) {
    digitalWrite(8, HIGH);
  } else {
    digitalWrite(8, LOW);
  }
  //This block to individually evaluate A/C V2 Contactor
  if (statusArrayFdb[11] == enabled) {
    digitalWrite(9, HIGH);
  } else {
    digitalWrite(9, LOW);
  }
  //&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
  //This block is to evaluate which pzem module needs to be zeroing
  //Serial.println("Just before");
  for (byte pzemZeroScan = 0; pzemZeroScan < 10; pzemZeroScan++) {
    if (statusArrayFdb[pzemZeroScan] == enabled && workingResetPzem[pzemZeroScan] == disabled && doneResetPzem[pzemZeroScan] == enabled) {
      Serial.println("I'M HERE");
      workingResetPzem[pzemZeroScan] = enabled;
      statusArrayFdb[pzemZeroScan] = disabled;  //Ensure order clear from array in order to avoid repetition
      statusArray2[pzemZeroScan] = enabled;     //Its a copy of workingResetPzem
      prevMilForZeroingPzem[pzemZeroScan] = currentMillis;
      doneResetPzem[pzemZeroScan] = disabled;  // flag markdown
      if (pzemZeroScan >= 0 && pzemZeroScan < 4) {
        PZEM004Tv30 pzemM9(&Serial2, pzemFrameGroup[pzemZeroScan]);
        pzemM9.resetEnergy();
        pzemGroup[pzemZeroScan][4] = 0.0;  //Mark as zero the energy meter registry pzem afected in case raspberry asks
      } else if (pzemZeroScan >= 4 && pzemZeroScan < 8) {
        PZEM004Tv30 pzemM9(&Serial3, pzemFrameGroup[pzemZeroScan]);
        pzemM9.resetEnergy();
        pzemGroup[pzemZeroScan][4] = 0.0;  //Mark as zero the energy meter registry pzem afected in case raspberry asks
      } else {
        PZEM004Tv30 pzemM9(pzemSWSerial, pzemFrameGroup[pzemZeroScan]);
        pzemGroup[pzemZeroScan][4] = 0.0;  //Mark as zero the energy meter registry pzem afected in case raspberry asks
        pzemM9.resetEnergy();
      }
    }
  }

  //This block is to evaluate elapsed time for finishing flag marking PZEM Reset
  for (byte pzemZeroScan = 0; pzemZeroScan < 10; pzemZeroScan++) {
    if (workingResetPzem[pzemZeroScan] == enabled) {
      if (currentMillis - prevMilForZeroingPzem[pzemZeroScan] >= intervalForZeroingPzem[pzemZeroScan]) {
        doneResetPzem[pzemZeroScan] = enabled;  // save the last time you scan this group
        workingResetPzem[pzemZeroScan] = disabled;
        statusArray2[pzemZeroScan] = disabled;  //Its a copy of workingResetPzem
      }
    }
  }
}  //End loop function

//Detect and process command request from raspberry
void serialEvent1() {
  raspCommand = (char)Serial1.read();  //A command char received from raspberry
  bool flagToFloatTransmit = false;    //This one in order to request specific float array transmission if needed
  int pzemPositioner = 0;
  if ((raspCommand >= 'a' && raspCommand <= 'k')) {
    flagToFloatTransmit = true;  //For future reference a string must be defined to expand options of can be decided
  }
  if (raspCommand == 'a') {
    pzemPositioner = 0;
  } else if (raspCommand == 'b') {
    pzemPositioner = 1;
  } else if (raspCommand == 'c') {
    pzemPositioner = 2;
  } else if (raspCommand == 'd') {
    pzemPositioner = 3;
  } else if (raspCommand == 'e') {
    pzemPositioner = 4;
  } else if (raspCommand == 'f') {
    pzemPositioner = 5;
  } else if (raspCommand == 'g') {
    pzemPositioner = 6;
  } else if (raspCommand == 'h') {
    pzemPositioner = 7;
  }
  //---------datos de los PZEM A/C en este bloque
  else if (raspCommand == 'i') {
    pzemPositioner = 8;
  } else if (raspCommand == 'j') {
    pzemPositioner = 9;
  }
  //-----------Fin Bloque
  else if (raspCommand == 'k') {
    frameSensors1[0] = 11.07;
    frameSensors1[7] = checkSumCalculatorF(frameSensors1);
    Serial1.write((byte*)&frameSensors1, floatsToSend * sizeof(float));
    return;
  }
  //Byte command received to answer for serialPortStatus
  else if (raspCommand == 'l') {
    Serial1.write(180);
    return;
  } else if (raspCommand == 'u') {
    //Raspberry asking to send array of bytes as flag commands
    byte byteFrame[32];
    byte indexFr;
    for (indexFr = 0; indexFr < 32; indexFr++) {
      delay(2);
      if (Serial1.available() > 0) {
        byteFrame[indexFr] = byte(Serial1.read());
      }
    }
    //Let's check first if package received from raspberry is ok
    byte packChksmInspect = checkSumCalculatorB(byteFrame);
    if (packChksmInspect == byteFrame[31]) {
      for (indexFr = 0; indexFr < 32; indexFr++) {
        statusArrayFdb[indexFr] = byteFrame[indexFr];
      }
    }
    return;
  } else if (raspCommand == 'y') {
    //Raspberry asking for array of bytes to be received as an answer
    statusArray2[29]++;
    statusArray2[31] = checkSumCalculatorB(statusArray2);
    Serial1.write((byte*)&statusArray2, sizeof(statusArray2));
    return;
  } else if (raspCommand == 'z') {
    //Raspberry asking for array of bytes to be received as an answer
    statusArray[29]++;
    statusArray[31] = checkSumCalculatorB(statusArray);
    Serial1.write((byte*)&statusArray, sizeof(statusArray));
    return;
  }
  if (flagToFloatTransmit) {
    for (int indexToSerial = 0; indexToSerial < 10; indexToSerial++) {
      fFrameToSerial[indexToSerial] = pzemGroup[pzemPositioner][indexToSerial];
    }
    fFrameToSerial[0] = 11.07;
    fFrameToSerial[7] = checkSumCalculatorF(fFrameToSerial);
    Serial1.write((byte*)&fFrameToSerial, floatsToSend * sizeof(float));
    return;
  }
}
