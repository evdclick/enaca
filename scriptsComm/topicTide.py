#                    GNU GENERAL PUBLIC LICENSE
#                       Version 3, 29 June 2007
#
# Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
# Everyone is permitted to copy and distribute verbatim copies
# of this license document, but changing it is not allowed.

nodes = ['ElectroMESH']
zones = ['general', 'house', 'apartment1', 'apartment2', 'smallBusiness']
category = ('indicators', 'status', 'controls')
positionsBase = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
'10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22',
'23', '24', '25', '26', '27', '28', '29', '30', '31','32', '33', '34', '35',
'36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48',
'49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61',
'62', '63' ]

def lookSearch(nodeLocate, zoneLocate, categoryLocate, indexLocate):
 locateVector = [-1, -1, -1, -1]
 if nodeLocate in nodes:
  print ("Node located")
  nodePosition = nodes.index(nodeLocate)
 if zoneLocate in zones:
  print ("Zone located")
  zonePosition = zones.index(zoneLocate)
 if categoryLocate in category:
  print ("Category located")
  categoryPosition = category.index(categoryLocate)
 if indexLocate in positionsBase:
  print ("Position located")
  indexPosition = positionsBase.index(indexLocate)
 locateVector = [nodePosition, zonePosition, categoryPosition, indexPosition]
 return locateVector
