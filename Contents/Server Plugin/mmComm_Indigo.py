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
import bisect

try:
	import indigo
except:
	pass

import mmLib_Log
import mmLib_Low
import mmLib_CommandQ
import time
import mmComm_Insteon
from collections import deque
import random

# For BrightenWithRamp
tenthValues = [1,3,20,65,190,230,280,320,380,470,900,1500,2100,2700,3600,4800]

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
		self.StatusType = 'Off'						# default status type
		try:
			if theDeviceParameters["debugDeviceMode"] != "noDebug":
				self.debugDevice = 1
				mmLib_Low.DebugDevices[self.deviceName] = 1
				mmLib_Log.logForce("### Debugging Device " + self.deviceName)
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
	#	Support for SetBrightnessWithRamp (0x2E)
	#
	#	makeRampCmdModifier(level,RampRateSeconds)
	# 		where
	# 			Level = 0-100%
	# 		and
	# 			RampRateSeconds = .1-480 seconds
	#
	# cmd modifier = Bits 4-7 = OnLevel + 0x0F and Bits 0-3 = 2 x RampRate + 1
	#		where
	# 			onLevel is 16 levels of brightness (0-15) : 0 = off and 15 = 100%
	# 		and
	# 			RampRate = 0-15 log indexed into [1,3,20,65,190,230,280,320,380,470,900,1500,2100,2700,3600,4800] seconds,
	# 			then inverted by subtracting it by 15:
	#
	def makeRampCmdModifier(self, theLevel, RampRateSeconds):

		global tenthValues

		if RampRateSeconds < 0.1:
			RampRateSeconds = 0.1
		elif RampRateSeconds > 480:
			RampRateSeconds = 480

		onLevel = int(theLevel / 6.5) * 0x10

		iPoint = bisect.bisect_left(tenthValues, int(RampRateSeconds * 10))
		# print str(tenthValues[iPoint]/10.0) + " is closest to requested " + str(RampRateSeconds) + " seconds"

		finalCmd = onLevel + (15 - iPoint)
		return finalCmd

	#
	# continueDimming -		Continue stepped dimming in this timer proc
	#						All timer procs return 0 to dequeue the timer or nSeconds to requeue the timer for specified number of seconds
	def continueDimming(self,theCommandParameters):

		finalLoop = 0

		if self.debugDevice: mmLib_Log.logForce( "Continue Dimming device " + self.deviceName)

		# If the target expirationTime has been met, set the final brightness, if not continue on to next brightness step

		currentBrightness = int(self.theIndigoDevice.states['brightnessLevel'])

		try:
			recentBrightness = theCommandParameters['recentBrightness']
		except:
			#if self.debugDevice: mmLib_Log.logForce("Command Parameters:" + str(theCommandParameters))
			#if self.debugDevice: mmLib_Log.logForce("Dimming device " + self.deviceName + " does not have a recent brightness value... initializing it to " + str(currentBrightness))
			recentBrightness = currentBrightness


		try:
			targetValue = int(theCommandParameters['targetBrightness'])
		except:
			mmLib_Log.logWarning("This should not be possible... No target value in command parameters for continueDimming proc for " + self.deviceName + " The command Parameters: " + str(theCommandParameters))
			return 0	#Exit due to missing parametrer

		#if self.debugDevice: mmLib_Log.logForce( "Dimming device " + self.deviceName + " Current brightness and Target value: " + str(currentBrightness) + ", " + str(targetValue) + ". Recent Brightness: " + str(recentBrightness))

		# mm/indigo brightness commands are processed as a percentage, but the hardware only has 32 steps,
		# so we determine our target is met when we are within 3.125 percent (4 for short)

		if int(theCommandParameters['UpOrDown']) == mmComm_Insteon.kInsteonIncreaseBrightness:
			# We are increasing Brightness
			if recentBrightness > currentBrightness:
				# Brightness went the wrong direction
				mmLib_Log.logWarning("Unexpected Brightness. While increasing brightness of device " + self.deviceName + " recent brightness (" + str(recentBrightness) + ") greater than currentBrightness.")
				return 0	# exit due to brightness meddling
			if currentBrightness > targetValue and (currentBrightness-targetValue) > 4:
				# Brightness went too far in the right diection
				mmLib_Log.logWarning("Unexpected Brightness. While increasing brightness of device " + self.deviceName + " current brightness (" + str(recentBrightness) + ") is greater than targetValue.")
				return 0 # exit due to brightness meddling
			if currentBrightness >= targetValue: finalLoop = 1
		else:
			# We are Decreasing Brightness
			if recentBrightness < currentBrightness:
				# Brightness went the wrong direction
				mmLib_Log.logWarning("Unexpected Brightness. While decreasing brightness of device " + self.deviceName + " recent brightness (" + str(recentBrightness) + ") less than currentBrightness.")
				return 0 # exit due to brightness meddling
			if currentBrightness < targetValue and (targetValue-currentBrightness) > 4:
				# Brightness went too far in the right diection
				mmLib_Log.logWarning("Unexpected Brightness. While decreasing brightness of device " + self.deviceName + " current brightness (" + str(recentBrightness) + ") is less than targetValue.")
				return 0 # exit due to brightness meddling
			if currentBrightness <= targetValue: finalLoop = 1


		if finalLoop:
			# do the final brightness command to make sure we are at the correct requested level (no ramp)
			if self.debugDevice: mmLib_Log.logForce("All Brightness steps complete for " + self.deviceName)
			self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': targetValue, 'retry': 2})
			self.queueCommand({'theCommand': 'sendStatusRequest', 'theDevice': self.deviceName, 'theValue': 998, 'retry': 0})
			return 0
		else:
			# continue with the brightness steps
			if self.debugDevice: mmLib_Log.logForce("Continue Dimming device. Issuing next step for " + self.deviceName)
			self.queueCommand({'theCommand':'sendRawInsteonCommand', 'theDevice':self.deviceName, 'ackWait':0, 'cmd1':int(theCommandParameters['UpOrDown']), 'cmd2':0, 'retry':0})
			self.queueCommand({'theCommand': 'sendStatusRequest', 'theDevice': self.deviceName, 'theValue': 997, 'retry': 0})
			continueTimeVariance = int((random.randint(1, 4)) * mmLib_Low.TIMER_QUEUE_GRANULARITY)	# randomize our timing so all devices dont fire on the same cycle when changing brightness.
			# update recentBrightness for later to determine if the brightness was inadvertantly tampered with while ramping
			return {'timeDeltaSeconds': continueTimeVariance, 'recentBrightness':currentBrightness}

		return 0

	#
	# completeAutonomousDimming -	Dimmer ramp (old version) completion proc
	#								All timer procs return 0 to dequeue the timer or nSeconds to requeue the timer for specified number of seconds
	def completeAutonomousDimming(self,theCommandParameters):

		if self.debugDevice: mmLib_Log.logForce( "Completing Ramp down to 0 for " + theCommandParameters['theDevice'])
		self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': 0, 'retry': 2})
		return 0
	#
	#  Set Brightness... Old version. 	There is a bug in the insteon dimmers thaet when you use a ramp command, the device is unresponsive
	#  									until the full timeout on the ramp. This version of the brighten command has been largely retired.
	#  									It is only used when a custom ramp command is being used. That is only accessed programatically
	#  									from Action Group test commands.
	#  									The version below is the one used now, but it calls this routine in the case of a custom ramp command.
	#
	def brightenDeviceOld(self, theCommandParameters):

		if self.debugDevice: mmLib_Log.logForce( "brightenDeviceOld for " + self.deviceName + " CommandParameters: " + str(theCommandParameters))

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return 'unresponsive'

		try:
			theValue = int(theCommandParameters['theValue'])
		except:
			mmLib_Log.logError("brightenDevice - Must specify a value for: " + self.deviceName)
			return 'brightenDevice: required parameter not present'


		if self.theIndigoDevice.__class__ == indigo.DimmerDevice:
			mmLib_Log.logDebug("brightenDevice - theCommand Value: " + str(theValue))

			self.defeatTimerUpdate = theCommandParameters.get("defeatTimerUpdate",0)

			theRampRate = int(theCommandParameters.get("ramp",0))

			if theRampRate:
				if str(self.theIndigoDevice.protocol) == "Insteon":
					# this only works on Insteon Devices
					rampCommand = theCommandParameters.get("rampOverrideCommand",0)

					if rampCommand == 0:
						if self.theIndigoDevice.version in [0x44, 0x45, 0x48]:
							# The above firmware tested and work with the following command
							rampCommand = 0x34		# (52  mmComm_Insteon.kInsteonBrightenWithRamp2)
						elif self.theIndigoDevice.version in [0x38, 0x40, 0x41, 0x43]:
							# The above firmware tested and work with the following command
							rampCommand = 0x2E		# (46 mmComm_Insteon.kInsteonBrightenWithRamp)
						else:
							rampCommand = 0  # Ramp is untested and assumed unsupported for this firmware version
							mmLib_Log.logError("### Unknown insteon Firmware version " + str(self.theIndigoDevice.version) + " for device " + self.deviceName + " while attempting BrightenWithRamp. Defaulting to standard Brighten function.")

					mmLib_Log.logForce("### RampCommand " + str(rampCommand) + " for device " + self.deviceName)

					if rampCommand:
						# Use Ramp command

						self.sendRawInsteonCommandLow([rampCommand,self.makeRampCmdModifier(theValue, theRampRate)], False, 0, False)		# light ON with Ramp (see //_Documentation/InsteonCommandTables.pdf)

						if theValue == 0:
							# Only if we are trying to dim to 0... for some reason, dimming doesnt go down to 0, it goes to 6. Finish up the last dimming step at the end of the ramp cycle
							# Note this will also fix the other problem below where the device status will not become updated. So you dont need to do both.
							mmLib_Low.registerDelayedAction({'theFunction': self.completeAutonomousDimming,
															 'timeDeltaSeconds': theRampRate + 60,
															 'theDevice': self.deviceName,
															 'timerMessage': "completeAutonomousDimming"})
						else:
							# update the periodicStatusUpdateRequest to make sure the brightness gets updated in indigo when the brightening concludes.
							# since this is a dimmer device, we know this function exists
							# Note: Added +60 to theRampRate below because sometimes periodicStatusUpdateRequest was being called before the ramp was complete
							mmLib_Low.registerDelayedAction( {	'theFunction': self.periodicStatusUpdateRequest,
																'timeDeltaSeconds': theRampRate + 60,
																'theDevice': self.deviceName,
																'timerMessage': "periodicStatusUpdateRequest"})

						# We are done with an async ramp command. Bail out
						return 0
				else:
					mmLib_Log.logWarning("### brightenDevice RampRate only supported on Insteon Dimmers. Reverting to standard Brightness command for device. Class " + str(self.theIndigoDevice.__class__) + " not equal to " + str(indigo.DimmerDevice) + " " + self.deviceName)

			# Its a dimmer device, but One way or another we didnt do a brightness command - use traditional set brightness command
			indigo.dimmer.setBrightness(self.devIndigoID, value=theValue)

		else:
			# not a dimmer device... do an on/off command
			if self.debugDevice: mmLib_Log.logForce( "brightenDevice for " + self.deviceName + " not a dimmer device. It is " + str(self.theIndigoDevice.__class__) + ". Defaulting to onOff")
			self.onOffDevice(theCommandParameters)


		return 0		# continue as normal (no dequeue)

	#
	# SetBrightnewss - Same as above but uses tiers and brightness-step to raise and lower brightness
	#					This is necessary because once you send a ramp command to a dimmer (and we have been defaulting to a 360 second ramp), it will not
	#					Respond to any commands until the ful 360 seconds. Using the timers, we sent an instant discreet ramp-up or ramp-down command every 10 seconds
	#					The dimmer remains fully responsive during this process
	#
	#					if 'ramp' command is requested ('ramp' <> 0) in the commandparameters, it will do a ramp-step over time utilizing timer functions
	#					the timing of each step will be 1 and 4 timerQueue cycles... i.e. int(random.randint(1, 4)) * mmLib_Low.TIMER_QUEUE_GRANULARITY
	#
	def brightenDevice(self, theCommandParameters):


		rampCommand = theCommandParameters.get("rampOverrideCommand", 0)

		# cancel continueDimming timer if its already running. All brighten commands override the ramp timer
		mmLib_Low.cancelDelayedAction(self.continueDimming)

		# We dont support RampComand in this proc, if we found one, use the old proc above.
		if rampCommand: return(self.brightenDeviceOld(theCommandParameters))

		if self.debugDevice: mmLib_Log.logForce( "brightenDevice for " + self.deviceName + " CommandParameters: " + str(theCommandParameters))

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return 'unresponsive'

		try:
			theValue = int(theCommandParameters['theValue'])
		except:
			mmLib_Log.logError("brightenDevice - Must specify a value for: " + self.deviceName)
			return 'brightenDevice: required parameter not present'


		if self.theIndigoDevice.__class__ == indigo.DimmerDevice:
			mmLib_Log.logDebug("brightenDevice - theCommand Value: " + str(theValue))

			self.defeatTimerUpdate = theCommandParameters.get("defeatTimerUpdate",0)

			theRampRate = int(theCommandParameters.get("ramp",0))

			if theRampRate:
				if str(self.theIndigoDevice.protocol) == "Insteon":
					# this only works on Insteon Devices
					currentBrightness = int(self.theIndigoDevice.states['brightnessLevel'])

					if currentBrightness > theValue:
						directionOfChange = mmComm_Insteon.kInsteonDecreaseBrightness
					elif currentBrightness < theValue:
						directionOfChange = mmComm_Insteon.kInsteonIncreaseBrightness
					else:
						# no change needed. Bail
						if self.debugDevice: mmLib_Log.logForce("brightenDevice for " + self.deviceName + " No brightness change requested. Exiting with \'Dque\'.")
						return 'Dque'

					#self.queueCommand({'theCommand': 'sendRawInsteonCommand', 'theDevice': self.deviceName, 'ackWait': 1,'cmd1': int(theCommandParameters['UpOrDown']), 'cmd2': 0, 'retry': 0})
					# Do the initiel ramp step
					try:
						self.sendRawInsteonCommandLow([int(directionOfChange), 0], False, 0, False)  # step light brightness (either up or down)
						self.queueCommand({'theCommand': 'sendStatusRequest', 'theDevice': self.deviceName, 'theValue': 996,'retry': 0})
					except:
						mmLib_Log.logWarning("sendRawInsteonCommandLow command " + str(directionOfChange) + " failed for device " + self.deviceName)

					mmLib_Low.registerDelayedAction({'theFunction': self.continueDimming,
													 'timeDeltaSeconds': int((random.randint(1, 4)) * mmLib_Low.TIMER_QUEUE_GRANULARITY),
													 'theDevice': self.deviceName,
													 'targetBrightness':theValue,
													 'UpOrDown': directionOfChange,
													 'timerMessage': "continueDimming"})

					# We are done with an async ramp command. Bail out
					return 0
				else:
					mmLib_Log.logWarning("### brightenDevice RampRate only supported on Insteon Dimmers. Reverting to standard Brightness command for device. Class " + str(self.theIndigoDevice.__class__) + " not equal to " + str(indigo.DimmerDevice) + " " + self.deviceName)

			# Its a dimmer device, but Ramp command was not requested - use traditional set brightness command
			indigo.dimmer.setBrightness(self.devIndigoID, value=theValue)

		else:
			# not a dimmer device... do an on/off command
			if self.debugDevice: mmLib_Log.logForce( "brightenDevice for " + self.deviceName + " not a dimmer device. It is " + str(self.theIndigoDevice.__class__) + ". Defaulting to onOff")
			self.onOffDevice(theCommandParameters)


		return 0		# continue as normal (no dequeue)



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

		return 0

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


		try:
			theMMDeviceName = theCommandParameters['theDevice']
		except:
			mmLib_Log.logError("No device Name given")
			return 0

		try:
			theMMDevice = mmLib_Low.MotionMapDeviceDict[theMMDeviceName]
		except:
			mmLib_Log.logError(" No MM Device Named \"" + theMMDeviceName + "\".")
			return 0

		try:
			theMMDevice.validateCommand(theCommandParameters['theCommand'])
			# note: check for valid parameters eventually when the command actually gets dispatched
		except:
			mmLib_Log.logForce(theMMDevice.deviceName + " Command \"" + str(theCommandParameters) + "\" could not be queued. NO HANDLER")
			return 0

		# note: The following can't fail. However if the queue was previously empty, the command will execute which may fail.
		#    we dont have this in a try statement because we dont want to mask the failures, we want to fix them (as they present themselves as errors)

		if "NoFlush" in theCommandParameters:
			mmLib_CommandQ.enqueQ(theMMDevice, theCommandParameters, 0)
		else:
			mmLib_CommandQ.enqueQ(theMMDevice, theCommandParameters, ['theCommand'])


		return 1


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
		if self.debugDevice: mmLib_Log.logForce("onOff " + self.deviceName + ". theCommand Value: " + str(theValue))

		try:
			defeatTimerUpdateParm = theCommandParameters["defeatTimerUpdate"]
		except:
			defeatTimerUpdateParm = 0

		self.defeatTimerUpdate = defeatTimerUpdateParm

		if int(theValue) != 0:
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
						mmLib_Log.logVerbose("=== Command Complete... "+ self.deviceName + " No Value Found")

				try:
					repeatVal = int(qHead["repeat"])
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
