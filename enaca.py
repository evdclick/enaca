#                    GNU GENERAL PUBLIC LICENSE
#                       Version 3, 29 June 2007
#
# Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
# Everyone is permitted to copy and distribute verbatim copies
# of this license document, but changing it is not allowed.
#=====================================================
#Last modification: 2026-02-04
#run enaca.py as this example:.
#nohup python enaca.py >/dev/null 2>&1&
#Library import in order to make the script works propertly
import datetime
import paho.mqtt.client as paho
import RPi.GPIO as GPIO
import serial
import sys
import struct
import time
import schedule #To be used as schedule for timed events
import numpy as np
import random
from time import sleep
import traceback
sys.path.append('./scriptsComm') #Relative path that applies to raspberry
from topicTide import *

#Rasperry inputs to be used as pulse counter for water flow
GPIO.setmode (GPIO.BCM)
GPIO.setup(18, GPIO.IN)
GPIO.setup(23, GPIO.IN)
GPIO.setup(24, GPIO.IN)
GPIO.setup(25, GPIO.IN)

#Variables for True and False to ensure communications
disabled = 150
enabled = 180

#Variables for scheduling events
flagEach5Minute01=False
flagEachHour01=False
flagEachDay01=False
flagEachEndDay01=False

#Oficially defined and controlled variables for comms and processing
serialReboots=0 #Keep counts of serial.open/serial.close
outRangeFloats=0 #Keep counts when out of range floats are received
serialTransactions=0 #Number of times serial queries executed in lines of while loop
executionsFinished=0 #Keep count of complete program execution
exceptionsDetected=0 #Keep count of exceptions events detected
serialExceptionsDetected=0
cleanData=0 #How much serial data request have been received clean data
windSpeed=0
execTime=0 #Amount of seconds used to execute complete script
countBackForReset=disabled
# IF NOT USED, DELETE... myData = ['A']*8 #Init array of string to receive bytes struct packets
#############################Start of 3D block implementation for future try
latestNormal1 = [0.0]*8      #List of 8 float to hold bkp data from PZEM House F1
energyModuleData1 = [0.0]*8  #List of 8 floats to receive data from PZEM House F1
latestNormal2 = [0.0]*8      #List of 8 float to hold bkp data from PZEM House F2
energyModuleData2 = [0.0]*8  #List of 8 floats to receive data from PZEM House F2
latestNormal3 = [0.0]*8      #List of 8 float to hold bkp data from PZEM Apt1 F1
energyModuleData3 = [0.0]*8  #List of 8 floats to receive data from PZEM Apt1 F1
latestNormal4 = [0.0]*8      #List of 8 float to hold bkp data from PZEM Apt1 F2
energyModuleData4 = [0.0]*8  #List of 8 floats to receive data from PZEM Apt1 F2
latestNormal5 = [0.0]*8      #List of 8 float to hold bkp data from PZEM Apt2 F1
energyModuleData5 = [0.0]*8  #List of 8 floats to receive data from PZEM Apt2 F1
latestNormal6 = [0.0]*8      #List of 8 float to hold bkp data from PZEM Apt2 F2
energyModuleData6 = [0.0]*8  #List of 8 floats to receive data from PZEM Apt2 F2
latestNormal7 = [0.0]*8      #List of 8 float to hold bkp data from PZEM small business F1
energyModuleData7 = [0.0]*8  #List of 8 floats to receive data from PZEM small business F1
latestNormal8 = [0.0]*8      #List of 8 float to hold bkp data from PZEM small business F2
energyModuleData8 = [0.0]*8  #List of 8 floats to receive data from PZEM small business F2
latestNormal50 = [0.0]*8      #List of 8 float to hold bkp data from PZEM A/C V1
energyModuleData50 = [0.0]*8  #List of 8 floats to receive data from PZEM A/C V1
latestNormal51 = [0.0]*8      #List of 8 float to hold bkp data from PZEM A/C V2
energyModuleData51 = [0.0]*8  #List of 8 floats to receive data from PZEM A/C V2
##############################This block can be packed in a 3D array, but actually not implemented

latestNormal9 = [0.0]*8      #List of 8 float to hold bkp data from sensors group 1
sensorsModuleData9 = [0.0]*8 #List of 8 float to receive data from sensors group 1
statusArray10 = []*32        #List of 32 bytes related to pzem status and others
statusArray11 = []*32        #List of 32 bytes related to pzem status and others
cmdAndStatusFromRasp1=[180]*32 #List of 32 bytes related to command and status from raspberry to Mega


#counter init values for water consumption
totalizer = 0
acumHouse = 0
acumApt1 = 0
acumApt2 = 0

#Variables for MQTT server
mqttc = paho.Client()
host = "192.168.15.102" #Server IP can be selected as you desire
door = []
port = 1883 #The one that mosquitto uses

class bcolors: #To be used for displaying alarms when debugging
 HEADER = '\033[95m'
 OKBLUE = '\033[94m'
 OKGREEN = '\033[92m'
 WARNING = '\033[93m'
 FAIL = '\033[91m'
 ENDC = '\033[0m'
 BOLD = '\033[1m'
 UNDERLINE = '\033[4m'

#print("Por aquí no vuelvo a pasar")
#Group of functions for scheduling events
def schTask1():
 global flagEach5Minute01
 flagEach5Minute01=True
 return
def schTask2():
 global flagEachHour01
 flagEachHour01=True
 return
def schTask3():
 global flagEachDay01
 flagEachDay01=True
 return
def schTask4():
 global flagEachEndDay01
 flagEachEndDay01=True
 return
#----------------------------------------------


def writeBytesArray(bytePack, writeCommand):
 binaryList = bytearray(bytePack)
 comArdu.write(writeCommand.encode())
 comArdu.write(binaryList)
 comArdu.reset_input_buffer()
 comArdu.reset_output_buffer()
 return

