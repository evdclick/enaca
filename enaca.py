
import datetime
import paho.mqtt.client as paho
import RPi.GPIO as GPIO
import serial
import sys
import struct
import time
from topicTide import *

#Rasperry inputs to be used as pulse counter for water flow
GPIO.setmode (GPIO.BCM)
GPIO.setup(22, GPIO.IN)
GPIO.setup(18, GPIO.IN)

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
mqttc = paho.client()
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

#32 bytes vector conversion to 8 floats
#This routine was used when workin with i2c comm
def get_float[data, index]:
 bytes = data[4.index:(index+1)*4]
 return struct.unpack('f', "".join(map(chr, bytes)))[0]

#Function for connecting with MQTT server
def on_connect(client, userdata, flags, rc):
 print ("on_connect() " + str(rc))
 for nodeCount in range(len(nodes)):
  for zoneCount in range(len(zones)):
   for indexCount in range(len(positionsBase)):
    topicRouteSubs = nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[2]+'/'+positionsBase[indexCount]
    print ("Subscribing to: "+ topicRouteSubs)
    mqttc.subscribe(topicRouteSubs)

def on_subscribe(client, userdata, mid, granted_qos):
 print("Successful subscribed")

def on_message(client, userdata, msg):
 print("\n on_message() topic: "+msg.topic+"\n payload: "+str(msg.payload)+"\n")
 topic = msg.topic
 try:
  payloadContent = int(msg.payload)
  topicsMap = topic.split('/')
  door = lookSearch(topicsMap[0], topicsMap[1], topicsMap[2], topicsMap[3])
 except:
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
GPIO.add_event_detect(18, GPIO.RISING, callback=counterPlus2, bouncetime=3)
GPIO.add_event_detect(22, GPIO.RISING, callback=counterPlus3, bouncetime=3)
