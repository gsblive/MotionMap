__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

# import json
#import os
#import traceback
#import datetime

import indigo
import mmLib_Log
import mmLib_Low
import mmComm_Indigo
import mmObj_Motion
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
import random



######################################################
#
# mmMultisensor - Multi Sensor Device (such as Fibaro FGMS-0001)
#
######################################################
class mmMultisensor(object):

	######################################################################################
	#
	# Internally used routines for this object (mmMultisensor)
	#
	######################################################################################

	def makeDeviceSubmodelDictionary(self):

		for newDev in indigo.devices.iter("indigo.zwave, indigo.sensor"):

			try:
				subModelDevs = mmLib_Low.SubmodelDeviceDict[newDev.address]
			except:
				mmLib_Low.SubmodelDeviceDict[newDev.address] = {}
				subModelDevs = mmLib_Low.SubmodelDeviceDict[newDev.address]

			subModelDevs[str(newDev.name)] = newDev

		return


	######################################################################################
	#
	#  __init__ mmMultisensor
	#
	######################################################################################

	def __init__(self, theDeviceParameters):

		supportMatrixDict = {	 u'Multi Sensor 6 (ZW100) Humidity': mmMultisensorHumidity,
								 u'Multi Sensor 6 (ZW100) Tamper': mmMultisensorVibration,
								 u'Motion Sensor (FGMS001) Motion Sensor': mmMultisensorMotion,
								 u'Multi Sensor 6 (ZW100) Motion Sensor': mmMultisensorMotion,
								 u'Multi Sensor 6 (ZW100) Luminance': mmMultisensorLuminance,
								 u'Multi Sensor 6 (ZW100) Temperature': mmMultisensorTemperature,
								 u'Motion Sensor (FGMS001) Temperature': mmMultisensorTemperature,
								 u'Motion Sensor (FGMS001) Tilt/Tamper': mmMultisensorVibration,
								 u'Motion Sensor (FGMS001) Luminance': mmMultisensorLuminance,
								 u'Multi Sensor 6 (ZW100) Ultraviolet': mmMultisensorUltraviolet}

		self.initResult = 0
		mmLib_Log.logVerbose("Adding multisensor with parameters: " + str(theDeviceParameters))
		self.deviceName = theDeviceParameters["deviceName"]
		self.theIndigoDevice = indigo.devices[self.deviceName]
		self.theIndigoAddress = self.theIndigoDevice.address
		self.debugDevice = 0

		try:
			if theDeviceParameters["debugDeviceMode"] != "noDebug":
				self.debugDevice = 1
		except:
			mmLib_Log.logVerbose("debugDeviceMode field is undefined in config file for " + self.deviceName + " , " + self.theIndigoDevice.subModel)
			theDeviceParameters["debugDeviceMode"] = "noDebug"


		# Now as a courtesy, add all the submodels

		if mmLib_Low.SubmodelDeviceDict == {}:
			self.makeDeviceSubmodelDictionary()
			#mmLib_Log.logForce( str(mmLib_Low.SubmodelDeviceDict))

		subDeviceParameters = theDeviceParameters
		subModelDevs = mmLib_Low.SubmodelDeviceDict[self.theIndigoAddress]

		for newDevName, newDev in subModelDevs.iteritems():
			try:
				theDeviceDescriptor = str(newDev.model) + " " + str(newDev.subModel)
				theInitProc = supportMatrixDict[theDeviceDescriptor]
			except:
				mmLib_Log.logForce("==== WARNING ==== Handler not found for " + newDevName + ". Descriptor: " + theDeviceDescriptor)
				return

			subDeviceParameters["deviceName"] = newDevName
			subDeviceParameters["deviceType"] = newDev.subModel

			if self.debugDevice != 0: mmLib_Log.logForce("Initializing: " + str(newDevName))

			theInitProc(subDeviceParameters)




	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################



######################################################################################
#
# Device Subclasses Such as the motion Sensor, Vibration Sensor, temperature sensor and the Luminance Sensor for the fibaro above
#
######################################################################################


