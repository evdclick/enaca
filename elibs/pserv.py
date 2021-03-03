import numpy as np
import time
import datetime
import sys

class variablesCollector:
  def __init__(self):
    self.trendVolt = trendVolt = []
    self.trendCurrent = trendCurrent = []
    self.trendEnergy = trendEnergy = []
    self.trendPower = trendPower = []
    self.trendFreq = trendFreq = []
    self.trendPf = trendPf = []
    #Status array initialization
    self.energyzed = energyzed = []
    self.overCurrent = overCurrent = []
    self.overCompsumption = overCompsumption = []
    self.dateList = dateList = []
    self.firstCompIncidence = False
    self.lastCompIncidence = False

  def attach_energy(self, energy=[]):
    self.dateList.append(datetime.datetime.today()) #Actualizando variable de fecha y hora hoy
    refMinute=int(self.dateList[0].strftime("%M"))
    refSecs=int(self.dateList[0].strftime("%S"))
    self.trendVolt.append(energy[1])
    self.trendCurrent.append(energy[2])
    self.trendEnergy.append(energy[3])
    self.trendPower.append(energy[4])
    self.trendFreq.append(energy[5])
    self.trendPf.append(energy[6])
  def attach_status(self, stVar1=0, stVar2=0, stVar3=0):
    self.energyzed.append(stVar1)
    self.overCurrent.append(stVar2)
    self.overCompsumption.append(stVar3)

  def __str__(self):
    if len(self.trendVolt)==0:
      OutString="Feed the parcel man"
    else:
      OutString = "Aquí es '{0}'".format(self.trendVolt)
    return OutString
  def __del__(self):
    print('Destructor called, this object is out of memory')

#Busqueda reversible de un lapso de tiempo
"""
 for h in range(0, len(arraytemp)):
	mins=int(arraytemp[taks].strftime("%M"))
	secs=int(arraytemp[taks].strftime("%S"))
	if(mins==34 and secs<=10):
		print(mins, ":", secs)
		break
	taks+=(-1)
"""
