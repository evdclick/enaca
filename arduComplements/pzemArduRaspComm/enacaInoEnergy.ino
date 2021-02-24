//                    GNU GENERAL PUBLIC LICENSE
//                       Version 3, 29 June 2007
//
// Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
// Everyone is permitted to copy and distribute verbatim copies
//of this license document, but changing it is not allowed.

//Enacaino-energy V1.0
//Last modification 24-feb-2021
//This code applies for energy monitoring device PZEM-004 V3 with Arduino Mega 2560.
//Created by: William Jiménez

#include <SoftwareSerial.h>
#include <PZEM004Tv30.h>

byte inact = 150;
byte act = 180;
float windSpeed = 0.00;
#define FLOATS_SENT 8
float frameHouseF1[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the house
float frameHouseF2[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the house
float frameApt1F1[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt1
float frameApt1F2[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt1
float frameApt2F1[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt2
float frameApt2F2[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt2
float frameMiniLocalF1[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt2
float frameMiniLocalF2[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt2
float frameSensors1[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt2
byte statusArray[32];
unsigned long previousMillis = 0;        // will store last time LED was updated
const long interval = 1500;           // interval at which to blink (milliseconds)
//Energy monitoring's address device is defined with another separate and code for using with one at a time
PZEM004Tv30 pzemHouseF1(&Serial3, 0x42); //PZEM module for house phase 1
PZEM004Tv30 pzemHouseF2(&Serial3, 0x43); //PZEM module for house phase 2
PZEM004Tv30 pzemApt1F1(&Serial3, 0x44); //PZEM module for aparment 1 phase 1
PZEM004Tv30 pzemApt1F2(&Serial3, 0x45); //PZEM module for aparment 1 phase 2
PZEM004Tv30 pzemApt2F1(&Serial3, 0x46); //PZEM module for aparment 2 phase 1
PZEM004Tv30 pzemApt2F2(&Serial3, 0x47); //PZEM module for aparment 2 phase 2
PZEM004Tv30 pzemMiniLocalF1(&Serial3, 0x48); //PZEM module for small business phase 1
PZEM004Tv30 pzemMiniLocalF2(&Serial3, 0x49); //PZEM module for small business phase 2


char raspCommand;
bool charComplete = false;
void setup() {
  Serial.begin(115200); //This is the speed for serial monitoring
  Serial2.begin(9600);  //Speed for serial comm with raspberry pi through TTL leveler

  //pzemHouse.resetEnergy(); //In case you need to reset energy totalizer uncomment this for the specific module
  delay(200);
  // put your setup code here, to run once:
}

void loop() {
  unsigned long currentMillis = millis();
  windSpeed = (analogRead(A0)); //Read wind speed (0-5V) connected to analog input A0
  windSpeed = (windSpeed * 30) / 1023; //According to manual max speed range is around 30m/s
  //WARNING
  frameHouseF1[0] = windSpeed;  //Element Zero is available for each array. Please fill it with any float value to avoid errors in serial comm
  frameSensors1[0] = windSpeed; //Sensors will have an independent float array
  frameSensors1[1] = windSpeed + .5; //Sensors will have an independent float array
  frameSensors1[2] = windSpeed + .7; //Sensors will have an independent float array
  frameSensors1[3] = windSpeed + .8; //Sensors will have an independent float array
  frameSensors1[4] = windSpeed + 1.1; //Sensors will have an independent float array
  frameSensors1[5] = windSpeed + 1.3; //Sensors will have an independent float array
  frameSensors1[6] = windSpeed + 1.5; //Sensors will have an independent float array
  frameSensors1[7] = windSpeed + 1.8; //Sensors will have an independent float array

  if (currentMillis - previousMillis >= interval) {
    // save the last time you blinked the LED
    previousMillis = currentMillis;
    //Leer en primer módulo todos los datos de energía
    pzemGetter(frameHouseF1, pzemHouseF1);
    if (frameHouseF1[1] == -3) {
      statusArray[0] = inact;
    }
    else {
      statusArray[0] = act;
    }
    pzemGetter(frameHouseF2, pzemHouseF2);
    if (frameHouseF2[1] == -3) {
      statusArray[1] = inact;
    }
    else {
      statusArray[1] = act;
    }
    //  pzemGetter(frameApt1F1, pzemApt1F1);
    //  pzemGetter(frameApt1F2, pzemApt1F2);
    //  pzemGetter(frameApt2F1, pzemApt2F1);
    //  pzemGetter(frameApt2F2, pzemApt2F2);
    //  pzemGetter(frameMiniLocalF1, pzemMiniLocalF1);
    //  pzemGetter(frameMiniLocalF2, pzemMiniLocalF2);
  }
}

void serialEvent2() {
  raspCommand = (char)Serial2.read();
  switch (raspCommand) {
    case 'a':
      Serial2.write((byte*) &frameHouseF1, FLOATS_SENT * sizeof(float));
      break;
    case 'b':
      Serial2.write((byte*) &frameHouseF2, FLOATS_SENT * sizeof(float));
      break;
    case 'c':
      Serial2.write((byte*) &frameApt1F1, FLOATS_SENT * sizeof(float));
      break;
    case 'd':
      Serial2.write((byte*) &frameApt1F2, FLOATS_SENT * sizeof(float));
      break;
    case 'e':
      Serial2.write((byte*) &frameApt2F1, FLOATS_SENT * sizeof(float));
      break;
    case 'f':
      Serial2.write((byte*) &frameApt2F2, FLOATS_SENT * sizeof(float));
      break;
    /*  case 'g':
        Serial2.write((byte*) &FrameMiniLocalF1, FLOATS_SENT * sizeof(float));
        break;
      case 'h':
        Serial2.write((byte*) &FrameMiniLocalF2, FLOATS_SENT * sizeof(float));
        break;*/
    case 'i':
      Serial2.write((byte*) &frameSensors1, FLOATS_SENT * sizeof(float));
      break;
    case 'j':
      Serial2.write((byte*)&statusArray, sizeof(statusArray));
      //Serial2.write(statusArray, 32);
      break;
  }
}

//Function definition to get data from energy modules pzem004t installed in the same bus. Code efficiency
float pzemGetter (float frmEnergy[], PZEM004Tv30 pzemModule) {
  frmEnergy[1] = pzemModule.voltage();
  if (isnan(frmEnergy[1]) || (frmEnergy[1] > 500)) { //Validating voltage value in case of power off or bigger than expected
    frmEnergy[1] = -3.0;
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
  if ((isnan(frmEnergy[5])) || (frmEnergy[5] > 150)) { //Validating frecuency value in case of power off or bigger than expected
    frmEnergy[5] = -3.0;
  }
  frmEnergy[6] = pzemModule.pf();
  if ((isnan(frmEnergy[6])) || (frmEnergy[6] > 2)) { //Validating pf value in case of power off or bigger than expected
    frmEnergy[6] = -3.0;
  }
  frmEnergy[7] = 26.10; //I added this one as a personal final element verification in raspberry
}
