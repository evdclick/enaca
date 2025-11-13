#                    GNU GENERAL PUBLIC LICENSE
#                       Version 3, 29 June 2007
#
# Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
# Everyone is permitted to copy and distribute verbatim copies
# of this license document, but changing it is not allowed.
#=====================================================
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
kWprice=480 #kWh price value for energy consumption
kWpriceIntern=850 #kWh price value for energy consumption
myData = ['A']*8 #Init array of string to receive bytes struct packets
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

#Function to explore EVD structure in topicTide.py and execute massive subscription to controls topics
def on_connect(client, userdata, flags, rc):
 print ("on_connect() " + str(rc))
 for nodeCount in range(len(nodes)): #Get list of nodes
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
 print("\n on_message() topic: "+msg.topic+"\n payload: "+str(msg.payload)+"\n")
 topic = msg.topic
 try: #Firs check if topic exist
  payloadContent = int(msg.payload)
  topicsMap = topic.split('/')
  door = lookSearch(topicsMap[0], topicsMap[1], topicsMap[2], topicsMap[3]) #Search for topic location
  controlsGroup[int(door[1])][int(door[3])] = payloadContent
 except: #The idea is to receive control commands as a number
  print("It's not possible. Strings cannot be processed in payload. Only Numbers")

def writeBytesArray(bytePack, writeCommand):
 binaryList = bytearray(bytePack)
 comArdu.write(writeCommand.encode())
 comArdu.write(binaryList)
 comArdu.reset_input_buffer()
 comArdu.reset_output_buffer()

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
def readByteArrayInSerial():
 global serialReboots
 global serialTransactions
 global cleanData
 statusCleanData=True
 serialTransactions+=1
 numberStuffs=[0]*32
 comArdu.write('j'.encode()) #Keyword used to be sure about what is expected to receive energy data from specific pzem module
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
 return(numberStuffs)

def checkSerial():
  global serialReboots
  global serialTransactions
  global cleanData
  statusCleanData=True
  serialTransactions+=1
  internalComChecker=comArdu.write('k'.encode())
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

mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message

print("connecting to: "+host)
mqttc.connect(host, port, 60)
mqttc.loop_start()

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
                   list(indicatorList),]

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
cmdAndStatusFromRasp1[24]=disabled
statusArray10=[180]*32
statusArray10[28]=enabled
while True:
 try:
  #List of bytes and status commands to Arduino Mega in order to execute
  #specific instructions according to table specs in excel profile and
  #certain descriptions within lines in this code
  cmdAndStatusFromRasp1[31]=checkSumByteSender(cmdAndStatusFromRasp1) #Simple test to calculate checksum
  writeBytesArray(cmdAndStatusFromRasp1, writeCommand='r') #Then send byte array
  #------------------------
  execIniTime = time.time()
  statusBefore=checkSerial()
  if statusBefore!=enabled:
   comArdu.close()
   comArdu.open()
   serialReboots+=1
  statusArray10 = readByteArrayInSerial()
  if statusArray10[30]!=enabled:
   comArdu.close()
   comArdu.open()
   serialReboots+=1
