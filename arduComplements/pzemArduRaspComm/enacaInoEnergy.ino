//                    GNU GENERAL PUBLIC LICENSE
//                       Version 3, 29 June 2007
//
// Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
// Everyone is permitted to copy and distribute verbatim copies
//of this license document, but changing it is not allowed.

//Enacaino-energy V1.0
//Last modification 11-jul-2025
//This code applies for energy monitoring device PZEM-004 V3 with Arduino Mega 2560.
//Created by: William Jiménez

#include <PZEM004Tv30.h>
#include <SoftwareSerial.h>

SoftwareSerial pzemSWSerial(10, 11);  //Pins to connect to A/C energy monitors


byte disabled = 150;  //My own statement for True value in serial transmission
byte enabled = 180;   //My own statement for False value in serial transmission


bool flagForPzemReset = false;  //Temp flag to ensure reset condition
bool mqttTempFill = false;      //Temp flag to switch on pump VIA mqtt from raspberry
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
byte statusArray2[3][32];            //Will be used for redesign purpose status indicador for max 2D pzemGroup max [55][32]
//--------------------------
//===========Timing variables defined to scan energy modules according to priority assigned
unsigned long previousMillis1 = 50;  // will store last time for priority 1 group
const long interval1 = 2000;         // interval at which to scan pzem group #1 (milliseconds)
unsigned long previousMillis2 = 50;  // will store last time for priority 2 group
const long interval2 = 2000;         // interval at which to scan pzem group #2 (milliseconds)
unsigned long previousMillis3 = 50;  // will store last time for serial monitoring priority
const long interval3 = 2000;         // interval at which serial monitoring updates values for IDE
unsigned long previousMillis4 = 50;  // will store last time for serial monitoring priority
const long interval4 = 2000;         // interval at which serial monitoring updates values for IDE


//--------------------------
//===========Energy monitoring's address device is defined with another separate code for using with one at a time
PZEM004Tv30 pzemBdcst2(&Serial2, 0x00);      //This port for 0x42, 0x43, 0x44 and 0x45 modules
PZEM004Tv30 pzemBdcst3(&Serial3, 0x00);      //This port for 0x46, 0x47, 0x48 and 0x49 modules
PZEM004Tv30 pzemBdcst4(pzemSWSerial, 0x00);  //This port for 0x50 and 0x51 modules that monitor A/C

