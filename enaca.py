#run enaca.py as this example:
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
sys.path.append('./scriptsComm') #Relative path that applies to raspberry
from topicTide import *

#Rasperry inputs to be used as pulse counter for water flow
GPIO.setmode (GPIO.BCM)
GPIO.setup(18, GPIO.IN)
GPIO.setup(23, GPIO.IN)
GPIO.setup(24, GPIO.IN)
GPIO.setup(25, GPIO.IN)

#Variables for True and False to ensure communications
active = 150
inactive = 180

#Initial lists to calculate consumption per day
litresStartingDay = [0, 0, 0 ,0]
litresEndDay = [0, 0, 0, 0]
energyStartinDay = [0, 0, 0, 0]
energyEndDay = [0, 0, 0, 0]

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

#In case of using i2c display
initDispT = 1 #Time for displayin message

#References to reset counters
refSave = 0
refResetDay = 0
refResetHour = 0
refResetMin = 0

#Variables to study counter overflow
fs1 = 0.00
fs2 = 0.00
fs3 = 0.00
fs4 = 0.00

#Final variables for liter conversion to CSV file
litersHouse = 0.00
litersApt1 = 0.00
litersApt2 = 0.00
litersTot = 0.00

#Variables for paying values according to each section
valuePayHouse = 0.00
valuePayApt1 = 0.00
valuePayApt2 = 0.00
#Variables for the last month to pay
lastPayValueHouse = 0.00
lastPayValueApt1 = 0.00
lastPayValueApt2 = 0.00

#Variable for saving last energy paying value in apt1
lastEnergyPayApt1 = 0.00

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
 for nodeCount in range(len(nodes)):
  for zoneCount in range(len(zones)):
   for indexCount in range(len(positionsBase)):
    topicRouteSubs = nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[2]+'/'+positionsBase[indexCount]
    #print ("Subscribing to: "+ topicRouteSubs) #Uncomment this if you need to see what happend with each control topic before subscription
    mqttc.subscribe(topicRouteSubs)
 print("Subscription completed for all topics in EVD structure")

def on_subscribe(client, userdata, mid, granted_qos):
 pass #Just in this case to to nothing if subscribe event is receive from the broker
 #print("Successful subscribed") #If you need confirmation for each subscribed topic in console uncomment this line

def on_message(client, userdata, msg): #This function is about on-screen events after receiving controls topics
 print("\n on_message() topic: "+msg.topic+"\n payload: "+str(msg.payload)+"\n")
 topic = msg.topic
 try: #Firs check if topic exist
  payloadContent = int(msg.payload)
  topicsMap = topic.split('/')
  door = lookSearch(topicsMap[0], topicsMap[1], topicsMap[2], topicsMap[3])
  controlsGroup[int(door[1])][int(door[3])] = payloadContent
 except: #The idea is to receive control commands as a number
  print("It's not possible. Strings cannot be processed in payload. Only Numbers")

#Rising events for flow sensor totalizer input #4
def counterPlus(channel):
 global totalizer
 if GPIO.input(channel)>0.5: #Get pulse
  controlsGroup[0][4]+=1
  totalizer = controlsGroup [0][4]
  statusGroup = [0][2] = 1
 else:
  controlsGroup[0][4]+=0
  totalizer = controlsGroup [0][4]

def counterPlus1(channel):
 global acumApt1
 if GPIO.input(channel)>0.5: #Get pulse
  controlsGroup[2][11]+=1
  acumApt1 = controlsGroup [2][11]
  statusGroup = [2][4] = 1
 else:
  controlsGroup[2][11]=0
  totalizer = controlsGroup [2][11]

def counterPlus2(channel):
 global acumApt2
 if GPIO.input(channel)>0.5: #Get pulse
  controlsGroup[3][7]+=1
  acumApt2 = controlsGroup [3][7]
  statusGroup = [3][3] = 1
 else:
  controlsGroup[3][7]=0
  totalizer = controlsGroup [3][7]

def counterPlus3(channel):
 global acumHouse
 if GPIO.input(channel)>0.5: #Get pulse
  controlsGroup[1][9]+=1
  acumApt2 = controlsGroup [1][9]
  statusGroup = [1][5] = 1
 else:
  controlsGroup[1][9]=0
  totalizer = controlsGroup [1][9]

