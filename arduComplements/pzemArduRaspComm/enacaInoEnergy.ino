//                    GNU GENERAL PUBLIC LICENSE
//                       Version 3, 29 June 2007
//
// Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
// Everyone is permitted to copy and distribute verbatim copies
//of this license document, but changing it is not allowed.

//Enacaino-energy V1.0
//Last modification 25-feb-2021
//This code applies for energy monitoring device PZEM-004 V3 with Arduino Mega 2560.
//Created by: William Jiménez

#include <PZEM004Tv30.h>

byte disabled = 150;
byte enabled = 180;

float windSpeed = 0.00;
char raspCommand;
byte busyIndex = 0; //To ensure arduino mega is not busy before sending float array from PZEM
#define floatsToSend 8
//============Arrays definition to be reported to raspberry through serial connection

float frameSensors1[floatsToSend]; //Data frame that belongs to energy monitoring from the apt2
float frameTransfer[floatsToSend]; //Data frame to be copied from pzem lecture
float fFrameToSerial[floatsToSend]; //Interchange frame before transfer array of floats to serial port
float pzemGroup[8][8];  //A testing way to group pzem modules into array of arrays
float sensorsGroup[12][8];  //A testing way to group sensors modules into array of arrays
byte statusArray[32];
//--------------------------
//===========Timing variables defined to scan energy modules according to priority assigned
unsigned long previousMillis1 = 0;        // will store last time LED was updated
const long interval1 = 1500;           // interval at which to blink (milliseconds)
unsigned long previousMillis2 = 0;        // will store last time LED was updated
const long interval2 = 7500;           // interval at which to blink (milliseconds)
//--------------------------
//===========Energy monitoring's address device is defined with another separate code for using with one at a time
//PZEM004Tv30 pzemHouseF1(&Serial3, 0x42); //PZEM module for house phase 1
//PZEM004Tv30 pzemHouseF2(&Serial3, 0x43); //PZEM module for house phase 2
//PZEM004Tv30 pzemApt1F1(&Serial3, 0x44); //PZEM module for aparment 1 phase 1


PZEM004Tv30 pzemBdcst(&Serial3, 0x00); //Broadcast
PZEM004Tv30 pzemFrameGroup[] = {PZEM004Tv30(&Serial3, 0x42), PZEM004Tv30(&Serial3, 0x43),
                                PZEM004Tv30(&Serial3, 0x44), PZEM004Tv30(&Serial3, 0x45),
                                PZEM004Tv30(&Serial3, 0x46), PZEM004Tv30(&Serial3, 0x47),
                                PZEM004Tv30(&Serial3, 0x48), PZEM004Tv30(&Serial3, 0x49)
                               };
//--------------------------
void setup() {
  Serial.begin(115200); //This is the speed for serial monitoring
  Serial2.begin(9600);  //Speed for serial comm with raspberry pi through USB Serial FTDI adapter
  delay(200);
  statusArray[30] = enabled; //Status flag to always check serial available
}

void loop() {
  unsigned long currentMillis = millis();
  windSpeed = (analogRead(A0)); //Read wind speed (0-5V) connected to analog input A0
  windSpeed = (windSpeed * 30) / 1023; //According to manual max speed range is around 30m/s WARNING
  sensorsGroup[0][0] = windSpeed; //wind speed sensor location in float Sensor Array
  frameSensors1[1] = windSpeed; //wind speed sensor location in float Sensor Array
  frameSensors1[2] = windSpeed + .5; //Definition pending
  frameSensors1[3] = windSpeed + .7; //Definition pending
  frameSensors1[4] = windSpeed + .8; //Definition pending
  frameSensors1[5] = windSpeed + 1.1; //Definition pending
  frameSensors1[6] = windSpeed + 1.3; //Definition pending

  //This block is for testing purpose
  if (currentMillis - previousMillis1 >= interval1) {
    previousMillis1 = currentMillis; // save the last time you blinked the LED
    for (int blockFrame1 = 0; blockFrame1 < 4; blockFrame1++) {
      //pzemGetter(frameTransfer, pzemFrameGroup[blockFrame1], busyIndex = blockFrame1 + 8);
      pzemGetter(frameTransfer, pzemFrameGroup[blockFrame1], statusArray, busyIndex = blockFrame1 + 8);
      statusArray[blockFrame1] = voltageDetect(frameTransfer[1]); //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
      for (int elementIndex = 0; elementIndex < 8; elementIndex++) {
        pzemGroup[blockFrame1][elementIndex] = frameTransfer[elementIndex];
      }
    }
  }

  if (currentMillis - previousMillis2 >= interval2) {
    previousMillis2 = currentMillis; // save the last time you blinked the LED
    for (int blockFrame1 = 4; blockFrame1 < 8; blockFrame1++) {
      //pzemGetter(frameTransfer, pzemFrameGroup[blockFrame1], busyIndex = blockFrame1 + 8);
      pzemGetter(frameTransfer, pzemFrameGroup[blockFrame1], statusArray, busyIndex = blockFrame1 + 8);
      statusArray[blockFrame1] = voltageDetect(frameTransfer[1]); //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
      for (int elementIndex = 0; elementIndex < 8; elementIndex++) {
        pzemGroup[blockFrame1][elementIndex] = frameTransfer[elementIndex];
      }
    }
  }
}//End loop function