#Function to upgrade energy module information or some other array of 8 float elements
def comPzemCycler(ofversion, bkpversion, readCommand):
 global serialTransactions
 global outRangeFloats
 global cleanData
 statusCleanData=True
 serialTransactions+=1
 statusBefore=enabled
 incompleteArraySet=[-2]*8
 incompleteByteSet=[]
 if statusBefore==enabled:
  comArdu.write(readCommand.encode()) #Keyword used to be sure about what is expected to receive energy data from specific pzem module
  numberStuffs=[0]*32
  byteData = comArdu.read(32)
  if len(byteData)<32:
   for partialElement in incompleteArraySet:
    incompleteByteSet.append(struct.pack('f',partialElement))
   unpackCounter=0
   for unpackElement in incompleteByteSet:
    ofversion[unpackCounter]=(struct.unpack('f',unpackElement))
    unpackCounter+=1
  else:
   ofversion[0]=struct.unpack('f', byteData[0:4]) #Unpack to float
   ofversion[1]=struct.unpack('f', byteData[4:8]) #Unpack to float
   ofversion[2]=struct.unpack('f', byteData[8:12]) #Unpack to float
   ofversion[3]=struct.unpack('f', byteData[12:16]) #Unpack to float
   ofversion[4]=struct.unpack('f', byteData[16:20]) #Unpack to float
   ofversion[5]=struct.unpack('f', byteData[20:24]) #Unpack to float
   ofversion[6]=struct.unpack('f', byteData[24:28]) #Unpack to float
   ofversion[7]=struct.unpack('f', byteData[28:32]) #Unpack to float
  #ofversion=list(ofversion)
  for i in range (0, 8):
   #ofversion[i]=round(ofversion[i],2)
   tempTuple =  ofversion[i]
   ofversion[i] = np.array(tempTuple, dtype=float) #Convert the tupple back to numpy array
   ofversion[i]=np.round(ofversion[i], decimals=2)
   ofversion[i] = float(ofversion[i]) #Numpy Array element back to float to avoid brackets when printing
   if (ofversion[i]==-3): #Check if it was a power off
    continue
   elif (ofversion[i]<0 or ofversion[i]>10000): #Just to check if the number is extremely out of range
    ofversion[i]=bkpversion[i]
    outRangeFloats+=1
    statusCleanData=False
    continue
   else:
    bkpversion[i]=ofversion[i]
  if (ofversion[1]==-3): #Analyze the whole list in case of PZEM for power off condition
   ofversion[4]=bkpversion[4] #Keep energy consumption info available
   ofversion[0]=disabled #powerStatus will be in this position for PZEMs
   ofversion[1]=0
   ofversion[2]=0
   ofversion[3]=0
   ofversion[5]=0
   ofversion[6]=0
 else:
  comArdu.close()
  comArdu.open()
 sumForCheck = sum(ofversion[:7]) #Determine check sum from list of data received
 difference = abs(sumForCheck-ofversion[7]) #Compare their difference with the one calculated in ardu mega
 if (difference>2): #Don't consider as clean data in case of difference bigger than 2
  statusCleanData=False
 if statusCleanData: #If everything is fine, keep counting clean data
  cleanData+=1
 comArdu.reset_input_buffer()
 comArdu.reset_output_buffer()
 return(ofversion, bkpversion, readCommand)

#Function to retrieve array of bytes through serial connection
def readByteArrayInSerial(charCommand):
 global serialReboots
 global serialTransactions
 global cleanData
 statusCleanData=True
 serialTransactions+=1
 numberStuffs=[0]*32
 comArdu.write(charCommand.encode()) #Keyword used to be sure about what is expected to receive from raspberry
 intData = comArdu.read(32)
 if len(intData)==32:
  numColector=0
  checkSumTracker=0
  for byteElement in intData:
   numberStuffs[numColector]=byteElement #ord(byteElement) implicit
   if numColector<31:
    checkSumTracker=checkSumTracker+numberStuffs[numColector]
   numColector+=1
  checkSumTracker=checkSumTracker & (0x00ff)
  if checkSumTracker != numberStuffs[31]:
   statusCleanData=False
   statusCleanData=False
   numberStuffs[30]=disabled
   comArdu.close()
   comArdu.open()
   serialReboots+=1
  if (numberStuffs[30]!=enabled): #This frame cannot be trusted if default enabled status is not received
   statusCleanData=False
   numberStuffs[30]=disabled
   comArdu.close()
   comArdu.open()
   serialReboots+=1
 else:
  numberStuffs[30]=disabled
  comArdu.close()
  comArdu.open()
  serialReboots+=1
  statusCleanData=False
 if statusCleanData:
  cleanData+=1
 comArdu.reset_input_buffer()
 comArdu.reset_output_buffer()
 arraySet=numberStuffs
 return(numberStuffs)

def checkSerial():
  global serialReboots
  global serialTransactions
  global cleanData
  statusCleanData=True
  serialTransactions+=1
  internalComChecker=comArdu.write('l'.encode())
  statusChecking=comArdu.read()
  if len(statusChecking)>0:
   statusChecking=ord(statusChecking)
   if statusChecking!=enabled:
    statusChecking=disabled
    statusCleanData=False
  else:
   #print(statusChecking)
   comArdu.close()
   comArdu.open()
   serialReboots+=1
   statusChecking=disabled
   statusCleanData=False
  if statusCleanData:
   cleanData+=1
  comArdu.reset_input_buffer()
  comArdu.reset_output_buffer()
  return(statusChecking)

#Calculate checksum from a given byte array of all elements except last one
def checkSumByteSender(byteList):
 checkSumByteSolver=0
 for byteElement in range(len(byteList)-1):
  checkSumByteSolver=checkSumByteSolver + byteList[byteElement]
 checkSumByteSolver=checkSumByteSolver & (0x00ff)
 return(checkSumByteSolver)

