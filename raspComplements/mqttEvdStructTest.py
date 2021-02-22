#                    GNU GENERAL PUBLIC LICENSE
#                       Version 3, 29 June 2007
#
# Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
# Everyone is permitted to copy and distribute verbatim copies
# of this license document, but changing it is not allowed.

#sys.path.append('.\scriptsComm') #Relative path in case of windows
import datetime
import random #This one is to generate random numbers that will be published in created topics
import paho.mqtt.client as paho #To connect to mqtt broker
import sys  #To help to identify testing Library created to publish using EVD structure
import time #To help in delays if needed
sys.path.append('./scriptsComm') #Relative path in case of raspberry
from topicTide import *

mqttc = paho.Client()
host = "192.168.15.102" #Server IP can be selected as you desire
door = []
port = 1883 #The one that mosquitto uses

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

mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message

time.sleep(.1)
print("connecting to: "+host)
mqttc.connect(host, port, 60)
mqttc.loop_start()

#This is the code block created to initialize EVD structure before subs and pub
#in mqtt broker
indicatorsList = []
statusList = []
controlsList = []
for x in range(len(positionsBase)):
 indicatorsList.append(8) #initialize with any int value as prefered
 statusList.append(8)
 controlsList.append(0)
indicatorsGroup = [list(indicatorsList),
                   list(indicatorsList),
                   list(indicatorsList),
                   list(indicatorsList),
                   list(indicatorsList),]
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

time.sleep(.5)
while True:
 try:
  for nodeCount in range(len(nodes)):
   for zoneCount in range(len(zones)):
    for indexCount in range(len(positionsBase)):
     topicPath=nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[0]+'/'+positionsBase[indexCount]
     time.sleep(.005)
#     print(topicPath+'='+str(indicatorsGroup[zoneCount][indexCount]))  #This line is only for debugging purpose
     mqttc.publish(topicPath, str(indicatorsGroup[zoneCount][indexCount]*random.randint(1,15))) #Publish random numbers
     topicPath=nodes[nodeCount]+'/'+zones[zoneCount]+'/'+category[1]+'/'+positionsBase[indexCount]
     time.sleep(.005)
#     print(topicPath+'='+str(statusGroup[zoneCount][indexCount])) #This line is only for debugging purpose
     mqttc.publish(topicPath, str(statusGroup[zoneCount][indexCount]*random.randint(1,15))) #Publish random numbers
  time.sleep(1)
 except KeyboardInterrupt:
  print("Good bye!!!! Test finished manually")
  quit()
 except:
  print("Something wrong happended. Please trace code or ask to the author")
  quit()


print("Done")
