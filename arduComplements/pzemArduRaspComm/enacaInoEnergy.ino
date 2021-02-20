//Enacaino-energy V1.0
//Last modification 13-jan-2021
//This code applies for energy monitoring device PZEM-004 V3 with Arduino Mega 2560.
//Created by: William Jiménez


#include <SoftwareSerial.h>
#include <PZEM004Tv30.h>

float windSpeed = 0.00;
#define FLOATS_SENT 8
float frameHouse[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the house
float frameApt1[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt1
float frameApt2[FLOATS_SENT]; //Data frame that belongs to energy monitoring from the apt2

//Energy monitoring's address device is defined with another separate and code for using with one at a time
PZEM004Tv30 pzemHouse(&Serial3, 0x42); //PZEM module for house
PZEM004Tv30 pzemApto1(&Serial3, 0x43); //PZEM module for aparment 1
PZEM004Tv30 pzemApto2(&Serial3, 0x44); //PZEM module for aparment 2
char raspCommand;
bool charComplete = false;
void setup() {
  Serial.begin(115200); //This is the speed for serial monitoring
  Serial2.begin(9600);  //Speed for serial comm with raspberry pi through TTL leveler

  //pzemHouse.resetEnergy(); //In case you need to reset energy totalizer uncomment this for the specific module
  delay(500);
  // put your setup code here, to run once:
}

void loop() {
  windSpeed = (analogRead(A0)); //Read wind speed (0-5V) connected to analog input A0
  windSpeed = (windSpeed * 30) / 1023; //According to manual max speed range is around 30m/s
  //WARNING
  frameHouse[0] = windSpeed;  //Element Zero is available for each array. Please fill it with any float value to avoid errors in serial comm

  //Leer en primer módulo todos los datos de energía
  pzemGetter(frameHouse, pzemHouse);
  /*  Serial.println(frameHouse[1]);
    Serial.println(frameHouse[2]);
    Serial.println(frameHouse[3]);
    Serial.println(frameHouse[4]);
    Serial.println(frameHouse[5]);
    Serial.println(frameHouse[6]);
    Serial.println(frameHouse[7]);
  */
  if (charComplete == true) {
    //    Serial.println(inputString);
    if (raspCommand == 'A') { //'A' is the key code that device waits in order to transmit specific energy data from house
      Serial2.write((byte*) &frameHouse, FLOATS_SENT * sizeof(float));
    }
    raspCommand = 'B';
    //inputString = "";
    charComplete = false;
  }
  delay(300);
}

void serialEvent2() {
  raspCommand = (char)Serial2.read();
  Serial.println(raspCommand);
  charComplete = true;
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