#Rising events for flow sensor totalizer input #4
def counterPlus(channel):
 global totalizer
 if GPIO.input(channel)>0.5: #Get pulse
  totalizer+=1
  controlsGroup[0][4]=totalizer
  statusGroup[0][2] = 1
 else:
  totalizer+=0
  controlsGroup[0][4]+=totalizer

def counterPlus1(channel):
 global acumApt1
 if GPIO.input(channel)>0.5: #Get pulse
  acumApt1+=1
  controlsGroup[2][11]=acumApt1
  statusGroup[2][4] = 1
 else:
  acumApt1+=0
  controlsGroup[2][11]=acumApt1

def counterPlus2(channel):
 global acumApt2
 if GPIO.input(channel)>0.5: #Get pulse
  acumApt2+=1
  controlsGroup[3][7]+=acumApt2
  statusGroup[3][3] = 1
 else:
  acumApt2+=0
  controlsGroup[3][7]=acumApt2

def counterPlus3(channel):
 global acumHouse
 if GPIO.input(channel)>0.5: #Get pulse
  acumHouse+=1
  controlsGroup[1][9]+=acumHouse
  statusGroup[1][5] = 1
 else:
  acumHouse+=0
  controlsGroup[1][9]=acumHouse

#Interrupt routines to count rising edges in digital inputs
GPIO.add_event_detect(18, GPIO.RISING, callback=counterPlus, bouncetime=3)
GPIO.add_event_detect(23, GPIO.RISING, callback=counterPlus1, bouncetime=3)
GPIO.add_event_detect(24, GPIO.RISING, callback=counterPlus2, bouncetime=3)
GPIO.add_event_detect(25, GPIO.RISING, callback=counterPlus3, bouncetime=3)

indicatorList = []
statusList = []
controlsList = []

for x in range(len(positionsBase)):
 indicatorList.append(0)
 statusList.append(0)
 controlsList.append(0)

indicatorsGroup = [list(indicatorList),
                   list(indicatorList),
                   list(indicatorList),
                   list(indicatorList),
                   list(indicatorList)]

statusGroup = [list(statusList),
               list(statusList),
               list(statusList),
               list(statusList),
               list(statusList)]

controlsGroup = [list(controlsList),
                 list(controlsList),
                 list(controlsList),
                 list(controlsList),
                 list(controlsList)]
#Definition of serial port object, speed and its timeout
#import serial
comArdu = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=1)
#Here the loop starts
for flagInitReset in range(12):
 cmdAndStatusFromRasp1[flagInitReset]=disabled
statusArray10=[180]*32
statusArray10[28]=enabled
statusArray11=[180]*32

#Scheduling init and process
#https://medium.com/@istuti.mce21/schedule-python-03d689d07b00
kWpricel=[0,680,505,505,1000]
alter1Before=[0,0,0,0,0]
alter1Now=[0,0,0,0,0]
alter2Before=[0,0,0,0,0]
alter2Now=[0,0,0,0,0]
moneyAcLimit=-1000
schedule.every(5).minutes.do(schTask1) #Time for data collection has been set to 5 in order to keep file not that large
schedule.every().hour.at(":00").do(schTask2)
schedule.every().day.at("00:01").do(schTask3)
schedule.every().day.at("23:59").do(schTask4)

#MQTT profile
#Function to explore EVD structure in topicTide.py and execute massive subscription to controls topics
def on_connect(client, userdata, flags, rc):
 for nodeCount in range(len(nodes)): #Get list of nodes #THIS LINE WAS BEFORE FOR TESTING # print ("on_connect() " + str(rc))
  for zoneCount in range(len(zones)): #Get list of zones
   for indexCount in range(len(positionsBase)): #Get number of index according to user needs
    topicRouteSubs = nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[2]+'/'+positionsBase[indexCount] #Set subscription topic only for controls category
    #print ("Subscribing to: "+ topicRouteSubs) #Uncomment this if you need to see what happend with each control topic before subscription
    mqttc.subscribe(topicRouteSubs) #Execute subscription to controls category
 print("Subscription completed for all topics in EVD structure") #Show confirmation when for loops is complete

def on_subscribe(client, userdata, mid, granted_qos):
 pass #Just in this case to to nothing if subscribe event is receive from the broker
 #print("Successful subscribed") #If you need confirmation for each subscribed topic in console uncomment this line

def on_message(client, userdata, msg): #This function is about on-screen events after receiving controls topics
 topic = msg.topic #THIS LINE WAS BEFORE FOR TESTING PURPOSE  #print("\n on_message() topic: "+msg.topic+"\n payload: "+str(msg.payload)+"\n")
 try: #Firs check if topic exist
  payloadContent = int(msg.payload)
  topicsMap = topic.split('/')
  door = lookSearch(topicsMap[0], topicsMap[1], topicsMap[2], topicsMap[3]) #Search for topic location
  controlsGroup[int(door[1])][int(door[3])] = payloadContent
 except: #The idea is to receive control commands as a number
  print("It's not possible. Strings cannot be processed in payload. Only Numbers")

mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message
#print("connecting to: "+host)
mqttc.connect(host, port, 60)
mqttc.loop_start()
while True:
 try:
  if controlsGroup[1][3] == enabled: #Individual request to zero Main PZEM
    cmdAndStatusFromRasp1[0]=enabled
    cmdAndStatusFromRasp1[1]=enabled
    controlsGroup[1][3] = disabled
  if controlsGroup[2][3] == enabled: #Individual request to zero V1 PZEM
    cmdAndStatusFromRasp1[2]=enabled
    cmdAndStatusFromRasp1[3]=enabled
    controlsGroup[2][3] = disabled
  if controlsGroup[3][3] == enabled: #Individual request to zero V2 PZEM
    cmdAndStatusFromRasp1[4]=enabled
    cmdAndStatusFromRasp1[5]=enabled
    controlsGroup[3][3] = disabled    
  if controlsGroup[4][3] == enabled: #Individual request to zero SmallBusiness PZEM
    cmdAndStatusFromRasp1[6]=enabled
    cmdAndStatusFromRasp1[7]=enabled
    controlsGroup[4][3] = disabled
  if controlsGroup[2][0] == enabled and statusArray11[8]==disabled: #Solicitud para poner a cero medidor de energía A/C V1
   cmdAndStatusFromRasp1[8]=enabled
   controlsGroup[2][0] = disabled
  if controlsGroup[3][0] == enabled and statusArray11[9]==disabled: #Solicitud para poner a cero medidor de energía A/C V2
   cmdAndStatusFromRasp1[9]=enabled
   controlsGroup[3][0] = disabled  
  if controlsGroup[2][2] == enabled:
   cmdAndStatusFromRasp1[10]=enabled #SET A/C V1 Via MQTT
  else:
   cmdAndStatusFromRasp1[10]=disabled
  if controlsGroup[3][2] == enabled:
   cmdAndStatusFromRasp1[11]=enabled #SET A/C V2 Via MQTT
  else:
   cmdAndStatusFromRasp1[11]=disabled   
  cmdAndStatusFromRasp1[31]=checkSumByteSender(cmdAndStatusFromRasp1) #Simple test to calculate checksum
  #List of bytes and status commands to Arduino Mega in order to execute
  #specific instructions according to table specs in excel profile and
  #certain descriptions within lines in this code
  writeBytesArray(cmdAndStatusFromRasp1, writeCommand='u') #Then send byte array
  for globalFlagReset in range(10): 
   cmdAndStatusFromRasp1[globalFlagReset]=disabled #Setting back global reset to normal  
  #------------------------
  execIniTime = time.time()
  statusBefore=checkSerial()
  if statusBefore!=enabled:
   comArdu.close()
   comArdu.open()
   serialReboots+=1
  statusArray11=readByteArrayInSerial(charCommand='y')
  statusArray10=readByteArrayInSerial(charCommand='z') 
  #0.4seg
#Partially isolated block
  if statusArray10[30]!=enabled:
   comArdu.close()
   comArdu.open()
   serialReboots+=1
#=======
#===========Retrieve data 8 float array PZEM function Definition =========
#Check if voltage is ON and there's not busy flag from Arduino Mega
  #Block to read PZEM modules from House
  with open('saldoAC.txt') as batchPayedAC:
   lotePrepagoAC=batchPayedAC.readlines()
   if len(lotePrepagoAC)==2:
    indicatorsGroup[2][41]=int(lotePrepagoAC[0])
    indicatorsGroup[3][41]=int(lotePrepagoAC[1])  
  autoIncrementMark=statusArray10[29]
  statusBefore=checkSerial()
  #0.5 a 1.1seg
  ##Remeber that serialEvent1 in Arduino has a condition to identify when to send float array and must be partially config
  #Block te read PZEM Modeules from main feed. Ni idea sobre el motivo pero fue necesario comenzar por la letra 'b'
  if (statusArray10[1]==enabled and statusArray10[17]==disabled and statusBefore==enabled) or (statusArray10[1]==disabled and energyModuleData2[1]>0):
   comPzemCycler(energyModuleData2, latestNormal2, readCommand='b')
   for j in range (8,16):
    indicatorsGroup[1][j]=energyModuleData2[j-8] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[1][16]=round(indicatorsGroup[1][4]+indicatorsGroup[1][12],1) #Asign sum of energy
   indicatorsGroup[1][17]=int(indicatorsGroup[1][16]*kWpricel[1]) #Asign paying bill value
   indicatorsGroup[1][18]=round(indicatorsGroup[1][2]+indicatorsGroup[1][10],1) #Asign sum of instant power
   indicatorsGroup[1][19]=int((indicatorsGroup[1][18]/1000)*kWpricel[1]) #Asign money for instant power
  if (statusArray10[0]==enabled and statusArray10[16]==disabled and statusBefore==enabled) or (statusArray10[0]==disabled and energyModuleData1[1]>0):
   comPzemCycler(energyModuleData1, latestNormal1, readCommand='a')
   for j in range (0,8):
    indicatorsGroup[1][j]=energyModuleData1[j] #indicators axes that belongs to main feed
  statusBefore=checkSerial()
  #Block to read PZEM modules from Apartment1
  statusBefore=checkSerial()
  if (statusArray10[2]==enabled and statusArray10[18]==disabled and statusBefore==enabled) or (statusArray10[2]==disabled and energyModuleData3[1]>0):
   comPzemCycler(energyModuleData3, latestNormal3, readCommand='c')
   for j in range (0,8):
    indicatorsGroup[2][j]=energyModuleData3[j] #indicators axes that belongs to general.... testing purpose
  statusBefore=checkSerial()
  if (statusArray10[3]==enabled and statusArray10[19]==disabled and statusBefore==enabled) or (statusArray10[3]==disabled and energyModuleData4[1]>0):
   comPzemCycler(energyModuleData4, latestNormal4, readCommand='d')
   for j in range (8,16):
    indicatorsGroup[2][j]=energyModuleData4[j-8] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[2][16]=round(indicatorsGroup[2][4]+indicatorsGroup[2][12],1) #Asign sum of energy
   indicatorsGroup[2][17]=int(indicatorsGroup[2][16]*kWpricel[2]) #Asign paying bill value
   indicatorsGroup[2][18]=round(indicatorsGroup[2][2]+indicatorsGroup[2][10],1) #Asign sum of instant power
   indicatorsGroup[2][19]=round((indicatorsGroup[2][18]/1000)*kWpricel[2]) #Asign money for instant power
  #Block to read PZEM modules from Apartment2
  statusBefore=checkSerial()
  if (statusArray10[4]==enabled and statusArray10[20]==disabled and statusBefore==enabled) or (statusArray10[4]==disabled and energyModuleData5[1]>0):
   comPzemCycler(energyModuleData5, latestNormal5, readCommand='e')
   for j in range (0,8):
    indicatorsGroup[3][j]=energyModuleData5[j] #indicators axes that belongs to general.... testing purpose
  statusBefore=checkSerial()
  if (statusArray10[5]==enabled and statusArray10[21]==disabled and statusBefore==enabled) or (statusArray10[5]==disabled and energyModuleData6[1]>0):
   comPzemCycler(energyModuleData6, latestNormal6, readCommand='f')
   for j in range (8,16):
    indicatorsGroup[3][j]=energyModuleData6[j-8] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[3][16]=round(indicatorsGroup[3][4]+indicatorsGroup[3][12],1) #Asign sum of energy
   indicatorsGroup[3][17]=int(indicatorsGroup[3][16]*kWpricel[3]) #Asign paying bill value
   indicatorsGroup[3][18]=round(indicatorsGroup[3][2]+indicatorsGroup[3][10],1) #Asign sum of instant power
   indicatorsGroup[3][19]=round((indicatorsGroup[3][18]/1000)*kWpricel[3]) #Asign money for instant power
  #Block to read PZEM modules from Mini Local
  statusBefore=checkSerial()
  if (statusArray10[6]==enabled and statusArray10[22]==disabled and statusBefore==enabled) or (statusArray10[6]==disabled and energyModuleData7[1]>0):
   comPzemCycler(energyModuleData7, latestNormal7, readCommand='g')
   for j in range (0,8):
    indicatorsGroup[4][j]=energyModuleData7[j] #indicators axes that belongs to general.... testing purpose
  statusBefore=checkSerial()
  if (statusArray10[7]==enabled and statusArray10[23]==disabled and statusBefore==enabled) or (statusArray10[7]==disabled and energyModuleData8[1]>0):
   comPzemCycler(energyModuleData8, latestNormal8, readCommand='h')
   for j in range (8,16):
    indicatorsGroup[4][j]=energyModuleData8[j-8] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[4][16]=round(indicatorsGroup[4][4]+indicatorsGroup[4][12],1) #Asign sum of energy
   indicatorsGroup[4][17]=int(indicatorsGroup[4][16]*kWpricel[4]) #Asign paying bill value
   indicatorsGroup[4][18]=round(indicatorsGroup[4][2]+indicatorsGroup[4][10],1) #Asign sum of instant power
   indicatorsGroup[4][19]=round((indicatorsGroup[4][18]/1000)*kWpricel[4]) #Asign money for instant power