######################################################
#
# mmMultisensorMotion - SubModel of multisensorDevice above
#
######################################################
class mmMultisensorMotion(mmObj_Motion.mmMotion):

	#
	# __init__
	#
	def __init__(self, theDeviceParameters):

		super(mmMultisensorMotion, self).__init__(theDeviceParameters)  # Initialize Base Class

		s = str(self.deviceName + "Battery.%")
		self.batteryLevelVar = s.replace(' ', '.')

		self.deviceName = theDeviceParameters["deviceName"]
		self.theIndigoDevice = indigo.devices[self.deviceName]
		self.theIndigoAddress = self.theIndigoDevice.address


		# take this time to update the battery level
		try:
			mmLib_Low.setIndigoVariable(self.batteryLevelVar, str(self.theIndigoDevice.states["batteryLevel"]))
		except:
			mmLib_Log.logForce(" ===== Initializing mmMultisensorMotion: " + self.deviceName + " no batteryLevel State")

		mmLib_Low.registerDelayedAction(	{'theFunction': self.OnceADayTimer,
											 'timeDeltaSeconds': random.randint(60*60*10, 60*60*14),
											 'theDevice': self.deviceName,
											 'timerMessage': "OnceADayTimer"})

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################

	#
	# OnceADayTimer - Check battery level etc
	#
	def OnceADayTimer(self, parameters):

		# take this time to update the battery level
		mmLib_Low.setIndigoVariable(self.batteryLevelVar, str(self.theIndigoDevice.states["batteryLevel"]))

		return random.randint(60*60*10, 60*60*14)	# Between 10 and 14 hours is fine


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmMultisensorMotion: " + self.deviceName + " with Value of: " + str(diff))
			#mmLib_Log.logForce("Parsing Update for mmMultisensorMotion: " + self.deviceName + " with Value of: " + str(newDev))

		super(mmMultisensorMotion, self).deviceUpdated(origDev, newDev)  # the Motion class to do motion processing

		return 1	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorMotion: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorMotion: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	#
	#  Sends a Status Request
	#		Does not honor the unresponsive variable
	#
	def sendStatusRequest(self, theCommandParameters):
		mmLib_Log.logVerbose("Requesting Status for " + self.deviceName)
		indigo.iodevice.statusRequest(self.theIndigoDevice.id)

		return(0)


	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		mmLib_Log.logForce("### Update Event for " + newDev.name + " should have been processed by parseUpdate()")

		return(0)


	#
	# devStatus
	#
	def devStatus(self, theCommandParameters):

		# Do any specialized status info here

		super(mmMultisensorMotion, self).devStatus(theCommandParameters)

		return(0)

	#
	# checkBattery - report the status of this device's battery
	# 	FORCE it to the log
	#	returns 0 if good battery, nonzero if bad
	#
	def checkBattery(self, theCommandParameters):

		currentBatteryVal = int(mmLib_Low.getIndigoVariable(self.batteryLevelVar, "101"))


		if theCommandParameters["ReportType"] == "Terse":
			if currentBatteryVal > 100:
				addString = ""				# Its not setup yet
			elif currentBatteryVal > 50:
				addString = ""
			else:
				addString = self.deviceName + " battery level is at " + str(currentBatteryVal) + "%"
				mmLib_Log.logReportLine(addString)
		else:
			addString = self.deviceName + " battery level is at " + str(currentBatteryVal) + "%"
			mmLib_Log.logReportLine(addString)

		return(addString)