//pzemFrameGroup must be sized to 8 elements maximum
byte pzemFrameGroup[] = { 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x50, 0x51 };  //List of pzem addresses in communication bus
//Configuration function
void setup() {
  Serial.begin(115200);  //This is the speed for serial monitoring
  Serial1.begin(9600);   //Speed for serial comm with raspberry pi through USB Serial FTDI adapter
  delay(50);
  statusArray[30] = enabled;  //Status flag to always check serial available
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


  //First block of PZEM modules (Main feed and V1)
  if (currentMillis - previousMillis2 >= interval2) {
    previousMillis2 = currentMillis;  // save the last time you scan this group
    for (int blockFrame1 = 0; blockFrame1 < 4; blockFrame1++) {
      PZEM004Tv30 pzemM(&Serial2, pzemFrameGroup[blockFrame1]);                     //Define object at specific address according to pzemFrameGroup position
      pzemGetter(frameTransfer, pzemM, statusArray, busyIndex = blockFrame1 + 16);  //busyFlag position according to definition Table
      statusArray[blockFrame1] = voltageDetect(frameTransfer[1]);                   //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
      for (int elementIndex = 0; elementIndex < 8; elementIndex++) {
        pzemGroup[blockFrame1][elementIndex] = frameTransfer[elementIndex];  //Trannsfer from 1D array to specifc block in 2D array
      }
    }
  }

  //Second block of PZEM modules (V2 and me)
  if (currentMillis - previousMillis1 >= interval1) {
    previousMillis1 = currentMillis;  // save the last time you scan this group
    for (int blockFrame1 = 4; blockFrame1 < 8; blockFrame1++) {
      PZEM004Tv30 pzemM(&Serial3, pzemFrameGroup[blockFrame1]);                     //Define object at specific address according to pzemFrameGroup position
      pzemGetter(frameTransfer, pzemM, statusArray, busyIndex = blockFrame1 + 16);  //Call to upgrade values inside especific pzem module
      statusArray[blockFrame1] = voltageDetect(frameTransfer[1]);                   //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
      for (int elementIndex = 0; elementIndex < 8; elementIndex++) {
        pzemGroup[blockFrame1][elementIndex] = frameTransfer[elementIndex];  //Trannsfer from 1D array to specifc block in 2D array
      }
    }
  }

  //Third block of PZEM modules for A/C Machines. Only two modules are actually (2025-07-11) installed in this group
  if (currentMillis - previousMillis3 >= interval3) {
    previousMillis3 = currentMillis;                                 // save the last time you scan this group
    for (int blockFrame1 = 8; blockFrame1 < 10; blockFrame1++) {     //PZEM Modules por A/C located at pzemFrameGroup[8][8] and [9][8]
      PZEM004Tv30 pzemM(pzemSWSerial, pzemFrameGroup[blockFrame1]);  //Define object at specific address according to pzemFrameGroup position
      pzemGetter(frameTransfer, pzemM, statusArray, busyIndex = blockFrame1 + 16);
      statusArray[blockFrame1] = voltageDetect(frameTransfer[1]);  //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
      for (int elementIndex = 0; elementIndex < 8; elementIndex++) {
        pzemGroup[blockFrame1][elementIndex] = frameTransfer[elementIndex];  //Trannsfer from 1D array to specifc block in 2D array
      }
    }
  }

/*
  //Print results in serial monitor for debugging purposes
  if (currentMillis - previousMillis4 >= interval4) {
    previousMillis4 = currentMillis;  // save the last time printed values in serial monitor
    for (int i = 0; i < 10; i++) {
      for (int j = 0; j < 8; j++) {
        Serial.print(pzemGroup[i][j]);
        Serial.print(" ");
      }
      Serial.println();
    }
    Serial.println("/");
    Serial.println("======================================");
  }
*/


  //This section is to oneshot rain reservoir pump with Arduino while been away
  if (mqttTempFill == true) {
    mqttTempFill = false;
  }

  if (flagForPzemReset == true) {
    //Individually counter reset for PZEM group connected to Serial2
    PZEM004Tv30 pzemM1(&Serial2, 0x42);
    pzemM1.resetEnergy();
    PZEM004Tv30 pzemM2(&Serial2, 0x43);
    pzemM2.resetEnergy();
    PZEM004Tv30 pzemM3(&Serial2, 0x44);
    pzemM3.resetEnergy();
    PZEM004Tv30 pzemM4(&Serial2, 0x45);
    pzemM4.resetEnergy();

    //Individually counter reset for PZEM group connected to Serial3
    PZEM004Tv30 pzemM5(&Serial3, 0x46);
    pzemM5.resetEnergy();
    PZEM004Tv30 pzemM6(&Serial3, 0x47);
    pzemM6.resetEnergy();
    PZEM004Tv30 pzemM7(&Serial3, 0x48);
    pzemM7.resetEnergy();
    PZEM004Tv30 pzemM8(&Serial3, 0x49);
    pzemM8.resetEnergy();
    delay(2000);
    flagForPzemReset = false;
  }

}  //End loop function