#------------Leave this block alone to retrieve PZEM A/C data testing purposes
  statusBefore=checkSerial()
  if (statusArray10[8]==enabled and statusArray10[24]==disabled and statusBefore==enabled) or (statusArray10[8]==disabled and energyModuleData50[1]>0):
   comPzemCycler(energyModuleData50, latestNormal50, readCommand='i')
   for j in range (32,40):
    indicatorsGroup[2][j]=energyModuleData50[j-32] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[2][40]=int(indicatorsGroup[2][36]*kWpricel[4]) #Asign paying bill value
   indicatorsGroup[2][42]=indicatorsGroup[2][41]-indicatorsGroup[2][40]
   if indicatorsGroup[2][35]>1.4:
    statusGroup[2][0]=enabled           #Mark enabled compressor A/C V1 operating status flag
   else:
    statusGroup[2][0]=disabled          
   if indicatorsGroup[2][42]<moneyAcLimit:
    statusGroup[2][1]=enabled           #In case consumption A/C V1 exceeds moneyAcLimit 
   else:
    statusGroup[2][1]=disabled    
  statusBefore=checkSerial()
  if (statusArray10[9]==enabled and statusArray10[25]==disabled and statusBefore==enabled) or (statusArray10[9]==disabled and energyModuleData51[1]>0):
   comPzemCycler(energyModuleData51, latestNormal51, readCommand='j')
   for j in range (32,40):                         #next must be j-32 or start of range
    indicatorsGroup[3][j]=energyModuleData51[j-32] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[3][40]=int(indicatorsGroup[3][36]*kWpricel[4]) #Asign paying bill value
   indicatorsGroup[3][42]=indicatorsGroup[3][41]-indicatorsGroup[3][40]
   if indicatorsGroup[3][35]>1.4:
    statusGroup[3][0]=enabled           #Mark enabled compressor A/C V2 operating status flag
   else:
    statusGroup[3][0]=disabled          #Mark disabled compressor A/C V2 operating status flag   
   if indicatorsGroup[3][42]<moneyAcLimit:
    statusGroup[3][1]=enabled           #In case consumption A/C V2 exceeds moneyAcLimit 
   else:
    statusGroup[3][1]=disabled
#-------------END BLOCK

  #Block to read data from external sensors installed in arduino mega
  statusBefore=checkSerial()
  if statusArray10[30]==enabled and statusBefore==enabled:
   comPzemCycler(sensorsModuleData9, latestNormal9, readCommand='k')
   windSpeed=sensorsModuleData9[1] #Delete this as soon as test is finished
