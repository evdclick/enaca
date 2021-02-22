#                    GNU GENERAL PUBLIC LICENSE
#                       Version 3, 29 June 2007
#
#Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
#Everyone is permitted to copy and distribute verbatim copies
#of this license document, but changing it is not allowed.

#Enacaino-energy-testRasp V1.0
#Last modification 13-jan-2021
#This code applies for energy monitoring device PZEM-004 V3 with Arduino Mega 2560.
#Created by: William Jimenez

import serial
from time import sleep
import struct
import numpy as np



comArdu = serial.Serial("/dev/ttyUSB0", 9600, timeout=4) #Serial port USB to TTL serial converter

myData = ['A']*8 #Init array of string to receive bytes struct packets
f_data = [0.0]*8 #Init array of float values to unpack and convert to numpy array
intData = [0]*32 #To receive array of bytes through serial port

def readByteArrayInSerial():
  comArdu.write("g") #Keyword used to be sure about what is expected to receive energy data from specific pzem module
  intData = comArdu.read(32)
  numberStuffs=[0]*32
  numColector=0
  for byteElement in intData:
   numberStuffs[numColector]=ord(byteElement)
   numColector+=1
  return(numberStuffs)

statusArray1 = []*32

while True:
 try:
  comArdu.write("a") #Keyword used to be sure about what is expected to receive energy data from specific pzem module
  for i in range (0, 8):
   myData[i] = comArdu.read(4)
   f_data[i] = struct.unpack('f', myData[i]) #Unpack to float
   tempTuple = f_data[i]
   f_data[i] = round(np.array(tempTuple, dtype=float), 2) #Convert the tupple back to numpy array
   print(f_data[i])
  print("============================")
  comArdu.reset_input_buffer() #Flush input buffer
  sleep(.5) #Repeat every .5 seconds
  statusArray1 = readByteArrayInSerial()
  print(statusArray1)
  sleep(.5) #Repeat every .5 seconds
 except KeyboardInterrupt:
  print("Manually finished... Good bye!")
  quit()
 except Exception as err:
  print("Problem is: ", err)
  continue