#===========Retrieve data 8 float array PZEM function Definition =========
#Check if voltage is ON and there's not busy flag from Arduino Mega
  #Block to read PZEM modules from House
  autoIncrementMark=statusArray10[29]
  statusBefore=checkSerial()
  ##Remeber that serialEvent1 in Arduino has a condition to identify when to send float array and must be partially config
  if (statusArray10[0]==enabled and statusArray10[16]==disabled and statusBefore==enabled) or (statusArray10[0]==disabled and energyModuleData1[1]>0):
   comPzemCycler(energyModuleData1, latestNormal1, readCommand="a")
   for j in range (0,8):
    indicatorsGroup[1][j]=energyModuleData1[j] #indicators axes that belongs to general.... testing purpose
  statusBefore=checkSerial()
  if (statusArray10[1]==enabled and statusArray10[17]==disabled and statusBefore==enabled) or (statusArray10[1]==disabled and energyModuleData2[1]>0):
   comPzemCycler(energyModuleData2, latestNormal2, readCommand="b")
   for j in range (8,16):
    indicatorsGroup[1][j]=energyModuleData2[j-8] #indicators axes that belongs to general.... testing purpose
  #Block to read PZEM modules from Apartment1
  statusBefore=checkSerial()
  if (statusArray10[2]==enabled and statusArray10[18]==disabled and statusBefore==enabled) or (statusArray10[2]==disabled and energyModuleData3[1]>0):
   comPzemCycler(energyModuleData3, latestNormal3, readCommand="c")
   for j in range (0,8):
    indicatorsGroup[2][j]=energyModuleData3[j] #indicators axes that belongs to general.... testing purpose
  statusBefore=checkSerial()
  if (statusArray10[3]==enabled and statusArray10[19]==disabled and statusBefore==enabled) or (statusArray10[3]==disabled and energyModuleData4[1]>0):
   comPzemCycler(energyModuleData4, latestNormal4, readCommand="d")
   for j in range (8,16):
    indicatorsGroup[2][j]=energyModuleData4[j-8] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[2][16]=round(indicatorsGroup[2][4]+indicatorsGroup[2][12],1) #Asign sum of energy
   indicatorsGroup[2][17]=int(indicatorsGroup[2][16]*kWprice) #Asign paying bill value
   indicatorsGroup[2][18]=round(indicatorsGroup[2][2]+indicatorsGroup[2][10],1) #Asign sum of instant power
  #Block to read PZEM modules from Apartment2
  statusBefore=checkSerial()
  if (statusArray10[4]==enabled and statusArray10[20]==disabled and statusBefore==enabled) or (statusArray10[4]==disabled and energyModuleData5[1]>0):
   comPzemCycler(energyModuleData5, latestNormal5, readCommand="e")
   for j in range (0,8):
    indicatorsGroup[3][j]=energyModuleData5[j] #indicators axes that belongs to general.... testing purpose
  statusBefore=checkSerial()
  if (statusArray10[5]==enabled and statusArray10[21]==disabled and statusBefore==enabled) or (statusArray10[5]==disabled and energyModuleData6[1]>0):
   comPzemCycler(energyModuleData6, latestNormal6, readCommand="f")
   for j in range (8,16):
    indicatorsGroup[3][j]=energyModuleData6[j-8] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[3][16]=round(indicatorsGroup[3][4]+indicatorsGroup[3][12],1) #Asign sum of energy
   indicatorsGroup[3][17]=int(indicatorsGroup[3][16]*kWprice) #Asign paying bill value
   indicatorsGroup[3][18]=round(indicatorsGroup[3][2]+indicatorsGroup[3][10],1) #Asign sum of instant power
  #Block to read PZEM modules from Mini Local
  statusBefore=checkSerial()
  if (statusArray10[6]==enabled and statusArray10[22]==disabled and statusBefore==enabled) or (statusArray10[6]==disabled and energyModuleData7[1]>0):
   comPzemCycler(energyModuleData7, latestNormal7, readCommand="g")
   for j in range (0,8):
    indicatorsGroup[4][j]=energyModuleData7[j] #indicators axes that belongs to general.... testing purpose
  statusBefore=checkSerial()
  if (statusArray10[7]==enabled and statusArray10[23]==disabled and statusBefore==enabled) or (statusArray10[7]==disabled and energyModuleData8[1]>0):
   comPzemCycler(energyModuleData8, latestNormal8, readCommand="h")
   for j in range (8,16):
    indicatorsGroup[4][j]=energyModuleData8[j-8] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[4][16]=round(indicatorsGroup[4][4]+indicatorsGroup[4][12],1) #Asign sum of energy
   indicatorsGroup[4][17]=int(indicatorsGroup[4][16]*kWpriceIntern) #Asign paying bill value
   indicatorsGroup[4][18]=round(indicatorsGroup[4][2]+indicatorsGroup[4][10],1) #Asign sum of instant power