#=======================================================================
  serialComQuality=round(((float(cleanData)/float(serialTransactions))*100),2)
  indicatorsGroup[0][0]=executionsFinished #Keep count of complete program execution
  indicatorsGroup[0][1]=serialTransactions #Number of times serial queries executed in lines of while loop
  indicatorsGroup[0][2]=cleanData #Keep count of clean serial queries
  #Don't let this number get too high... it's stable and no need for that long
  if serialTransactions>=9000000:
   serialTransactions=0
   cleanData=0
   executionsFinished=0
  indicatorsGroup[0][6]=serialReboots #Keep counts of serial.open/serial.close
  indicatorsGroup[0][7]=serialComQuality #Serial communication performance
  indicatorsGroup[0][8]=outRangeFloats #Keep counts when out of range floats are received
  indicatorsGroup[0][9]=exceptionsDetected #Keep count of exceptions events detected
  indicatorsGroup[0][10]=serialExceptionsDetected
  indicatorsGroup[0][11]=windSpeed
  indicatorsGroup[0][12]=execTime
  indicatorsGroup[0][13]=0 #available-->incompleteByteArrayReception
  indicatorsGroup[0][14]=0 #available--->incompleteFloatsReception
  indicatorsGroup[1][24]= round(indicatorsGroup[1][3]-indicatorsGroup[1][11],1) #Delta I in mains 220V phase-N
  indicatorsGroup[2][24]= round(indicatorsGroup[2][3]-indicatorsGroup[2][11],1) #Delta I in apartment1 220V phase-N
  indicatorsGroup[3][24]= round(indicatorsGroup[3][3]-indicatorsGroup[3][11],1) #Delta I in apartment2 220V phase-N
  indicatorsGroup[4][24]= round(indicatorsGroup[4][3]-indicatorsGroup[4][11],1) #Delta I in smallBusiness 220V phase-N  
  statusGroup[0][0]=autoIncrementMark #This one will be used to keep track of sequential value from status array
  
  today = datetime.datetime.today() #Take a look for recent date and time value
  refDay=int(today.strftime("%d"))
  refHour=int(today.strftime("%H"))
  refMinute=int(today.strftime("%M"))
  
  