//Detect and process command request from raspberry
void serialEvent1() {
  raspCommand = (char)Serial1.read();  //A command char received from raspberry
  //Serial.print("Interrupcion: ");
  //Serial.println(raspCommand);
  bool flagToFloatTransmit = false; //This one in order to request specific float array transmission if needed
  int pzemPositioner = 0;
  if ((raspCommand >= 'a' && raspCommand <= 'i')||(raspCommand == 'y' || raspCommand == 'z')) {
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
  //---------Temporalmente pido datos de los PZEM A/C en este bloque
  else if (raspCommand == 'y') {
    pzemPositioner = 8;
  } else if (raspCommand == 'z') {
    pzemPositioner = 9;
  }
  //-----------Fin Bloque
  else if (raspCommand == 'i') {
    frameSensors1[0] = 11.07;
    frameSensors1[7] = checkSumCalculatorF(frameSensors1);
    Serial1.write((byte*)&frameSensors1, floatsToSend * sizeof(float));
    return;
  } else if (raspCommand == 'j') {
    statusArray[29]++;
    statusArray[31] = checkSumCalculatorB(statusArray);
    Serial1.write((byte*)&statusArray, sizeof(statusArray));
    return;
  } else if (raspCommand == 'k') {
    Serial1.write(enabled);
    return;
  } else if (raspCommand == 'l') {
    //Serial.println("RECEIVED RESET COMMAND");
    flagForPzemReset = true;

    //pzemBdcst3.resetEnergy(); Global reset for softwareSerial instance

    /*This section will not be in the field until octubre 2025
    for (int resetCycler = 0; resetCycler < sizeof(pzemFrameGroup); resetCycler++) {
      PZEM004Tv30 pzemM(&Serial2, pzemFrameGroup[resetCycler]);
      if (statusArray[resetCycler] == enabled) {
        pzemM.resetEnergy();
        statusArray[resetCycler + 16] = enabled;
      } else {
        statusArray[resetCycler + 16] = disabled;
      }
    }
*/
    Serial1.write(enabled);

    return;
  } else if (raspCommand == 'm') {
    mqttTempFill = true;
  } else if (raspCommand == 'r') {
    byte byteFrame[32];
    byte indexFr;
    for (indexFr = 0; indexFr < 32; indexFr++) {
      delay(2);
      if (Serial1.available() > 0) {
        byteFrame[indexFr] = byte(Serial1.read());
      }
    }
    return;
  }
  if (flagToFloatTransmit) {
    for (int indexToSerial = 0; indexToSerial < 8; indexToSerial++) {
      fFrameToSerial[indexToSerial] = pzemGroup[pzemPositioner][indexToSerial];
    }
    fFrameToSerial[0] = 11.07;
    fFrameToSerial[7] = checkSumCalculatorF(fFrameToSerial);
    Serial1.write((byte*)&fFrameToSerial, floatsToSend * sizeof(float));
    return;
  }
}

//Function definition to get data from energy modules pzem004t installed in the same bus. Code efficiency
void pzemGetter(float frmEnergy[], PZEM004Tv30 pzemModule, byte statusFlagger[], byte busyFlagLocator) {
  statusFlagger[busyFlagLocator] = enabled;
  frmEnergy[0] = 11.07;  //I added this one as a personal initial element verification in raspberry
  frmEnergy[1] = pzemModule.voltage();
  if (isnan(frmEnergy[1]) || (frmEnergy[1] > 500)) {  //Validating voltage value in case of power off or bigger than expected
    frmEnergy[1] = -3.0;
  }
  //If there's no voltage then avoid requesting the rest of variables
  if (frmEnergy[1] == -3.0) {
    frmEnergy[2] = -3.0;
    frmEnergy[3] = -3.0;
    frmEnergy[4] = -3.0;
    frmEnergy[5] = -3.0;
    frmEnergy[6] = -3.0;
    frmEnergy[7] = 26.10;  //I added this one as a personal final element verification in raspberry
    statusFlagger[busyFlagLocator] = disabled;
    return;
  }
  frmEnergy[2] = pzemModule.power();
  if ((isnan(frmEnergy[2])) || (frmEnergy[3] > 4000)) {  //Validating power value in case of power off or bigger than expected for 110VAC
    frmEnergy[2] = -3.0;
  }
  frmEnergy[3] = pzemModule.current();
  if ((isnan(frmEnergy[3])) || (frmEnergy[3] > 100)) {  //Validating voltage value in case of power off or bigger than max amperage pzem004t
    frmEnergy[3] = -3.0;
  }
  frmEnergy[4] = pzemModule.energy();
  if ((isnan(frmEnergy[4])) || (frmEnergy[4] > 2000)) {  //Validating energy value in case of power off or bigger than expected
    frmEnergy[4] = -3.0;
  }
  frmEnergy[5] = pzemModule.frequency();
  if ((isnan(frmEnergy[5])) || (frmEnergy[5] > 100)) {  //Validating frecuency value in case of power off or bigger than expected
    frmEnergy[5] = -3.0;
  }
  frmEnergy[6] = pzemModule.pf();
  if ((isnan(frmEnergy[6])) || (frmEnergy[6] > 2)) {  //Validating pf value in case of power off or bigger than expected
    frmEnergy[6] = -3.0;
  }
  frmEnergy[7] = 0.0;  // Will be used for checkSumFloat before serial transmission
  statusFlagger[busyFlagLocator] = disabled;
}
