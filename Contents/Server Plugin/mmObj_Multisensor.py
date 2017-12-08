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

######################################################
#
# mmMultisensor - Multi Sensor Device (such as Fibaro FGMS-0001)
#
######################################################
class mmMultisensor(object):
	#
	# __init__
	#
	def __init__(self, theDeviceParameters):

		self.initResult = 0
		mmLib_Log.logVerbose("Adding multisensor with parameters: " + str(theDeviceParameters))
		self.deviceName = theDeviceParameters["deviceName"]
		self.theIndigoDevice = indigo.devices[self.deviceName]
		self.theIndigoAddress = self.theIndigoDevice.address

		if "FGMS001" in self.theIndigoDevice.model:
			# Add the sub components by itterating device address
			for newDev in indigo.devices.iter("indigo.zwave"):
				if newDev.address == self.theIndigoAddress:
					if newDev.subModel == "Motion Sensor":
						mmMultisensorMotion(theDeviceParameters)
					elif newDev.subModel == "Tilt/Tamper":
						mmMultisensorVibration({'deviceType':'VibrationSensor','deviceName':newDev.name})
					elif newDev.subModel == "Luminance":
						mmMultisensorLuminance({'deviceType':'LuminanceSensor','deviceName':newDev.name})
					elif newDev.subModel == "Temperature":
						mmMultisensorTemperature({'deviceType':'TemperatureSensor','deviceName':newDev.name})
					else:
						mmLib_Log.logForce("#### " + self.deviceName + " Unsupported subModel: " + str(newDev.subModel))

		else:
			mmLib_Log.logForce("#### " + self.deviceName + ": Unknown multifunction device type.")


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
# Device Subclasses
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

		# take this time to update the battery level
		mmLib_Low.setIndigoVariable(self.batteryLevelVar, str(self.theIndigoDevice.states["batteryLevel"]))

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
			mmLib_Log.logForce("Parsing Update for mmMultisensorMotion: " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorMotion: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorMotion: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

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

		# take this time to update the battery level
		mmLib_Low.setIndigoVariable(self.batteryLevelVar, str(newDev.states["batteryLevel"]))

		super(mmMultisensorMotion, self).deviceUpdated(origDev, newDev)  # the Motion class to do motion processing

		return(0)

	#
	# checkBattery - report the status of this device's battery
	# 	FORCE it to the log
	#	returns 0 if good battery, nonzero if bad
	#
	def checkBattery(self):

		currentBatteryVal = int(mmLib_Low.getIndigoVariable(self.batteryLevelVar, "101"))

		if currentBatteryVal > 100:
			addString = ""				# Its not setup yet
		elif currentBatteryVal > 10:
			addString = ""
		else:
			addString = self.deviceName + " battery level is at " + str(currentBatteryVal) + "%\n"
			mmLib_Log.logForce(addString)

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

		if self.theIndigoDevice.onState == True: indigo.device.turnOff(self.devIndigoID)
		mmLib_Low.mmRegisterForTimer(self.deviceTime, 60)		# give us a kick every minute

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
	# deviceTime - do device housekeeping... this should happen once a minute
	#
	def deviceTime(self):

		st = time.strptime(str(self.theIndigoDevice.lastChanged), "%Y-%m-%d %H:%M:%S")
		lastUpdateTimeSeconds = time.mktime(st)
		timeLapsedSeconds = int(time.mktime(time.localtime()) - lastUpdateTimeSeconds)

		mmLib_Log.logDebug("====Running Vibration Sensor Device Time for " + self.deviceName)
		if self.theIndigoDevice.onState and timeLapsedSeconds > 30:
			mmLib_Log.logForce("Resetting vibration setting for " + self.deviceName)
			indigo.device.turnOff(self.devIndigoID)

	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmMultisensorVibration: " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorVibration: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorVibration: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		if origDev.onState != newDev.onState:
			mmLib_Log.logForce(newDev.name + ": Vibrating = " + str(newDev.onState))

		else:
			mmLib_Log.logDebug(newDev.name + ": Received duplicate command: Vibrating = " + str(newDev.onState))


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
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorLuminance: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorLuminance: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		if origDev.sensorValue != newDev.sensorValue:
			# take this time to update the Lux level
			mmLib_Low.setIndigoVariable(self.luxLevelVar, str(newDev.sensorValue))
			mmLib_Log.logForce(newDev.name + ": Value = " + str(newDev.sensorValue) + " Lux")
		else:
			mmLib_Log.logDebug(newDev.name + ": Received duplicate value: Lux = " + str(newDev.sensorValue))


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
		theDegrees = (float(self.theIndigoDevice.sensorValue) * 1.8) + 32.0
		mmLib_Low.setIndigoVariable(self.tempFLevelVar, str(theDegrees) + 'F')
		return(theDegrees)

	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmMultisensorTemperature: " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmMultisensorTemperature: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmMultisensorTemperature: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):

		theTempF = self.setTemperature()

		if origDev.sensorValue != newDev.sensorValue:
			mmLib_Log.logForce(newDev.name + ": Value = " + str(theTempF) + " Degrees F")
		else:
			mmLib_Log.logDebug(newDev.name + ": Received duplicate value: Temperature = " + str(theTempF))


		return(0)