#Block conditioned to schedule events  
  schedule.run_pending()
  if flagEachHour01:
   for cycInd in range(1,len(kWpricel)):
    alter1Now[cycInd]=round(indicatorsGroup[cycInd][4]+indicatorsGroup[cycInd][12],1)
    if alter1Now[cycInd]<alter1Before[cycInd]:
     indicatorsGroup[cycInd][20]=round((alter1Before[cycInd]-alter1Now[cycInd]),1)
    else:
     indicatorsGroup[cycInd][20]=round((alter1Now[cycInd]-alter1Before[cycInd]),1)
    indicatorsGroup[cycInd][21]=int(indicatorsGroup[cycInd][20]*kWpricel[cycInd])
    alter1Before[cycInd]=alter1Now[cycInd]
   flagEachHour01=False
  if flagEachDay01:
   for cycInd in range(1,len(kWpricel)):
    alter2Now[cycInd]=round(indicatorsGroup[cycInd][4]+indicatorsGroup[cycInd][12],1)
    if alter2Now[cycInd]<alter2Before[cycInd]:
     indicatorsGroup[cycInd][22]=round(alter2Before[cycInd]-alter2Now[cycInd],1)
    else:
     indicatorsGroup[cycInd][22]=round(alter2Now[cycInd]-alter2Before[cycInd],1)
    indicatorsGroup[cycInd][23]=int(indicatorsGroup[cycInd][22]*kWpricel[cycInd])
    alter2Before[cycInd]=alter2Now[cycInd]
   flagEachDay01=False
  if flagEachEndDay01:
   f = open(today.strftime("/home/pi/pythons/Registros/%Y/%b/DatasetPerDay-%Y-%b.txt"), "a")    #Sacar el dia, el mes en letras y el año con la extensión ".txt"
   f.write(str(today.strftime("%Y-%b-%d,")))#Descriptivo fecha y hora   
   f.write(str(indicatorsGroup[1][4])+",") #Total Energía consumida PZEM Fase 1 color negro main feed
   f.write(str(indicatorsGroup[1][12])+",") #Total Energía consumida PZEM Fase 2 color rojo main feed
   f.write(str(indicatorsGroup[1][17])+",") #Valor monetario del consumo de energía para main feed
   f.write(str(11072016)+",")               #Elemento separador de secciones
   f.write(str(indicatorsGroup[2][4])+",") #Total Energía consumida PZEM Fase 1 color negro apartment1
   f.write(str(indicatorsGroup[2][12])+",") #Total Energía consumida PZEM Fase 2 color rojo apartment1
   f.write(str(indicatorsGroup[2][17])+",") #Valor monetario del consumo de energía para apartment1
   f.write(str(11072016)+",")               #Elemento separador de secciones
   f.write(str(indicatorsGroup[3][4])+",") #Total Energía consumida PZEM Fase 1 color negro apartment2
   f.write(str(indicatorsGroup[3][12])+",") #Total Energía consumida PZEM Fase 2 color rojo apartment2
   f.write(str(indicatorsGroup[3][17])+",") #Valor monetario del consumo de energía para apartment2
   f.write(str(11072016)+",")               #Elemento separador de secciones
   f.write(str(indicatorsGroup[4][4])+",") #Total Energía consumida PZEM Fase 1 color negro Seccion Mantenimiento   
   f.write(str(indicatorsGroup[4][12])+",") #Total Energía consumida PZEM Fase 2 color rojo Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][17])+",") #Valor monetario del consumo de energía para Seccion Mantenimiento   
   f.write(str(11072016)+"\n") #Guardar ultimo dato con salto de linea asegurando que es final de seccion
   f.close() #Cerrar archivo
   flagEachEndDay01=False
  if flagEach5Minute01: #Execution block for everything that belongs to each 5 minutes
   f = open(today.strftime("/home/pi/pythons/Registros/%Y/%b/%Y-%b-%d.txt"), "a")    #Sacar el dia, el mes en letras y el año con la extensión ".txt"
   f.write(str(today.strftime("%Y-%b-%d, %H:%M,")))#Descriptivo fecha y hora
   f.write(str(indicatorsGroup[1][1])+",") #Voltaje PZEM Fase 1 color negro main feed
   f.write(str(indicatorsGroup[1][2])+",") #Potencia instantána PZEM Fase 1 color negro main feed
   f.write(str(indicatorsGroup[1][3])+",") #Corriente instantánea PZEM Fase 1 color negro main feed
   f.write(str(indicatorsGroup[1][4])+",") #Total Energía consumida PZEM Fase 1 color negro main feed
   f.write(str(indicatorsGroup[1][5])+",") #Frecuencia instantánea PZEM Fase 1 color negro main feed
   f.write(str(indicatorsGroup[1][6])+",") #Factor de potencia PZEM Fase 1 color negro main feed
   f.write(str(indicatorsGroup[1][9])+",") #Voltaje PZEM Fase 2 color rojo main feed
   f.write(str(indicatorsGroup[1][10])+",") #Potencia instantána PZEM Fase 2 color rojo main feed
   f.write(str(indicatorsGroup[1][11])+",") #Corriente instantánea PZEM Fase 2 color rojo main feed
   f.write(str(indicatorsGroup[1][12])+",") #Total Energía consumida PZEM Fase 2 color rojo main feed
   f.write(str(indicatorsGroup[1][13])+",") #Frecuencia instantánea PZEM Fase 2 color rojo main feed
   f.write(str(indicatorsGroup[1][14])+",") #Factor de potencia PZEM Fase 2 color rojo main feed   
   f.write(str(indicatorsGroup[1][16])+",") #Sumatoria de energía consumida en las dos fases para main feed
   f.write(str(indicatorsGroup[1][17])+",") #Valor monetario del consumo de energía para main feed
   f.write(str(indicatorsGroup[1][24])+",") #Delta I in mains 220V phase-N   
   f.write(str(11072016)+",")               #Elemento separador de secciones
   f.write(str(indicatorsGroup[2][1])+",") #Voltaje PZEM Fase 1 color negro apartment1
   f.write(str(indicatorsGroup[2][2])+",") #Potencia instantána PZEM Fase 1 color negro apartment1
   f.write(str(indicatorsGroup[2][3])+",") #Corriente instantánea PZEM Fase 1 color negro apartment1
   f.write(str(indicatorsGroup[2][4])+",") #Total Energía consumida PZEM Fase 1 color negro apartment1
   f.write(str(indicatorsGroup[2][5])+",") #Frecuencia instantánea PZEM Fase 1 color negro apartment1
   f.write(str(indicatorsGroup[2][6])+",") #Factor de potencia PZEM Fase 1 color negro apartment1
   f.write(str(indicatorsGroup[2][9])+",") #Voltaje PZEM Fase 2 color rojo apartment1
   f.write(str(indicatorsGroup[2][10])+",") #Potencia instantána PZEM Fase 2 color rojo apartment1
   f.write(str(indicatorsGroup[2][11])+",") #Corriente instantánea PZEM Fase 2 color rojo apartment1
   f.write(str(indicatorsGroup[2][12])+",") #Total Energía consumida PZEM Fase 2 color rojo apartment1
   f.write(str(indicatorsGroup[2][13])+",") #Frecuencia instantánea PZEM Fase 2 color rojo apartment1
   f.write(str(indicatorsGroup[2][14])+",") #Factor de potencia PZEM Fase 2 color rojo apartment1   
   f.write(str(indicatorsGroup[2][16])+",") #Sumatoria de energía consumida en las dos fases para apartment1
   f.write(str(indicatorsGroup[2][17])+",") #Valor monetario del consumo de energía para apartment1
   f.write(str(indicatorsGroup[2][24])+",") #Delta I in apartment1 220V phase-N   
   f.write(str(11072016)+",")               #Elemento separador de secciones
   f.write(str(indicatorsGroup[3][1])+",") #Voltaje PZEM Fase 1 color negro apartment2
   f.write(str(indicatorsGroup[3][2])+",") #Potencia instantána PZEM Fase 1 color negro apartment2
   f.write(str(indicatorsGroup[3][3])+",") #Corriente instantánea PZEM Fase 1 color negro apartment2
   f.write(str(indicatorsGroup[3][4])+",") #Total Energía consumida PZEM Fase 1 color negro apartment2
   f.write(str(indicatorsGroup[3][5])+",") #Frecuencia instantánea PZEM Fase 1 color negro apartment2
   f.write(str(indicatorsGroup[3][6])+",") #Factor de potencia PZEM Fase 1 color negro apartment2
   f.write(str(indicatorsGroup[3][9])+",") #Voltaje PZEM Fase 2 color rojo apartment2
   f.write(str(indicatorsGroup[3][10])+",") #Potencia instantána PZEM Fase 2 color rojo apartment2
   f.write(str(indicatorsGroup[3][11])+",") #Corriente instantánea PZEM Fase 2 color rojo apartment2
   f.write(str(indicatorsGroup[3][12])+",") #Total Energía consumida PZEM Fase 2 color rojo apartment2
   f.write(str(indicatorsGroup[3][13])+",") #Frecuencia instantánea PZEM Fase 2 color rojo apartment2
   f.write(str(indicatorsGroup[3][14])+",") #Factor de potencia PZEM Fase 2 color rojo apartment2   
   f.write(str(indicatorsGroup[3][16])+",") #Sumatoria de energía consumida en las dos fases para apartment2
   f.write(str(indicatorsGroup[3][17])+",") #Valor monetario del consumo de energía para apartment2
   f.write(str(indicatorsGroup[3][24])+",") #Delta I in apartment2 220V phase-N   
   f.write(str(11072016)+",")               #Elemento separador de secciones
   f.write(str(indicatorsGroup[4][1])+",") #Voltaje PZEM Fase 1 color negro Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][2])+",") #Potencia instantána PZEM Fase 1 color negro Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][3])+",") #Corriente instantánea PZEM Fase 1 color negro Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][4])+",") #Total Energía consumida PZEM Fase 1 color negro Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][5])+",") #Frecuencia instantánea PZEM Fase 1 color negro Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][6])+",") #Factor de potencia PZEM Fase 1 color negro Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][9])+",") #Voltaje PZEM Fase 2 color rojo Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][10])+",") #Potencia instantána PZEM Fase 2 color rojo Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][11])+",") #Corriente instantánea PZEM Fase 2 color rojo Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][12])+",") #Total Energía consumida PZEM Fase 2 color rojo Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][13])+",") #Frecuencia instantánea PZEM Fase 2 color rojo Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][14])+",") #Factor de potencia PZEM Fase 2 color rojo Seccion Mantenimiento   
   f.write(str(indicatorsGroup[4][16])+",") #Sumatoria de energía consumida en las dos fases para Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][17])+",") #Valor monetario del consumo de energía para Seccion Mantenimiento
   f.write(str(indicatorsGroup[4][24])+",") #Delta I in Seccion Mantenimiento 220V phase-N
   f.write(str(11072016)+",")               #Elemento separador de secciones
   f.write(str(indicatorsGroup[2][35])+",") #Corriente instantánea PZEM A/C Apartamento 1
   f.write(str(indicatorsGroup[2][36])+",") #Total Energía consumida PZEM A/C Apartamento 1
   f.write(str(indicatorsGroup[2][41])+",") #Saldo de carga monteria A/C Apartamento 1
   f.write(str(indicatorsGroup[2][42])+",") #Saldo restante monetario A/C Apartamento 1 statusGroup[2][0]
   f.write(str(11072016)+",")               #Elemento separador de secciones
   f.write(str(indicatorsGroup[3][35])+",") #Corriente instantánea PZEM A/C Apartamento 2
   f.write(str(indicatorsGroup[3][36])+",") #Total Energía consumida PZEM A/C Apartamento 2
   f.write(str(indicatorsGroup[3][41])+",") #Saldo de carga monteria A/C Apartamento 2
   f.write(str(indicatorsGroup[3][42])+",") #Saldo restante monetario A/C Apartamento 2   
   f.write(str(11072016)+"\n") #Guardar ultimo dato con salto de linea asegurando que es final de seccion
   f.close() #Cerrar archivo
   flagEach5Minute01=False
  
  #VA PARA ASEGURAMIENTO DE DATOS EN SCHEDULE POR CADA MINUTO
  #KEEP THIS BLOCK OFF. In the meantime global reset will be made Manually  
  #Send if necesary during firs minute of month a general reset energy command
  if refDay==1 and refHour==0 and refMinute==0 and statusArray10[28]==disabled and countBackForReset==disabled:
   indicatorsGroup[1][25]=indicatorsGroup[1][16] #Ensuring for showing up last month energy consumption main feed
   indicatorsGroup[1][26]=indicatorsGroup[1][17] #Ensuring for showing up last month monetary energy consumption main feed
   indicatorsGroup[2][25]=indicatorsGroup[2][16] #Ensuring for showing up last month energy consumption apartment1
   indicatorsGroup[2][26]=indicatorsGroup[2][17] #Ensuring for showing up last month monetary energy consumption apartment1
   indicatorsGroup[3][25]=indicatorsGroup[3][16] #Ensuring for showing up last month energy consumption apartment2
   indicatorsGroup[3][26]=indicatorsGroup[3][17] #Ensuring for showing up last month monetary energy consumption apartment2
   indicatorsGroup[4][25]=indicatorsGroup[4][16] #Ensuring for showing up last month energy consumption seccion Mantenimiento
   indicatorsGroup[4][26]=indicatorsGroup[4][17] #Ensuring for showing up last month monetary energy consumption seccion Mantenimiento  
   for zeroFillerPzem in range(8):
    cmdAndStatusFromRasp1[zeroFillerPzem]=enabled #The idea is to mark each energy meter as requested to zero
   countBackForReset=enabled
  #clear if necesary during second minute of month a general reset energy command
  if refDay==1 and refHour==0 and refMinute==1 and statusArray10[28]==enabled:
   for zeroFillerPzem in range(10):
    cmdAndStatusFromRasp1[zeroFillerPzem]=disabled #Then after a minute clear flag order to zeroing
   countBackForReset=disabled
   
  if controlsGroup[0][0] == enabled:
    controlsGroup[0][0] = disabled
    for globalFlagReset in range(8): 
     cmdAndStatusFromRasp1[globalFlagReset]=enabled #Just a manual global reset using iteration VIA MQTT
  if controlsGroup[0][1] == enabled:
   #comArdu.write('m'.encode()) #Temp command to switch ON rain pump some minutes
   controlsGroup[0][1] = disabled
  if controlsGroup[0][2] == enabled:
   topicPath='ElectroMESH/general/status/01'
   mqttc.publish(topicPath, str(enabled))
   GPIO.cleanup()
   quit()