#------------Leave this block alone to retrieve PZEM A/C data testing purposes
  statusBefore=checkSerial()
  if (statusArray10[8]==enabled and statusArray10[24]==disabled and statusBefore==enabled) or (statusArray10[8]==disabled and energyModuleData50[1]>0):
   comPzemCycler(energyModuleData50, latestNormal50, readCommand="y")
   for j in range (32,40):
    indicatorsGroup[2][j]=energyModuleData50[j-32] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[2][40]=int(indicatorsGroup[2][36]*kWpriceIntern) #Asign paying bill value   
  statusBefore=checkSerial()
  if (statusArray10[9]==enabled and statusArray10[25]==disabled and statusBefore==enabled) or (statusArray10[9]==disabled and energyModuleData51[1]>0):
   comPzemCycler(energyModuleData51, latestNormal51, readCommand="z")
   for j in range (32,40):                         #next must be j-32 or start of range
    indicatorsGroup[3][j]=energyModuleData51[j-32] #indicators axes that belongs to general.... testing purpose
   indicatorsGroup[3][40]=int(indicatorsGroup[3][36]*kWpriceIntern) #Asign paying bill value   
#-------------END BLOCK

  #Block to read data from external sensors installed in arduino mega
  statusBefore=checkSerial()
  if statusArray10[30]==enabled and statusBefore==enabled:
   comPzemCycler(sensorsModuleData9, latestNormal9, readCommand="i")
   windSpeed=sensorsModuleData9[1] #Delete this as soon as test is finished
#=======================================================================
  serialComQuality=round(((float(cleanData)/float(serialTransactions))*100),2)
  indicatorsGroup[0][0]=executionsFinished #Keep count of complete program execution
  indicatorsGroup[0][1]=serialTransactions #Number of times serial queries executed in lines of while loop
  indicatorsGroup[0][2]=cleanData #Keep count of clean serial queries
  #Don't let this number get too high... it's stable and no need for that long
  if serialTransactions>=100000:
   serialTransactions=0
   cleanData=0
   executionsFinished=0
  indicatorsGroup[0][3]=0 #available --->basicSerialFailures #Keep counts of failures of basic serial int status query
  indicatorsGroup[0][4]=0 #available --->byteArrayFailures #Keep counts of failures of bytes array query
  indicatorsGroup[0][5]=0 #available --->stArrayComFailures #Detects communication failures when retrieving status array
  indicatorsGroup[0][6]=serialReboots #Keep counts of serial.open/serial.close
  indicatorsGroup[0][7]=serialComQuality #Serial communication performance
  indicatorsGroup[0][8]=outRangeFloats #Keep counts when out of range floats are received
  indicatorsGroup[0][9]=exceptionsDetected #Keep count of exceptions events detected
  indicatorsGroup[0][10]=serialExceptionsDetected
  indicatorsGroup[0][11]=windSpeed
  indicatorsGroup[0][12]=execTime
  indicatorsGroup[0][13]=0 #available-->incompleteByteArrayReception
  indicatorsGroup[0][14]=0 #available--->incompleteFloatsReception
  indicatorsGroup[1][17]= round(indicatorsGroup[1][3]-indicatorsGroup[1][11],1) #Temp purpose for Delta I in mains 220V phase-N
  statusGroup[0][0]=autoIncrementMark #This one will be used to keep track of sequential value from status array
  
  today = datetime.datetime.today() #Take a look for recent date and time value
  refDay=int(today.strftime("%d"))
  refHour=int(today.strftime("%H"))
  refMinute=int(today.strftime("%M"))
  #Send if necesary during firs minute of month a general reset energy command
  if refDay==1 and refHour==0 and refMinute==0 and statusArray10[28]==disabled:
   cmdAndStatusFromRasp1[24]=enabled
  #clear if necesary during second minute of month a general reset energy command
  if refDay==1 and refHour==0 and refMinute==1 and statusArray10[28]==enabled:
   cmdAndStatusFromRasp1[24]=disabled
  
  if controlsGroup[0][0] == enabled:
   comArdu.write('l'.encode())
   time.sleep(3)
   controlsGroup[0][0] = disabled
  if controlsGroup[0][1] == enabled:
   comArdu.write('m'.encode()) #Temp command to switch ON rain pump some minutes
   controlsGroup[0][1] = disabled

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
  print("Serial port is unplugged... check connection")
  serialExceptionsDetected+=1
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