#Interrupt routines to count rising edges in digital inputs
GPIO.add_event_detect(18, GPIO.RISING, callback=counterPlus, bouncetime=3)
GPIO.add_event_detect(23, GPIO.RISING, callback=counterPlus1, bouncetime=3)
GPIO.add_event_detect(24, GPIO.RISING, callback=counterPlus2, bouncetime=3)
GPIO.add_event_detect(25, GPIO.RISING, callback=counterPlus3, bouncetime=3)

kwhrApt1 = 0.0
lastKwhrApt1 = 0.0
lastAmpApt1 = 0.0

mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message

print("connecting to: "+host)
mqttc.connect(host, port, 60)
mqttc.loop_start()

indicatorList = []
statusList = []
controsList = []

for x in range(len(positionsBase)):
 indicatorList.append(0)
 statusList.append(0)
 controsList.append(0)

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

controlsGroup = [list(controsList),
                 list(controsList),
                 list(controsList),
                 list(controsList),
                 list(controsList)]


comArdu = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=2)
counter=0
commfails = 0
wrongData = 0
myData = ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'A'] #Init array of string to receive bytes struct packets
f_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] #Init array of float values to unpack and convert to numpy array
latestNormal1 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
energyModuleData1 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
latestNormal2 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
energyModuleData2 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

#Function to upgrade energy module information or some other array of 8 float elements
def comPzemCycler(ofversion, bkpversion, readCommand):
 comArdu.write(readCommand) #Keyword used to be sure about what is expected to receive energy data from specific pzem module
 for i in range (0, 8):
  myData[i] = comArdu.read(4)
  ofversion[i] = struct.unpack('f', myData[i]) #Unpack to float
  tempTuple = ofversion[i]
  ofversion[i] = round(np.array(tempTuple, dtype=float), 2) #Convert the tupple back to numpy array
  if (ofversion[i]<-3 or ofversion[i]>10000): #Just to check if the number is extremely out of range
   ofversion[i]=bkpversion[i]
  elif (f_data[i]==-3):
   continue
  else:
   bkpversion[i]=ofversion[i]
 if (ofversion[1]==-3):
  ofversion[1]=0
  ofversion[2]=0
  ofversion[3]=0
  ofversion[5]=0
  ofversion[6]=0
  ofversion[4]=bkpversion[4]
 return(ofversion, bkpversion, readCommand)

#Here the loop start
while True:
 sleep(.1) #Repeat every 1 second
 try:
  sleep(.1)
  comPzemCycler(energyModuleData1, latestNormal1, readCommand="A")
  for j in range (0,8):
   indicatorsGroup[0][j]=energyModuleData1[j] #indicators axes that belongs to general.... testing purpose
  comPzemCycler(energyModuleData2, latestNormal2, readCommand="A")
  for j in range (0,8):
   indicatorsGroup[1][j]=energyModuleData2[j] #indicators axes that belongs to general.... testing purpose
#  print("============================")
  counter+=1
  comArdu.reset_input_buffer()
  comArdu.reset_output_buffer()
  indicatorsGroup[0][8]=counter
  for nodeCount in range(len(nodes)):
   for zoneCount in range(len(zones)):
    for indexCount in range(len(positionsBase)):
     topicPath=nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[0]+'/'+positionsBase[indexCount]
     #print(topicPath+'='+str(indicatorsGroup[zoneCount][indexCount]))  #This line is only for debugging purpose
     mqttc.publish(topicPath, str(indicatorsGroup[zoneCount][indexCount])) #Publish data loaded from sensor measurement
     topicPath=nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[1]+'/'+positionsBase[indexCount]
     #print(topicPath+'='+str(statusGroup[zoneCount][indexCount])) #This line is only for debugging purpose
     mqttc.publish(topicPath, str(statusGroup[zoneCount][indexCount]*random.randint(1,15))) #Publish random numbers
 except KeyboardInterrupt:
  print("Good bye!!!! Test finished manually")
  GPIO.cleanup()
  quit()
 except Exception as err:
  print(err)
  print("Something wrong happended. Please trace code or ask to the author")
  comArdu.close()
  sleep(.5)
  comArdu.open()
  commfails+=1
  indicatorsGroup[0][9]=commfails
  continue
GPIO.cleanup()
print("Done")
