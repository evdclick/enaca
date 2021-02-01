#Enacaino-energy-testRasp V1.0
#Last modification 13-jan-2021
#This code applies for energy monitoring device PZEM-004 V3 with Arduino Mega 2560.
#Created by: William Jimenez

import serial
from time import sleep
import struct
import numpy as np



comArdu = serial.Serial("/dev/ttyS0", 9600, timeout=1) #Serial port UART in raspberry

myData = ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'A'] #Init array of string to receive bytes struct packets
f_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] #Init array of float values to unpack and convert to numpy array


while True:
 try:
  comArdu.write("A") #Keyword used to be sure about what is expected to receive energy data from specific pzem module
  for i in range (0, 8):
   myData[i] = comArdu.read(4)
   f_data[i] = struct.unpack('f', myData[i]) #Unpack to float
   tempTuple = f_data[i]
   f_data[i] = round(np.array(tempTuple, dtype=float), 2) #Convert the tupple back to numpy array
   print(f_data[i])
  print("============================")
  comArdu.reset_input_buffer() #Flush input buffer
  sleep(1) #Repeat every .5 seconds
 except KeyboardInterrupt():
  quit()
 except:
  continue