######################################################
#
# mmMultisensorVibration - SubModel of multisensorDevice above
#
######################################################
class mmMultisensorVibration(mmComm_Indigo.mmIndigo):

	#
	# __init__
	#
	def __init__(self, theDeviceParameters):


		super(mmMultisensorVibration, self).__init__(theDeviceParameters)  # Initialize Base Class

		#mmLib_Log.logForce("### Initializing Vibration sensor " + self.deviceName )

		if self.theIndigoDevice.onState == True: indigo.device.turnOff(self.devIndigoID)


	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################



	#
	# offTimer - Reset Vibration sense
	#
	def offTimer(self, parameters):

			mmLib_Log.logForce("Device: " + self.deviceName + " Resetting onstate to 0 ")
			indigo.device.turnOff(self.devIndigoID)
			return 0


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmMultisensorVibration: " + self.deviceName + " with Value of: " + str(diff))

		if self.theIndigoDevice.onState == True:
			mmLib_Log.logForce("Device: " + self.deviceName + " is vibrating. Setting callback timer to reset onstate: ")
			mmLib_Low.registerDelayedAction(	{'theFunction': self.offTimer,
												 'timeDeltaSeconds': 30,
												 'theDevice': self.deviceName,
												 'timerMessage': "offTimer"})

		return 1	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorVibration: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorVibration: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		mmLib_Log.logForce("### Update Event for " + newDev.name + " should have been processed by parseUpdate()")

		return(0)

	#
	# devStatus
	#
	def devStatus(self, theCommandParameters):

		# Do any specialized status info here

		if self.theIndigoDevice.onState == True:
			mmLib_Log.logReportLine(self.deviceName + " is vibrating")
		else:
			mmLib_Log.logReportLine(self.deviceName + " is not vibrating")

		return(0)

######################################################
#
# mmMultisensorLuminance - SubModel of multisensorDevice above
#
######################################################
class mmMultisensorLuminance(mmComm_Indigo.mmIndigo):

	#
	# __init__
	#
	def __init__(self, theDeviceParameters):

		super(mmMultisensorLuminance, self).__init__(theDeviceParameters)  # Initialize Base Class

		s = str(self.deviceName + ".Lux")
		self.luxLevelVar = s.replace(' ', '.')

		# take this time to update the Lux level
		mmLib_Low.setIndigoVariable(self.luxLevelVar, str(self.theIndigoDevice.sensorValue))


	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmMultisensorLuminance: " + self.deviceName + " with Value of: " + str(diff))

		if origDev.sensorValue != newDev.sensorValue:
			# take this time to update the Lux level
			mmLib_Low.setIndigoVariable(self.luxLevelVar, str(newDev.sensorValue))
			mmLib_Log.logForce(newDev.name + ": Value = " + str(newDev.sensorValue) + " Lux")
		else:
			mmLib_Log.logDebug(newDev.name + ": Received duplicate value: Lux = " + str(newDev.sensorValue))
		return 1	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorLuminance: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorLuminance: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		mmLib_Log.logForce("### Update Event for " + newDev.name + " should have been processed by parseUpdate()")

		return(0)

	# devStatus
	#
	def devStatus(self, theCommandParameters):

		# Do any specialized status info here

		mmLib_Log.logReportLine(self.deviceName + " LUX is: " + mmLib_Low.getIndigoVariable(self.luxLevelVar, "0"))


		return(0)

######################################################
#
# mmMultisensorHumidity - SubModel of multisensorDevice above
#
######################################################
class mmMultisensorHumidity(mmComm_Indigo.mmIndigo):

	#
	# __init__
	#
	def __init__(self, theDeviceParameters):

		super(mmMultisensorHumidity, self).__init__(theDeviceParameters)  # Initialize Base Class

		s = str(self.deviceName + ".Humidity")
		self.humidityLevelVar = s.replace(' ', '.')

		# take this time to update the Humidity level
		mmLib_Low.setIndigoVariable(self.humidityLevelVar, str(self.theIndigoDevice.sensorValue))


	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmMultisensorHumidity: " + self.deviceName + " with Value of: " + str(diff))

		if origDev.sensorValue != newDev.sensorValue:
			# take this time to update the Humidity level
			mmLib_Low.setIndigoVariable(self.humidityLevelVar, str(newDev.sensorValue))
			mmLib_Log.logForce(newDev.name + ": Value = " + str(newDev.sensorValue) + " % Relative Humidity")
		else:
			mmLib_Log.logDebug(newDev.name + ": Received duplicate value: Humidity = " + str(newDev.sensorValue))
		return 1	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorHumidity: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorHumidity: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		mmLib_Log.logForce("### Update Event for " + newDev.name + " should have been processed by parseUpdate()")

		return(0)

	# devStatus
	#
	def devStatus(self, theCommandParameters):

		# Do any specialized status info here

		mmLib_Log.logReportLine(self.deviceName + " Humidity is: " + mmLib_Low.getIndigoVariable(self.humidityLevelVar, "0"))

		return(0)