#MQTT publish launcher--------------------------------------
  for nodeCount in range(len(nodes)): #Whole publish MQTT
   for zoneCount in range(len(zones)):
    for indexCount in range(len(positionsBase)):
     topicPath=nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[0]+'/'+positionsBase[indexCount]
     #print(topicPath+'='+str(indicatorsGroup[zoneCount][indexCount]))  #This line is only for debugging purpose
     mqttc.publish(topicPath, str(indicatorsGroup[zoneCount][indexCount])) #Publish data loaded from sensor measurement
     topicPath=nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[1]+'/'+positionsBase[indexCount]
     #print(topicPath+'='+str(statusGroup[zoneCount][indexCount])) #This line is only for debugging purpose
     mqttc.publish(topicPath, str(statusGroup[zoneCount][indexCount])) #Publish random numbers
#-------------------------------------------------
  executionsFinished+=1
  execFinTime = time.time()
  execTime=round((execFinTime-execIniTime),2)
 except KeyboardInterrupt:
  print("Good bye!!!! Test finished manually")
  GPIO.cleanup()
  quit()
 except serial.SerialException as e:
  serialExceptionsDetected+=1
  topicPath=topicPath='ElectroMESH/general/status/03'
  mqttc.publish(topicPath, str(enabled))
  GPIO.cleanup()
  quit()
 except Exception as err:
  print(err)
  #print("Something wrong happended. Please trace code or ask to the author")
  exceptionsDetected+=1
  print(traceback.format_exc())
  #continue
  GPIO.cleanup()
  quit()
GPIO.cleanup()
print("Done")
