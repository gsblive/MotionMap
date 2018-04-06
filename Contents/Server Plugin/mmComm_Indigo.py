__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

# import json
# import os
# import traceback
# import datetime
# from collections import deque
# import itertools
# import pickle
# import collections

try:
	import indigo
except:
	pass

import mmLib_Log
import mmLib_Low
import mmLib_CommandQ
import time
from collections import deque


######################################################
#
# mmIndigo - An mmIndigo Entry... Just handle the Search Queues, DeviceName, theIndigoDevice, devIndigoAddress and devIndigoID
#
######################################################
class mmIndigo(object):
	#
	# __init__
	#
	def __init__(self, theDeviceParameters):
		#
		# Set object variables
		#
		self.initResult = 0

		self.deviceName = theDeviceParameters["deviceName"]
		self.mmDeviceType = theDeviceParameters["deviceType"]
		self.companionDeque = deque()				# make companion Deque for collaborations
		self.debugDevice = 0
		try:
			if theDeviceParameters["debugDeviceMode"] != "noDebug":
				self.debugDevice = 1
				mmLib_Low.DebugDevices[self.deviceName] = 1
			else:
				mmLib_Low.DebugDevices[self.deviceName] = 0
		except:
			mmLib_Log.logVerbose("debugDeviceMode field is undefined in config file for " + self.deviceName + " , " + self.mmDeviceType)

		mmLib_Log.logVerbose("Initializing mmIndigo" + self.deviceName + " , " + self.mmDeviceType)
		try:
			existingDevice = mmLib_Low.MotionMapDeviceDict[self.deviceName]
			mmLib_Log.logForce("### Processing Device Entry: " + self.deviceName + " device already exists. using first entry only.")
			self.initResult = "Duplicate Entry"
		except:
			# this is a normal result
			try:
				self.theIndigoDevice = indigo.devices[self.deviceName]
				self.devIndigoAddress = str(self.theIndigoDevice.address)
				self.devIndigoID = self.theIndigoDevice.id
			except:
				if self.mmDeviceType not in mmLib_Low.MMVirtualDeviceTypes:
					mmLib_Log.logForce("###### Warning: " + self.mmDeviceType + " device named " + self.deviceName + " does not exist. Add new virtual device types to mmLib_Low.MMVirtualDeviceTypes ######")
					self.initResult = "DeviceType " + self.mmDeviceType + " does not exist."

				# No indigo device use default index
				self.theIndigoDevice = "none"
				self.devIndigoAddress = self.mmDeviceType + ".addr." + self.deviceName
				self.devIndigoID = self.mmDeviceType + ".id." + self.deviceName

			#self.mmSignature = mmLib_Low.makeMMSignature(self.devIndigoID, self.devIndigoAddress )

			# Enqueue in search dictionary
			mmLib_Low.MotionMapDeviceDict[self.devIndigoID] = self
			mmLib_Low.MotionMapDeviceDict[self.devIndigoAddress] = self
			mmLib_Low.MotionMapDeviceDict[self.deviceName] = self
			#mmLib_Low.MotionMapDeviceDict[self.mmSignature] = self
			mmLib_Log.logDebug("Processing Device Entry: " + self.deviceName + " with address of " + self.devIndigoAddress)

			self.ourNonvolatileData = mmLib_Low.initializeNVDict(self.deviceName)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "timeoutCounter", 0)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "errorCounter", 0)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "highestSequentialErrors", 0)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "unresponsive", 0)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "sequentialErrors", 0)

			try:
				self.maxSequentialErrors = int(theDeviceParameters["maxSequentialErrorsAllowed"])
			except:
				self.maxSequentialErrors = mmLib_Low.MAX_SEQUENTIAL_ERRORS_DEFAULT


			self.lastUpdateTimeSeconds = 0
			self.setLastUpdateTimeSeconds()
			self.onlineState = 'on'

		self.supportedCommandsDict = {'devStatus': self.devStatus}


	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################

	#
	# deviceUpdatedEvent - Base class... all devices do this
	#
	def	deviceUpdatedEvent(self,eventID, eventParameters):

		# the device appears to be alive, reset the unresponsive flag
		self.ourNonvolatileData["unresponsive"] = 0

		# and reset the lastupdatetime timers
		self.setLastUpdateTimeSeconds()
		return 0

	#
	# receivedCommandEvent - we received a command from our device. This will take priority over anything in our queue. Flush the queue
	#                   A light switch for example may pass us an on or off command. The user clicked it, so that should take priority over anything we are doing
	#
	def receivedCommandEvent(self, eventID, eventParameters ):

		mmLib_Log.logForce("Higher level function must override receivedCommandEvent for: " + self.deviceName)

		return 0

	#
	# completeCommandEvent - we received a commandSent completion message from the server for this device.
	#
	def completeCommandEvent(self, eventID, eventParameters ):

		mmLib_Log.logForce("Higher level function must override completeCommandEvent for: " + self.deviceName)

		return 0

	#
	# errorCommandEvent - we received a commandSent completion message from the server for this device.
	#
	def errorCommandEvent(self, eventID, eventParameters  ):

		mmLib_Log.logForce("Higher level function must override errorCommandEvent for: " + self.deviceName)

		return 0

	def reportAddress(self):
		mmLib_Log.logForce("   >>>> deviceName is " + str(self.deviceName))
		mmLib_Log.logForce("   >>>> devIndigoAddress is " + str(self.devIndigoAddress))

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	#  	All commands in this section must have a single parameter theCommandParameters - a list of parameters
	# 	And all commands must be registered in self.supportedCommandsDict variable
	#
	######################################################################################



	#
	#  Flash Device - Flash our device
	#
	def flashDevice(self, theCommandParameters):
		completion = self.flashDeviceLow(theCommandParameters)
		#if completion == 'done': completion = 0
		return completion

	#
	# devStatus - Print Status information for this device to the log
	#
	def devStatus(self, theCommandParameters):
		mmLib_Log.logForce("Default status." + self.deviceName + " has no status handler routine.")

	#
	#  beepDevice - Beep the Device
	#
	def beepDevice(self, theCommandParameters):
		mmLib_Log.logForce("Default beep Function." + self.deviceName + " has no status handler routine.")

	#
	#  Toggle Device
	#
	def toggleDevice(self, theCommandParameters):
		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return 'unresponsive'

		indigo.device.toggle(self.devIndigoID)

	#
	#  Set Brightness
	#
	def brightenDevice(self, theCommandParameters):

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return 'unresponsive'

		try:
			theValue = theCommandParameters['theValue']
		except:
			mmLib_Log.logError("brightenDevice - Must specify a value for: " + self.deviceName)
			return 'brightenDevice: required parameter not present'

		if self.theIndigoDevice.__class__ == indigo.DimmerDevice:
			mmLib_Log.logDebug("brightenDevice - theCommand Value: " + str(theValue))

			try:
				defeatTimerUpdateParm = theCommandParameters["defeatTimerUpdate"]
			except:
				defeatTimerUpdateParm = 0

			self.defeatTimerUpdate = defeatTimerUpdateParm
			indigo.dimmer.setBrightness(self.devIndigoID, value=int(theValue))
		else:
			return self.onOffDevice(theCommandParameters)

		return 0




	######################################################################################
	#
	# Support Routines
	#
	######################################################################################


	#
	# registerCompanion
	#
	def registerCompanion(self, theCompanionDevice):

		mmLib_Log.logVerbose("HVAC Companion " + theCompanionDevice.deviceName + " is registering to: " + str(self.deviceName))

		self.companionDeque.append(theCompanionDevice)

		return(0)

	#
	# getOccupancyTimeout - return an int that indicates the number of minutes that must transpire before a non-occupancy state is assumed
	#
	def getOccupancyTimeout(self):

		try:
			theResult = int(self.minMovement)
		except:
			mmLib_Log.logVerbose(self.deviceName + " does not support the function getOccupancyTimeout. Continuing with large response of 1000000")
			theResult = int(1000000)

		return int(theResult)

	#
	# getSecondsSinceUpdate - how many seconds since the device has changed state
	#
	def getSecondsSinceUpdate(self):
		if self.onlineState == 'off': return int(60 * 60 * 24)  # default to a high number if the device is offline
		return int(time.mktime(time.localtime()) - self.lastUpdateTimeSeconds)

	#
	# getSecondsSinceState - how many seconds since the device was in the given on/off state
	#
	def getSecondsSinceState(self, theState):

		mmLib_Log.logForce("Invalid call to getSecondsSinceState. " + self.deviceName + " cannot track onOff States in mmIndigo.")

		return int(self.getSecondsSinceUpdate())

	#
	# getSecondsSinceEventInArea - Return the number of seconds of the last 'theEventOfInterest' in a given area (according to one or more controllers)
	#
	#  controllerList the controllers to evaluate
	#  theEventOfInterest - the event type we are looking for 'on', 'off', 'OccupiedAll', and 'UnoccupiedAll'
	#  theMode - 	'all' - all the devices must be in the the correct 'theEventOfInterest'
	#  			'any' - any of the devices must be in the the correct 'theEventOfInterest'
	#  theTarget - 'least' = return the target with the Least number of seconds
	#  			'greatest' = return the target with the Least number of seconds
	#  			note: Of course if theMode is 'any' this routine will return the matching target with any number of seconds
	#
	# ['MiddleFloorBathToiletMotion', 'MiddleFloorBathMotion', 'TopFloorStairsMotion', 'TopFloorMasterMotion'], True, all, least
	def getSecondsSinceEventInArea(self, controllerList, theEventOfInterest, theMode, theTarget):
		targetFound = 'undefined'

		# Find the most recent 'on' time

		for otherControllerName in controllerList:
			if not otherControllerName:
				break
			try:
				theController = mmLib_Low.MotionMapDeviceDict[otherControllerName]
			except:
				mmLib_Log.logForce("*** Cant find device named: " + otherControllerName)

			if theEventOfInterest == 'on' and theController.theIndigoDevice.onState == True:
				testResult = 1
			elif theEventOfInterest == 'off' and theController.theIndigoDevice.onState == False:
				testResult = 1
			elif theEventOfInterest == 'OccupiedAll' and theController.occupiedState == True:
				testResult = 1
			elif theEventOfInterest == 'UnoccupiedAll' and theController.occupiedState == False:
				testResult = 1
			else:
				testResult = 0

			if not testResult:
				if theMode == 'all': return 0  # this device isnt in the right state, so 'all' can never be true. bail
			else:
				# checkingControllerSeconds = theController.getSecondsSinceUpdate()
				checkingControllerSeconds = theController.getSecondsSinceState(theEventOfInterest)

				if theMode == 'any':
					targetFound = checkingControllerSeconds
					break  # we found one, we are done

				if theTarget == 'least':
					if targetFound != 'undefined' and checkingControllerSeconds > targetFound: continue
				else:
					if targetFound != 'undefined' and checkingControllerSeconds < targetFound: continue

				targetFound = checkingControllerSeconds  # then continue with next itteration

		# if we couldnt get a reading from the sensors (for whatever reason), return 0. If we get a zero reading (we cant return that), so return 1.
		if targetFound == 'undefined':
			targetFound = int(0)
		elif targetFound == 0:
			targetFound = int(1)

		return targetFound

	#
	# getSecondsSinceMotionInArea - the number of seconds of the last 'on' event in a given area (according to one or more controllers)
	#
	def getSecondsSinceMotionInArea(self, controllerList):

		recentOffSeconds = self.getSecondsSinceEventInArea(controllerList, 'on', 'any', 'greatest')
		mmLib_Log.logVerbose(self.deviceName + "\'s area has shown motion for " + str(recentOffSeconds) + " seconds.")

		return recentOffSeconds

	#
	# getSecondsSinceNoMotionInArea - the number of seconds of the last 'off' event in a given area (according to one or more controllers)
	#
	def getSecondsSinceNoMotionInArea(self, controllerList):

		recentOffSeconds = self.getSecondsSinceEventInArea(controllerList, 'off', 'all', 'least')
		mmLib_Log.logVerbose(self.deviceName + "\'s area has shown no motion for " + str(recentOffSeconds) + " seconds.")

		return recentOffSeconds

	#
	# setLastUpdateTimeSeconds - note the time when the device changed state
	#
	def setLastUpdateTimeSeconds(self):
		if self.lastUpdateTimeSeconds == 0 and self.theIndigoDevice != "none":  # set the initial value to the indigo value
			st = time.strptime(str(self.theIndigoDevice.lastChanged), "%Y-%m-%d %H:%M:%S")
			self.lastUpdateTimeSeconds = time.mktime(st)
		else:
			self.lastUpdateTimeSeconds = time.mktime(time.localtime())

		return ()


	#
	# validateCommand
	#
	def validateCommand(self, theCommand):

		try:
			theHandler = self.supportedCommandsDict[theCommand]
		except:
			mmLib_Log.logForce("Invalid command, " + theCommand + " sent to " + self.deviceName + " valid commands are: " + str(self.supportedCommandsDict))
			theHandler = 0
		return theHandler

	#
	# queueCommand (for execution later)
	#
	def queueCommand(self, theCommandParameters):

		theResult = 1

		try:
			theMMDeviceName = theCommandParameters['theDevice']
		except:
			theResult = 0
			mmLib_Log.logError("No device Name given")

		try:
			theMMDevice = mmLib_Low.MotionMapDeviceDict[theMMDeviceName]
		except:
			theResult = 0
			mmLib_Log.logError(" No MM Device Named \"" + theMMDeviceName + "\".")

		try:
			theMMDevice.validateCommand(theCommandParameters['theCommand'])
			# note: check for valid parameters eventually when the command actually gets dispatched
		except:
			theResult = 0
			mmLib_Log.logForce(theMMDevice.deviceName + " Command \"" + str(theCommandParameters) + "\" could not be queued. NO HANDLER")

		if(theResult):
			# note: The following can't fail. However if the queue was previously empty, the command will execute which may fail.
			#    we dont have this in a try statement because we dont want to mask the failures, we want to fix them (as they present themselves as errors)

			if "NoFlush" in theCommandParameters:
				mmLib_CommandQ.enqueQ(theMMDevice, theCommandParameters, 0)
			else:
				mmLib_CommandQ.enqueQ(theMMDevice, theCommandParameters, ['theCommand'])

		return theResult


	#
	# command Dispatcher (realtime)
	#
	def dispatchCommand(self, theCommandParameters):

		if self.initResult != 0:
			mmLib_Log.logForce(self.deviceName + "###### Is not Initialized for command " + theCommandParameters['theCommand'] + ". ######")
			return 0

		resultCode = 0

		try:
			theHandler = self.validateCommand(theCommandParameters['theCommand'])
		except:
			pass

		if not theHandler:
			mmLib_Log.logVerbose(self.deviceName + " Has no Handler for command " + theCommandParameters['theCommand'])
			return resultCode

		#mmLib_Log.logForce("Command for " + self.deviceName + " Handler: "+ str(theHandler) + " The Command" + str(theCommandParameters))
		resultCode = theHandler(theCommandParameters)

		# If we are running async (not waiting for ack), we have to do the repeats here (we will dequeue the command upon return)
		if resultCode == 'Dque':
			try:
				nTimes = theCommandParameters['repeat']
			except:
				nTimes = 0

			while nTimes:
				resultCode = theHandler(theCommandParameters)
				nTimes = nTimes - 1

		return resultCode

	#
	# errorCommandLow - Process the error coming from theCommandParameter.
	#
	#  errorType:
	# 		'Error' - if its an error result
	# 		'Timeout' - if its a timeout result
	#
	def errorCommandLow(self, theCommandParameters, errorType):

		if errorType == 'Error':
			self.ourNonvolatileData["errorCounter"] = self.ourNonvolatileData["errorCounter"] + 1
			self.ourNonvolatileData["sequentialErrors"] = self.ourNonvolatileData["sequentialErrors"] + 1

			if self.ourNonvolatileData["sequentialErrors"] > self.ourNonvolatileData["highestSequentialErrors"]: self.ourNonvolatileData["highestSequentialErrors"] = self.ourNonvolatileData["sequentialErrors"]

			if self.ourNonvolatileData["sequentialErrors"] > self.maxSequentialErrors:
				mmLib_Log.logVerbose("Too many sequential errors for " + self.deviceName + " it\'s going offline")
				self.ourNonvolatileData["unresponsive"] = 1
		elif errorType == 'Timeout':
			self.ourNonvolatileData["timeoutCounter"] = self.ourNonvolatileData["timeoutCounter"] + 1
		else:
			mmLib_Log.logForce("Unknown error type " + str(errorType) + " for " + self.deviceName + ".")

		if theCommandParameters:
			mmLib_Log.logVerbose(str(errorType) + " on command " + theCommandParameters['theCommand'] + " to " + self.deviceName)
			if errorType == 'Error':
				try:
					retryVal = theCommandParameters["retry"]
				except:
					retryVal = 0
			else:
				# lets not process retries for timeouts... they take so much time.. The command probably happened eanyway (we just missed the response)
				retryVal = 0

			if retryVal:
				mmLib_Log.logForce("Retrying command " + mmLib_CommandQ.pendingCommands[0]['theCommand'] + " for device " + self.deviceName)
				mmLib_Log.logForce("    Full Queued Command is " + str(mmLib_CommandQ.pendingCommands[0]))
				theCommandParameters["retry"] = retryVal - 1
				mmLib_CommandQ.dequeQ(0)  # Process the Retry
			else:
				# The command failed. Enqueue a status request just in case the message really got through (we will get the updated value)
				if theCommandParameters['theCommand'] != 'sendStatusRequest':

					if 'sendStatusRequest' in self.supportedCommandsDict:
						self.queueCommand({'theCommand': 'sendStatusRequest', 'theDevice': self.deviceName,'theValue': 0, 'retry': 2})

				mmLib_CommandQ.dequeQ(1)  # Give up on this command, pop our old command off and Restart the Queue

		return 0

	#
	#  Flash Device Low - this is a multistate command, return the phase name we are in, and return 'done' when all phases are complete
	#
	def flashDeviceLow(self, theCommandParameters):

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return 'done'  # pop our old command off and Restart the Queue

		# what phase of flash are we on?
		try:
			initialPhase = theCommandParameters['phase']
		except:
			initialPhase = 'start'

		mmLib_Log.logVerbose(theCommandParameters['theCommand'] + " command, phase " + initialPhase + " on device " + self.deviceName)

		if initialPhase == 'start':
			#  only start flash is the device is on
			if indigo.devices[self.devIndigoID].onState == True:
				# before we turn it off, lets capture the current brightness setting
				theCommandParameters["defeatTimerUpdate"] = 'flash'  # always force time update defeat on flash, this will be preserved through phase 2
				theCommandParameters['restoreValue'] = self.getBrightness()  # preserve restore value
				theCommandParameters['theValue'] = 0  # Going Off during Phase 1
				thePhase = 'one'
				self.brightenDevice(theCommandParameters)
			else:
				# skip the whole thing
				mmLib_Log.logForce("Flash was called for device that was NOT on: " + self.deviceName)
				thePhase = 'done'  # pop our old command off and Restart the Queue

		elif initialPhase == 'one':
			# entering phase 2... reset the retries, we want to make sure it goes back "on"
			theCommandParameters['retry'] = 2
			theCommandParameters['theValue'] = theCommandParameters['restoreValue']
			mmLib_Log.logVerbose("Completing Flash command... " + str(theCommandParameters))
			self.brightenDevice(theCommandParameters)
			thePhase = 'two'  # continue processing into phase 2

		elif initialPhase == 'two':
			thePhase = 'done'  # all is well, pop our old command off and Restart the Queue

		else:
			mmLib_Log.logForce("Unexpected phase " + initialPhase + " during flash of " + self.deviceName + " aborting the flash command.")
			thePhase = 'done'  # all is well, pop our old command off and Restart the Queue

		theCommandParameters['phase'] = thePhase
		return thePhase

	#
	#  isCommandImmed
	# 		Return 1 if the command was immediate, 0 otherwise
	#
	def isCommandImmed(self, theCommandParameters):
		try:
			theImmedFlag = theCommandParameters['theMode']
			if theImmedFlag != 'IMMED': theImmedFlag = 0
		except:
			theImmedFlag = 0
		return theImmedFlag

	#
	#  onOffDevice - we use brightness at a higher level, using 0 and 100 for devices that dont support brightness. This routine is here for those devices
	#  and is called from our brightenDevice routine
	#
	def onOffDevice(self, theCommandParameters):

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return 'unresponsive'

		theValue = theCommandParameters['theValue']
		mmLib_Log.logDebug("onOff - theCommand Value: " + str(theValue))

		try:
			defeatTimerUpdateParm = theCommandParameters["defeatTimerUpdate"]
		except:
			defeatTimerUpdateParm = 0

		self.defeatTimerUpdate = defeatTimerUpdateParm

		if theValue != 0:
			indigo.device.turnOn(self.devIndigoID)
		else:
			indigo.device.turnOff(self.devIndigoID)

		return 0

	########################################################
	############## Command and queue processing ############
	########################################################

	#
	# checkForOurMMCommand - Return a 1 of the command notification we received (motionmap command) matches what we expected on top of the queue
	#
	def checkForOurMMCommand(self, theMMCommand):
		if mmLib_CommandQ.pendingCommands:
			qHead = mmLib_CommandQ.pendingCommands[0]
			if qHead['theIndigoDeviceID'] == self.devIndigoID:  # is our device on top of the queue?
				headCommand = qHead['theCommand']
				if headCommand == theMMCommand:
					return 1  # yes it was our command
		return 0

	#
	# checkForOurCommandByte - Return a 1 of the command notification we received (theCommand) matches what we expected on top of the queue
	#
	def checkForOurCommandByte(self, theCommand):

		mmLib_Log.logForce("Higher level function must override checkForOurCommandByte for: " + self.deviceName)

		return 0

	#
	# receivedCommandByte - we received a command from our device. This will take priority over anything in our queue. Flush the queue
	#                   A light switch for example may pass us an on or off command. The user clicked it, so that should take priority over anything we are doing
	#
	def receivedCommandByte(self, theCommandByte):

		mmLib_Log.logForce("Higher level function must override receivedCommandByte for: " + self.deviceName)
		return 0

	#
	# completeCommandByte - we received a commandSent completion message from the server for this device.
	#
	def completeCommandByte(self, theCommandByte):

		self.ourNonvolatileData["sequentialErrors"] = 0
		self.ourNonvolatileData["unresponsive"] = 0

		if mmLib_CommandQ.pendingCommands:
			qHead = mmLib_CommandQ.pendingCommands[0]
			theCommand = qHead['theCommand']
			if self.checkForOurCommandByte(theCommandByte):

				# special processing for multiphase commands (flash for example)
				if theCommand == 'flash':
					if self.flashDeviceLow(qHead) != 'done': return 0  # still not done, let it continue to process

				# is the result what was expected?
				if theCommand == 'brighten':
					try:
						theValue = qHead['theValue']
						currentBrightness = self.getBrightness()
						if theValue == currentBrightness:
							mmLib_Log.logVerbose("Command Complete... Value Matches")
						else:
							mmLib_Log.logVerbose("Command Complete but Value does not match... Device " + self.deviceName + " brightness is now " + str(currentBrightness) + " Update Maseter " + self.loadDeviceName + " to " + str(currentBrightness))
					except:
						mmLib_Log.logVerbose("=== Command Complete... No Value Found")

				try:
					repeatVal = qHead["repeat"]
				except:
					repeatVal = 0

				if repeatVal:
					qHead["repeat"] = repeatVal - 1
					mmLib_Log.logVerbose("Successful " + theCommand + " command to " + self.deviceName + " RepeatVal: " + str(repeatVal))
					mmLib_CommandQ.dequeQ(0)  # all is well, but we have to do a repeat
				else:
					mmLib_Log.logVerbose("Successful " + theCommand + " command to " + self.deviceName)
					mmLib_CommandQ.dequeQ(1)  # all is well, pop our old command off and Restart the Queue
			else:
				# someone else sent a similar command while our commands were waiting, delete all of our commands (defer to other process)
				mmLib_Log.logVerbose("Flushing commands for " + self.deviceName + ", because the server sent a command that wasnt our command. The command byte: " + str(theCommandByte))
				mmLib_CommandQ.flushQ(self, qHead, ["theCommand"])

		return 0