######################################################
#
# mmMultisensorUltraviolet - SubModel of multisensorDevice above
#
######################################################
class mmMultisensorUltraviolet(mmComm_Indigo.mmIndigo):

	#
	# __init__
	#
	def __init__(self, theDeviceParameters):

		super(mmMultisensorUltraviolet, self).__init__(theDeviceParameters)  # Initialize Base Class

		s = str(self.deviceName + ".UV")
		self.uvLevelVar = s.replace(' ', '.')

		# take this time to update the UV level
		mmLib_Low.setIndigoVariable(self.uvLevelVar, str(self.theIndigoDevice.sensorValue))


	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmMultisensorUV: " + self.deviceName + " with Value of: " + str(diff))

		if origDev.sensorValue != newDev.sensorValue:
			# take this time to update the UV level
			mmLib_Low.setIndigoVariable(self.uvLevelVar, str(newDev.sensorValue))
			mmLib_Log.logForce(newDev.name + ": Value = " + str(newDev.sensorValue) + " mW\/cm^2")
		else:
			mmLib_Log.logDebug(newDev.name + ": Received duplicate value: mW\/cm^2 = " + str(newDev.sensorValue))
		return 1	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorUltraviolet: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorUltraviolet: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		mmLib_Log.logForce("### Update Event for " + newDev.name + " should have been processed by parseUpdate()")

		return(0)

	# devStatus
	#
	def devStatus(self, theCommandParameters):

		# Do any specialized status info here

		mmLib_Log.logReportLine(self.deviceName + " UVLevel is: " + mmLib_Low.getIndigoVariable(self.uvLevelVar, "0"))

		return(0)

######################################################
#
# mmMultisensorTemperature - SubModel of multisensorDevice above
#
######################################################
class mmMultisensorTemperature(mmComm_Indigo.mmIndigo):

	#
	# __init__
	#
	def __init__(self, theDeviceParameters):

		super(mmMultisensorTemperature, self).__init__(theDeviceParameters)  # Initialize Base Class

		if "ZW100" in self.theIndigoDevice.model:
			if self.debugDevice: mmLib_Log.logForce("Aeon Detected: " + self.deviceName)
			self.TempDefaultFormat = 'F'
		else:
			self.TempDefaultFormat = 'C'

		s = str(self.deviceName + ".F")
		self.tempFLevelVar = s.replace(' ', '.')

		self.setTemperature()

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	#
	# setTemperature - set the indigo related temperature variable to the device temperature
	#
	def setTemperature(self):

		if self.TempDefaultFormat == 'C':
			theDegrees = (float(self.theIndigoDevice.sensorValue) * 1.8) + 32.0
		else:
			theDegrees = self.theIndigoDevice.sensorValue

		mmLib_Low.setIndigoVariable(self.tempFLevelVar, str(theDegrees) + 'F')
		return(theDegrees)

	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmMultisensorTemperature: " + self.deviceName + " with Value of: " + str(diff))

		theTempF = self.setTemperature()

		if origDev.sensorValue != newDev.sensorValue:
			mmLib_Log.logForce(newDev.name + ": Value = " + str(theTempF) + " Degrees F")
		else:
			mmLib_Log.logDebug(newDev.name + ": Received duplicate value: Temperature = " + str(theTempF))

		return 1	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorTemperature: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorTemperature: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1	#0 means did not process

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		mmLib_Log.logForce("### Update Event for " + newDev.name + " should have been processed by parseUpdate()")

		return(0)


	# devStatus
	#
	def devStatus(self, theCommandParameters):

		# Do any specialized status info here

		mmLib_Log.logReportLine(self.deviceName + " Temperature (F) is: " + mmLib_Low.getIndigoVariable(self.tempFLevelVar, "0"))

		return(0)
