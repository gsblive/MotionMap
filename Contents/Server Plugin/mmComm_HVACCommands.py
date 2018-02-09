
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

try:
	import indigo
except:
	pass

import mmLib_Log
import mmLib_Low
import mmComm_Insteon
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections



######################################################
#
# mmHVACInsteon - Thermostat communication object must be overridden by mmLogic_HVAC.py
#
######################################################
class mmHVACCommands(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):
		mmLib_Log.logVerbose( "mmHVACCommands Initialization. ")
		super(mmHVACCommands, self).__init__(theDeviceParameters)  # Initialize Base Class
		self.supportedCommandsDict.update({'devStatus':self.devStatus, 'setHVACMode':self.setHVACMode, 'setHVACFanMode':self.setHVACFanMode, 'setHVACCoolSetpoint':self.setHVACCoolSetpoint, 'setHVACHeatSetpoint':self.setHVACHeatSetpoint})
		#
		# Set object variables
		#
		self.initResult = 0
		self.initializationInProgress = 1
		self.onControllers = {}
		self.sustainControllers = {}
		self.combinedControllers = {}
		self.updateFrequency = 0
		self.maxTempDelta = 0
		self.customCoolSetpoint = 0
		self.customHeatSetpoint = 0
		self.calculatedHeatSetpoint = 0
		self.calculatedCoolSetpoint = 0
		self.areaOccupied = 1
		self.operationalMode = 'HvacMonitor'
		self.coolSetpoint = int(theDeviceParameters["coolSetpoint"])
		self.heatSetpoint = int(theDeviceParameters["heatSetpoint"])
		self.allowAsync = int(theDeviceParameters["allowAsync"])

		self.statusMessage = "Unitialized."


	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################

	#
	# deviceUpdated -
	#
	#def deviceUpdated(self, origDev, newDev):
	#
	#	super(mmHVACCommands, self).deviceUpdated(origDev, newDev)	# Nothing special here, forward to the Base class



	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	#def completeCommand(self, theInsteonCommand ):
	#	super(mmHVACCommands, self).completeCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# receivedCommand - we received a command from our device.
	#
	#def receivedCommand(self, theInsteonCommand ):
	#	super(mmHVACCommands, self).receivedCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	#def errorCommand(self, theInsteonCommand ):
	#	super(mmHVACCommands, self).errorCommand(theInsteonCommand)	# Nothing special here, forward to the Base class



	######################################################################################
	#
	# Externally Addressable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	#
	# devStatus - Print Status information for this device to the log
	#
	def	devStatus(self, theCommandParameters):
		mmLib_Log.logForce("Default status." + self.deviceName + ":\n " + self.statusMessage)
		return(0)

	#
	# Set the HVAC mode as defined in theCommandParameters
	#
	def setHVACMode(self, theCommandParameters):
		resultCode = 0
		try:
			operationMode = theCommandParameters['theValue']
		except:
			mmLib_Log.logForce("setHVACMode Requires an operationMode value in \'theValue\'. Device: " + self.deviceName)
			return("missingOperationMode")

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return('unresponsive')

		if self.allowAsync:
			if operationMode == indigo.kHvacMode.Heat:
				resultCode = self.sendRawInsteonCommandLow( [107, 10, 10, 0, 0], False, True)
			elif operationMode == indigo.kHvacMode.Cool:
				resultCode = self.sendRawInsteonCommandLow( [107, 11, 11, 0, 0], False, True)
			elif operationMode == indigo.kHvacMode.HeatCool:
				resultCode = self.sendRawInsteonCommandLow( [107, 12, 12, 0, 0], False, True)
			else:
				mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. Illegal Operation mode for " + self.deviceName)
		else:
			resultCode = indigo.thermostat.setHvacMode(self.devIndigoID, value=operationMode)

		return(resultCode)



	#
	# Set the HVAC Fanmode as defined in theCommandParameters
	#
	def setHVACFanMode(self, theCommandParameters):
		resultCode = 0

		try:
			newFanMode = theCommandParameters['theValue']
		except:
			mmLib_Log.logForce("setHVACFanMode Requires a fanmode value in \'theValue\'. Device: " + self.deviceName)
			return("missingFanMode")

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return('unresponsive')

		if self.allowAsync:
			if newFanMode == indigo.kFanMode.AlwaysOn:
				resultCode = self.sendRawInsteonCommandLow( [107, 7, 7, 0, 0], False, True)
			elif newFanMode == indigo.kFanMode.Auto:
				resultCode = self.sendRawInsteonCommandLow( [107, 6, 6, 0, 0], False, True)
			else:
				mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. Illegal Fan mode for " + self.deviceName)
		else:
			resultCode = indigo.thermostat.setFanMode(self.devIndigoID, value=newFanMode)

		return(resultCode)

	#
	# Set the HVAC Cool Setpoint as defined in theCommandParameters
	#
	def setHVACCoolSetpoint(self, theCommandParameters):

		resultCode = 0

		try:
			newSetPoint = theCommandParameters['theValue']
		except:
			mmLib_Log.logForce("setHVACCoolSetpoint Requires Setpoint amount in \'theValue\'. Device: " + self.deviceName)
			return(0)

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return('unresponsive')

		if int(self.theIndigoDevice.coolSetpoint) != int(newSetPoint):
			if self.allowAsync:
				resultCode = self.sendRawInsteonCommandLow([mmComm_Insteon.kInsteonHVACCoolSetpoint, int(newSetPoint) * 2, int(newSetPoint) * 2, 4, 0], False, True)
			else:
				resultCode = indigo.thermostat.setCoolSetpoint(self.devIndigoID, value=int(newSetPoint))

		return(resultCode)


	#
	# Set the HVAC Heat Setpoint as defined in theCommandParameters
	#
	#	Setpoint = the setpoint (must convert to int)
	def setHVACHeatSetpoint(self, theCommandParameters):

		resultCode = 0

		try:
			newSetPoint = theCommandParameters['theValue']
		except:
			mmLib_Log.logForce("setHVACHeatSetpoint Requires Setpoint amount in \'theValue\'. Device: " + self.deviceName)
			return(0)

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return('unresponsive')

		if int(self.theIndigoDevice.coolSetpoint) != int(newSetPoint):
			if self.allowAsync:
				resultCode = self.sendRawInsteonCommandLow([mmComm_Insteon.kInsteonHVACHeatSetpoint, int(newSetPoint) * 2, int(newSetPoint) * 2, 4, 0], False, True)
			else:
				resultCode = indigo.thermostat.setHeatSetpoint(self.devIndigoID, value=int(newSetPoint))

		return(resultCode)