//Detect and process command request from raspberry
void serialEvent2() {
  raspCommand = (char)Serial2.read(); //A command char received from raspberry
  //Serial.println(raspCommand);
  bool flagToFloatTransmit = false;
  int pzemPositioner = 0;
  if (raspCommand >= 'a' && raspCommand <= 'i') {
    flagToFloatTransmit = true; //For future reference a string must be defined to expand options of can be decided
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
  } else if (raspCommand == 'i') {
    float checkSumFloat = 0.0;
    frameSensors1[0] = 11.07;
    for (int sumIndexer = 0; sumIndexer < 7; sumIndexer++) {
      checkSumFloat = checkSumFloat + frameSensors1[sumIndexer];
    }
    frameSensors1[7] = checkSumFloat; //I added this one as a personal final element verification in raspberry
    Serial2.write((byte*) &frameSensors1, floatsToSend * sizeof(float));
    return;
  } else if (raspCommand == 'j') {
    statusArray[29]++;
    byte checkSumStatus = 0;
    for (int checkAdder = 0; checkAdder < 31; checkAdder++) {
      checkSumStatus = checkSumStatus + statusArray[checkAdder];
    }
    statusArray[31] = checkSumStatus;
    Serial2.write((byte*)&statusArray, sizeof(statusArray));
    return;
  } else if (raspCommand == 'k') {
    Serial2.write(enabled);
    return;
  } else if (raspCommand == 'l') {
    //pzemBdcst.resetEnergy(); //General reset
    for (int resetCycler = 0; resetCycler < sizeof(pzemFrameGroup); resetCycler++) {
      if (statusArray[resetCycler] == enabled) {
        pzemFrameGroup[resetCycler].resetEnergy();
        statusArray[resetCycler + 16] = enabled;
      }
      else {
        statusArray[resetCycler + 16] = disabled;
      }
    }
    Serial2.write(enabled);
    return;
  }
  if (flagToFloatTransmit) {
    for (int indexToSerial = 0; indexToSerial < 8; indexToSerial++) {
      fFrameToSerial[indexToSerial] = pzemGroup[pzemPositioner][indexToSerial];
      //Serial.println(fFrameToSerial[indexToSerial]);
    }
    float checkSumFloat = 0.0;
    fFrameToSerial[0] = 11.07;
    for (int sumIndexer = 0; sumIndexer < 7; sumIndexer++) {
      checkSumFloat = checkSumFloat + fFrameToSerial[sumIndexer];
    }
    fFrameToSerial[7] = checkSumFloat; //I added this one as a personal final element verification in raspberry
    Serial2.write((byte*) &fFrameToSerial, floatsToSend * sizeof(float));
    return;
  }
}

//Function definition to get data from energy modules pzem004t installed in the same bus. Code efficiency
void pzemGetter (float frmEnergy[], PZEM004Tv30 pzemModule, byte statusFlagger[], byte busyFlagLocator) {
  statusFlagger[busyFlagLocator] = enabled;
  frmEnergy[0] = 11.07; //I added this one as a personal initial element verification in raspberry
  frmEnergy[1] = pzemModule.voltage();
  if (isnan(frmEnergy[1]) || (frmEnergy[1] > 300)) { //Validating voltage value in case of power off or bigger than expected
    frmEnergy[1] = -3.0;
  }
  //If there's no voltage then avoid requesting the rest of variables
  if (frmEnergy[1] == -3.0) {
    frmEnergy[2] = -3.0;
    frmEnergy[3] = -3.0;
    frmEnergy[4] = -3.0;
    frmEnergy[5] = -3.0;
    frmEnergy[6] = -3.0;
    frmEnergy[7] = 26.10; //I added this one as a personal final element verification in raspberry
    statusFlagger[busyFlagLocator] = disabled;
    return;
  }
  frmEnergy[2] = pzemModule.power();
  if ((isnan(frmEnergy[2])) || (frmEnergy[3] > 4000)) { //Validating power value in case of power off or bigger than expected for 110VAC
    frmEnergy[2] = -3.0;
  }
  frmEnergy[3] = pzemModule.current();
  if ((isnan(frmEnergy[3])) || (frmEnergy[3] > 100)) { //Validating voltage value in case of power off or bigger than max amperage pzem004t
    frmEnergy[3] = -3.0;
  }
  frmEnergy[4] = pzemModule.energy();
  if ((isnan(frmEnergy[4])) || (frmEnergy[4] > 2000)) { //Validating energy value in case of power off or bigger than expected
    frmEnergy[4] = -3.0;
  }
  frmEnergy[5] = pzemModule.frequency();
  if ((isnan(frmEnergy[5])) || (frmEnergy[5] > 100)) { //Validating frecuency value in case of power off or bigger than expected
    frmEnergy[5] = -3.0;
  }
  frmEnergy[6] = pzemModule.pf();
  if ((isnan(frmEnergy[6])) || (frmEnergy[6] > 2)) { //Validating pf value in case of power off or bigger than expected
    frmEnergy[6] = -3.0;
  }
  frmEnergy[7] = 0.0; // Will be used for checkSumFloat before serial transmission
  statusFlagger[busyFlagLocator] = disabled;
}

byte voltageDetect(float framElement) {
  if (framElement == -3) {
    return (disabled); //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
  }
  else {
    return (enabled); //set status bit energyzed in order to be read from raspberry
  }
}
