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
import mmLib_Events
import mmComm_Insteon
import mmObj_OccupationGroup
import mmComm_Indigo
#from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
import random
import datetime

kLoadDeviceTimeSeconds = 60
kBlackOutTimeSecondsAfterOff = 10

######################################################
#
# mmLoad - Load Device, usually a Dimmer or Switch
#
######################################################
class mmLoad(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):

		super(mmLoad, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.unoccupationDelay = int(theDeviceParameters["unoccupationDelay"]) * 60			# its defined in config file in minutes... keep it handy in seconds
			self.specialFeatures = theDeviceParameters["specialFeatures"].split(';')			# Can be a list, split by semicolons... normalize it into a proper list
			self.daytimeOnLevel = theDeviceParameters["daytimeOnLevel"]							# remember this is a str!
			self.nighttimeOnLevel = theDeviceParameters["nighttimeOnLevel"]						# remember this is a str!
			self.onControllers = [_f for _f in theDeviceParameters["onControllers"].split(';') if _f]  # Can be a list, split by semicolons... normalize it into a proper list
			self.sustainControllers = [_f for _f in theDeviceParameters["sustainControllers"].split(';') if _f]
			self.combinedControllers = self.onControllers + self.sustainControllers							# combinedControllers contain both sustainControllers and onControllers
			if not (self.daytimeOnLevel + self.nighttimeOnLevel) or not len(self.combinedControllers): self.manualControl = 1
			else: self.manualControl = 0
			self.lastOffCommandTime = 0
			self.noMax = 0
			self.allControllerGroups = []
			self.ourNonvolatileData = mmLib_Low.initializeNVDict(self.deviceName)
			self.onControllerName = ""
			self.sustainControllerName = ""


			if 'StatSync' in self.specialFeatures:
				self.StatusType = 'Sync'
			elif 'StatAsync' in self.specialFeatures:
				self.StatusType = 'Async'
			# else it defaults to Off

			if 'noMax' in self.specialFeatures:
				self.noMax = 1	# initialize noMax

			# Initialize automation mode (if applicable)
			if self.debugDevice: mmLib_Log.logForce( "##### " + self.deviceName + " Special features are: " + str(self.specialFeatures) + " ##### ")

			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "AUTOMATICMODE",mmLib_Low.AUTOMATIC_MODE_NOT_POSSIBLE) # this is the most common state by far
			self.ourNonvolatileData["AUTOMATICMODE"] = mmLib_Low.AUTOMATIC_MODE_NOT_POSSIBLE  # in case we ended up with a prior NV value from a previous version of MM

			if 'Automatic' in self.specialFeatures:
				#if it doesn't have a current state saved, initialize it to AUTOMATIC_MODE_ACTIVE
				self.ourNonvolatileData["AUTOMATICMODE"] = mmLib_Low.AUTOMATIC_MODE_ACTIVE	# Always default as ON/Active (if possible)
				if self.debugDevice: mmLib_Log.logForce( self.deviceName + " states that AutomaticMode IS present in special features. AUTOMATICMODE nonvolitile set to: " + self.ourNonvolatileData["AUTOMATICMODE"])
			else:
				#if it doesn't have a current state saved, initialize it to AUTOMATIC_MODE_NOT_POSSIBLE
				if self.debugDevice: mmLib_Log.logForce( self.deviceName + " states that AutomaticMode IS NOT present in special features... defaulting to " + self.ourNonvolatileData["AUTOMATICMODE"])

			# We obsoleted on/off motionsensor support in favor of Occupation events from occupation groups. But to do that, the motion sensors need to be in groups.
			# This transition allows to deal with only one "MotionSensor" (real or virtual) at a time... we dont have to do check loops to see if they all agree on state
			# If there are multiple sensors, the groups will hide that complexity from the Load device, reducing messages and improving performance.
			# However, we dont want to have to clutter up the config file with a bunch of very specific motion sensor groups, so we make them on the fly here.
			#
			# Make OccupationGroup (self.deviceName'_OG') and SustainGroup (self.deviceName'_SG') as necessary
			#

			if theDeviceParameters["onControllers"]:
				if len(self.onControllers) > 1:
					self.onControllerName = 'OG_' + self.deviceName
					mmObj_OccupationGroup.mmOccupationGroup({'deviceType': 'OccupationGroup', 'deviceName': self.onControllerName, 'members': theDeviceParameters["onControllers"],'unoccupiedRelayDelayMinutes': 0, 'debugDeviceMode': theDeviceParameters["debugDeviceMode"]})
				else:
					self.onControllerName = theDeviceParameters["onControllers"]				# This could be null, thats why we have the 'if' below

				if self.onControllerName: self.allControllerGroups.append(self.onControllerName)	# we dont want to append a null

			if theDeviceParameters["sustainControllers"]:
				if len(self.sustainControllers) > 1:
					self.sustainControllerName = 'SG_' + self.deviceName
					mmObj_OccupationGroup.mmOccupationGroup({'deviceType': 'OccupationGroup', 'deviceName': self.sustainControllerName, 'members': theDeviceParameters["sustainControllers"],'unoccupiedRelayDelayMinutes': 0, 'debugDeviceMode': theDeviceParameters["debugDeviceMode"]})
				else:
					self.sustainControllerName = theDeviceParameters["sustainControllers"]				# This could be null, thats why we have the 'if' below

				if self.sustainControllerName: self.allControllerGroups.append(self.sustainControllerName)	# we dont want to append a null

			# All controllers must subscribe to both occupied events and unoccupied.
			# Sustain/On controller differentiation happens inside processOccupationEvent

			if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Subscribing to [\'OccupiedAll\', \'OccupiedPartial\']" + " from " + str(self.allControllerGroups))
			mmLib_Events.subscribeToEvents(['OccupiedAll', 'OccupiedPartial'], self.allControllerGroups, self.processOccupationEvent, {}, self.deviceName)

			if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Subscribing to [\'UnoccupiedAll\']" + " from " + str(self.allControllerGroups))
			mmLib_Events.subscribeToEvents(['UnoccupiedAll'], self.allControllerGroups, self.processUnoccupationEvent, {}, self.deviceName)

			# Load devices with no controllers can stay on forever
			if len(self.allControllerGroups):
				self.maxOnTime = int(60*60*24)		# 24 hour maximum for any device with controllers
			else:
				self.maxOnTime = self.unoccupationDelay				# If no controllers, use occupationDelay as noted in config file notes. If it is 0, the load will stay on forever


			self.companions = []
			mmLib_Low.loadDeque.append(self)						# insert into loadDevice deque
			mmLib_Low.statisticsQueue.append(self)					# insert into statistics deque

			random.seed()
			initialStatusRequestTimeDelta = random.randint(60,660)		# somewhere between 1 to 11 minutes from now
			#mmLib_Log.logForce("### TIMER " + self.deviceName + " Will send Status Request in " + str(round(initialStatusRequestTimeDelta/60.0,2)) + " minutes.")

			mmLib_Low.registerDelayedAction({'theFunction': self.periodicStatusUpdateRequest, 'timeDeltaSeconds': initialStatusRequestTimeDelta, 'theDevice': self.deviceName, 'timerMessage': "periodicStatusUpdateRequest"})
			self.supportsWarning = 0
			if 'flash' in self.specialFeatures:
				self.supportsWarning = 'flash'
			elif 'beep' in self.specialFeatures:
				self.supportsWarning = 'beep'


			# update commands and events

			self.supportedCommandsDict.update({'setAutomaticMode':self.setAutomaticMode, 'devStatus':self.devStatus, 'queueBeepDevice':self.queueBeepDevice})

			mmLib_Events.subscribeToEvents(['isNightTime','isDayTime'], ['MMSys'], self.mmDayNightTransition, {}, self.deviceName)
			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.completeInit, {}, self.deviceName)
			
			# register for update events
			if self.theIndigoDevice.__class__ == indigo.DimmerDevice:
				if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Is Subscribing to event \'AttributeUpdate\' as dimmer with handlerDefinedData of " + str({'monitoredAttributes':{'onState':0, 'brightness':0}}))
				mmLib_Events.subscribeToEvents(['AttributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes':{'onState':0, 'brightness':0}} , self.deviceName)
			else:
				if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Is Subscribing to event \'AttributeUpdate\' as switch with handlerDefinedData of " + str({'monitoredAttributes':{'onState':0}}))
				mmLib_Events.subscribeToEvents(['AttributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes':{'onState':0}} , self.deviceName)

			# register for command events
			mmLib_Events.subscribeToEvents(['DevRcvCmd'], ['Indigo'], self.receivedCommandEvent, {} , self.deviceName)
			mmLib_Events.subscribeToEvents(['DevCmdComplete'], ['Indigo'], self.completeCommandEvent, {} , self.deviceName)
			mmLib_Events.subscribeToEvents(['DevCmdErr'], ['Indigo'], self.errorCommandEvent, {} , self.deviceName)


	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################

	#
	# deviceUpdatedEvent -
	#
	#
	# deviceUpdatedEvent - tell the companions what to do
	#
	def deviceUpdatedEvent(self, eventID, eventParameters):


		# 'na' below means no change if either onstate or brightness changed, processCompanions
		newBrightnessState = eventParameters.get('brightness', 'na')
		newOnState = eventParameters.get('onState', 'na')
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " update. Event: " + str(eventParameters) + " NewOnState = " + str(newOnState))
		processCompanions = 0

		if self.defeatTimerUpdate:
			mmLib_Log.logVerbose(self.deviceName + " processing " + str(self.defeatTimerUpdate) + " command, not updating timers and resetting flash flag.")
			self.defeatTimerUpdate = 0
		else:
			if newBrightnessState != 'na' or newOnState != 'na':
				processCompanions=1
				if newOnState == False:
					# We are not flashing (indicated by defeatTimerUpdate), an newOnState is now off, so the device was turned off, clear the off timers
					self.forceControllerTimeouts()

		if 0:
			# do automaticMode reset if needed. If a device is turned on bring it back online (auto mode on)
			if newOnState == True and self.ourNonvolatileData["AUTOMATICMODE"] == mmLib_Low.AUTOMATIC_MODE_SLEEP:
				self.ourNonvolatileData["AUTOMATICMODE"] = mmLib_Low.AUTOMATIC_MODE_ACTIVE
				mmLib_Log.logReportLine("Since a device has been turned on... Setting Online Mode to " + mmLib_Low.AUTOMATIC_MODE_ACTIVE + " for device: " + self.deviceName)
				self.setControllersOnOfflineState(mmLib_Low.AUTOMATIC_MODE_ACTIVE)


		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " checking processCompanions, OnState: " + str(newOnState) + " Brightness State: " + str(newBrightnessState) + " processCompanions: " + str(processCompanions) + " Companions: " + str(self.companions))

		# process companions as needed
		if processCompanions and self.companions:
			if self.debugDevice: mmLib_Log.logForce("Updated loadDevice: " + self.deviceName + ". " + " Value: " + str(self.getBrightness()) + " Send commands to companions: " + str(self.companions))
			initialBrightness = self.getBrightness()
			for theCompanion in self.companions:
				# debounce the command, dont send it if the value is already correct
				if theCompanion.getBrightness() == initialBrightness :
					mmLib_Log.logVerbose("Device: " + theCompanion.deviceName + " already has the appropriate value: " + str(initialBrightness))
					mmLib_CommandQ.flushQ(theCompanion, {'theDevice':theCompanion.deviceName,'theCommand': 'brighten'}, ["theCommand"])
				else:
					theCompanion.queueCommand({'theCommand':'brighten', 'theDevice':theCompanion.deviceName, 'theValue':initialBrightness, 'retry':2})

		super(mmLoad, self).deviceUpdatedEvent(eventID, eventParameters)	# Do universal housekeeping
		return(0)



	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	def completeCommandEvent(self, eventID, eventParameters ):
		super(mmLoad, self).completeCommandEvent(eventID, eventParameters)	# Nothing special here, forward to the Base class

	#
	# receivedCommand - we received a command from our device. The base object will do most of the work... we want to process special commands here, like auto mode mode
	#
	def receivedCommandEvent(self, eventID, eventParameters ):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " received command event from \'" + eventParameters['publisher'] + "\'.")

		mmLib_Low.cancelDelayedAction(self.continueDimming)

		theInsteonCommand = eventParameters['cmd']

		# if it was an off or fast off, clear the command queue, no other commands are important that are waiting
		#


		#
		# do the normal processing
		# ========================
		super(mmLoad, self).receivedCommandEvent(eventID, eventParameters)  			# execute Base Class
		mmLib_Log.logVerbose("Check for Automatic mode: " + self.deviceName)

		#
		# do the special processing
		# ========================

		try:
			theCommandByte = theInsteonCommand.cmdBytes[0]
		except:
			theCommandByte = 0

		########################################################
		# The following is necessary for automaticMode function (sometimes called sleep mode, or bedtime mode).
		# The concept is that if you have an automatic light in a light-sensitive area (like a bedroom), sometimes you may want to
		# turn off automatic processing (motion -> light activation). Effectively this simply disables the controller by putting it offline.
		# The user activates this special mode by double-clicking-off the light switch in question. If the light supports automaticmode,
		# an MMCommand is sent to the device (this mmLogic_Load.py file) which in-turn sends all of its controllers am OffLine command
		# to put the controllers to sleep. The controllers can be in one of 4 modes:
		#
		#		mmLib_Low.AUTOMATIC_MODE_NOT_POSSIBLE = this device does not support Auto Mode selection (this is the normal case for all load devices)
		#		mmLib_Low.AUTOMATIC_MODE_ACTIVE = this device supports automatic mode selection but is currently behaving in the standard sense
		#		mmLib_Low.AUTOMATIC_MODE_SLEEP = this device is currently sleping (offline) until morning or user interaction with the switch
		#		mmLib_Low.AUTOMATIC_MODE_OFFLINE = this device is offline and will remain so until manually brought online (does not react to dawn)
		#
		########################################################
		if self.debugDevice: mmLib_Log.logForce("### " + self.deviceName + " Automatic Mode is: " + self.ourNonvolatileData["AUTOMATICMODE"] + "  ###")

		if self.ourNonvolatileData["AUTOMATICMODE"] != mmLib_Low.AUTOMATIC_MODE_NOT_POSSIBLE:
			if self.debugDevice: mmLib_Log.logForce( "### " + self.deviceName + " Processing Automatic Mode. Current Mode is: " + self.ourNonvolatileData["AUTOMATICMODE"] + ". Command Byte is: " + str(theCommandByte) + " ###")

			if self.ourNonvolatileData["AUTOMATICMODE"] == mmLib_Low.AUTOMATIC_MODE_ACTIVE:
				# the device is capable of sleeping, but is not currently doing so
				# look for automaticMode activation  (double click off)
				# mmComm_Insteon.kInsteonOffFast = 20
				if theCommandByte == mmComm_Insteon.kInsteonOffFast :
					if self.debugDevice: mmLib_Log.logForce("### " + self.deviceName + " Off Fast Detected Putting device to sleep ###")
					self.setAutomaticMode( {'theCommand':'setAutomaticMode', 'theDevice':self.deviceName, 'newMode':mmLib_Low.AUTOMATIC_MODE_SLEEP, 'silent':'no'} )
					if self.debugDevice: mmLib_Log.logForce("### " + self.deviceName + " SetAutomaticMode Done. New Mode is: " + self.ourNonvolatileData["AUTOMATICMODE"] + "  ###")

			elif self.ourNonvolatileData["AUTOMATICMODE"] == mmLib_Low.AUTOMATIC_MODE_SLEEP:
				if self.debugDevice: mmLib_Log.logForce("### " + self.deviceName + " Received command while device is sleeping ###")
				# the device is sleeping, look for wake-up commands
				if theCommandByte == mmComm_Insteon.kInsteonOn or theCommandByte == mmComm_Insteon.kInsteonOnFast:
					if self.debugDevice: mmLib_Log.logForce("### " + self.deviceName + " Light turning on while asleep. Calling setAutomaticMode ###")
					self.setAutomaticMode( {'theCommand':'setAutomaticMode', 'theDevice':self.deviceName, 'newMode':mmLib_Low.AUTOMATIC_MODE_ACTIVE, 'silent':'no'} )
					if self.debugDevice: mmLib_Log.logForce("### " + self.deviceName + " SetAutomaticMode Done. New Mode is: " + self.ourNonvolatileData["AUTOMATICMODE"] + " ###")

		########################################################
		#         End of AutomaticMode processing              #
		########################################################


		#
		# Load devices also help the motion sensors calculate dead batteries by notifying them when a user is in a room pressing buttons
		# So, here we notify all controllers that the manual switch was turned on or off... That way the controllers can keep their own tally.
		# If the Tally gets too high, the motion sensor may decide that its battery os low. and needs to be changed - a log entry to that effect
		# will be generated in the battery report
		#


		if theCommandByte == mmComm_Insteon.kInsteonOn or theCommandByte == mmComm_Insteon.kInsteonOnFast:	#kInsteonOn = 17, kInsteonOnFast = 18

			# notify the motion sensors of the on event
			for member in self.allControllerGroups:
				if not member: break
				memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
				if memberDev:
					if self.debugDevice: mmLib_Log.logForce( self.deviceName + " sending loadDeviceNotificationOfOn to \'" + member + "\'.")
					memberDev.loadDeviceNotificationOfOn()

		# the following was obsoleted... it is now processed in deviceUpdatedEvent above

		#elif theCommandByte == mmComm_Insteon.kInsteonOff or theCommandByte == mmComm_Insteon.kInsteonOffFast:

			# Now defeat any pending unoccupation events from our controllers

		#	self.forceControllerTimeouts()

		return(0)


	#
	# Now defeat any pending unoccupation events from our controllers

	def forceControllerTimeouts(self):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " processing forceControllerTimeouts")

		# defeat the motion sensors for a couple seconds to keep the light from coming back on immediately
		self.lastOffCommandTime = int(time.mktime(time.localtime()))

		for member in self.allControllerGroups:
			if not member: break
			memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
			if memberDev:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " sending forceTimeout to \'" + member + "\'.")
				memberDev.forceTimeout(kBlackOutTimeSecondsAfterOff)

		return(0)

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#	We dont do anything special here, so it will be handled by the base class
	#




	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	# queueBeepDevice - Beep the device as requested.
	#
	def queueBeepDevice(self, theCommandParameters ):

		mmLib_Log.logForce("===== Issuing Single Beep Command to " + self.deviceName + ".")
		self.queueCommand({'theCommand':'beep', 'theDevice':self.deviceName, 'theValue':100, 'repeat':0, 'retry':0})

		return(0)

	#
	# setAutomaticMode - set automation mode Auto or Manual as requested.
	#
	def setAutomaticMode(self, theCommandParameters ):
		requestedMode = theCommandParameters["newMode"]
		try:
			silent = theCommandParameters["silent"]
		except Exception as exception:
			silent = 'yes'		#default - no noise

		mmLib_Log.logForce("===== setAutomaticMode being called for " + self.deviceName + "with request mode of " + requestedMode + ", NonVolatile AUTOMATICMODE is: " + self.ourNonvolatileData["AUTOMATICMODE"] + ".")

		# Basically this routine just turns the device online or offline state. However, it's
		# called BedtimeMode because it has automatic features to turn set the device back to online at daybreak

		theResult = 0
		if self.ourNonvolatileData["AUTOMATICMODE"] != mmLib_Low.AUTOMATIC_MODE_NOT_POSSIBLE and requestedMode != self.ourNonvolatileData["AUTOMATICMODE"]:
			self.setAutomaticModeLow(requestedMode)

			if requestedMode == mmLib_Low.AUTOMATIC_MODE_SLEEP:
				# if we are going sleep mode... turn off the light:
				self.queueCommand({'theCommand':'brighten', 'theDevice':self.deviceName, 'theValue':0, 'retry':2})
				if silent != 'yes':
					self.queueCommand({'theCommand': 'beep', 'theDevice': self.deviceName, 'theValue': 0, 'repeat': 1, 'retry': 0})
			elif requestedMode == mmLib_Low.AUTOMATIC_MODE_ACTIVE:
				if silent != 'yes':
					self.queueCommand({'theCommand': 'beep', 'theDevice': self.deviceName, 'theValue': 0, 'repeat': 0, 'retry': 0})

			# update nv file so we know we are supposed to be in automatic mode if the server restarts during the night
			mmLib_Low.cacheNVDict()		# make the NV variables permanent
		else:
			if self.debugDevice: mmLib_Log.logForce( "=============== " + self.deviceName + "'s automatic mode is already set to "+ self.ourNonvolatileData["AUTOMATICMODE"] + ".")

		return(theResult)


	#
	# 	devStatus - print the status of the device
	#
	def devStatus(self, theCommandParameters):

		theResult = self.deviceMotionStatus()
		return(theResult)

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self,eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce( self.deviceName + " completeInit. automaticMode NV Value is " + str(self.ourNonvolatileData["AUTOMATICMODE"]))

		# If the device is ON, but the associated Motion Sensors say it should be off, turn it off.
		# But, do it in a few seconds to give the motion sensors and groups a chance to settle

		if self.theIndigoDevice.onState == True and self.maxOnTime:			# maxOnTime to indicate that the device has controllers
			mmLib_Low.registerDelayedAction({'theFunction': self.completeInit2,
											 'timeDeltaSeconds': 10,
											 'theDevice': self.deviceName,
											 'timerMessage': "completeInit2"})

		return 0

	#
	# completeInit - Complete the initialization process for this device (Part 2)
	# we gave all motion devices a chance to settle..  now lets see if we should turn ourselves off
	#
	def completeInit2(self, parameters):

		if not self.manualControl:
			# Do this only if it's an automatic load device (has motion sensors)
			# If the device is ON, but the associated Motion Sensors say it should be off, turn it off.
			try:
				for member in self.allControllerGroups:
					if not member: return 0
					memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
					if memberDev:
						occupiedStateResult = memberDev.getOccupiedState()
						if self.debugDevice: mmLib_Log.logForce( self.deviceName + " called " + member + ".getOccupiedState with a result of " + str(occupiedStateResult))
						if memberDev.getOccupiedState() != 'UnoccupiedAll': return 0	# at least one member is occupied, so being ON now is fine
					else:
						mmLib_Log.logWarning(self.deviceName + " found no mmDevice called " + member + " while trying to access getOccupiedState")
						return(0)

					# if we got here all members are showing unoccupied, turn off our device

				if self.debugDevice: mmLib_Log.logForce( "Turning deivce " + self.deviceName + " off as all controllers are reporting Unoccupied")
				self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': 0, 'retry': 2})

		# GB Fix me... If the motions say 'ON' and we are 'OFF' then what?

			except Exception as exception:
				mmLib_Log.logWarning( self.deviceName + " Error: " + str(exception))

		return 0

	#
	#	processOccupationEvent(theEvent, eventParameters) - when a controller, (usually a motion sensor) has an event, it sends the event to a loaddevice through this routine
	#
	#	theHandler format must be
	#		theHandler(theEvent, eventParameters) where:
	#
	#		theEvent is the text representation of a single event type listed above: we handle ['OccupiedAll', 'OccupiedPartial'] here only
	#		eventParameters is a Dict with the following:
	#
	# thePublisher				The name of the Registered publisher (see above) who is sending the event
	# theEvent					The text name of the event to be sent (see subscribeToEvents below)
	# theSubscriber				The Text Name of the Subscriber to receive the event
	# publisherDefinedData		Any data the publisher chooses to include with the event (for example, if it
	# 								is an indigo command event, we might include the whole indigo command record here)
	# timestamp					The time (in seconds) the event is being published/distributed
	#
	def processOccupationEvent(self, theEvent, eventParameters):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " received \'" + theEvent + "\' Event: " + str(eventParameters))

		newOffTimerType = 'none'
		theControllerDev = mmLib_Low.MotionMapDeviceDict[eventParameters['publisher']]

		# if we are currently not processing motion events, bail early
		if indigo.variables['MMDefeatMotion'].value == 'true': return(0)

		# Blackout processing. This is when we ignore motion sensing immediately after a light turning off. Tzhe reason is that in most cases, after you
		# manually turn off a light, you stiull have to move through the room to leave (setting off the motion sensor again). We want to avoid the light
		# coming on right after turning it off, so we skip this motion detection in a specified blackout period (kBlackOutTimeSecondsAfterOff).

		defeatBlackout = int(eventParameters.get('defeatBlackout',0))
		if self.debugDevice: mmLib_Log.logForce( self.deviceName + " ****** DefeatBlackout is " + str(defeatBlackout))
		if defeatBlackout:
			if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Skipping blackout debouncing because DefeatBlackout is " + str(defeatBlackout))
		else:
			if self.lastOffCommandTime and int(time.mktime(time.localtime())) - self.lastOffCommandTime < kBlackOutTimeSecondsAfterOff:
					mmLib_Log.logForce( "=== " + self.deviceName + " is ignoring /'" + theEvent + "/' controller event from " + theControllerDev.deviceName + " " + str(int(time.mktime(time.localtime())) - self.lastOffCommandTime) + " seconds after user off command.")
					return(0)

		mmLib_Log.logVerbose(self.deviceName + " is being asked to process \'" + theEvent + "\' event by " + theControllerDev.deviceName)

		# none of the delay callbacks are valid now
		mmLib_Low.cancelDelayedAction(self.offDelayCallback)
		mmLib_Low.cancelDelayedAction(self.offCallback)

		# if are only sustaining, bail out before processing an ON command
		if eventParameters['publisher'] != self.onControllerName:
			if self.debugDevice: mmLib_Log.logForce("    " + eventParameters['publisher'] + " is not the ON controller. Processing as Sustain. Event complete.")
			return(0)
		else:
			if self.debugDevice: mmLib_Log.logForce("    " + eventParameters['publisher'] + " is the ON controller. Continue processing OccupationEvent. Current onState is " + str(self.theIndigoDevice.onState) + " Automatic Mode is "+ str(self.ourNonvolatileData["AUTOMATICMODE"]))

		if self.theIndigoDevice.onState == False:
			# the light is off, should we turn it on? Doesnt matter if this is a sustain or ON controller. Just care about automatic mode.
			# I'm not sure this can actually happen if our online state is false (i.e. automatic OFF mode)
			if self.ourNonvolatileData["AUTOMATICMODE"] != mmLib_Low.AUTOMATIC_MODE_SLEEP:	# this includes NA devices (its the default for load devices)
				if self.debugDevice: mmLib_Log.logForce("Debugging Device " + self.deviceName + " while daytime level is " + str(self.daytimeOnLevel) + ". and nightime is " + str(self.nighttimeOnLevel))
				if indigo.variables['MMDayTime'].value == 'true':
					theLevel = self.daytimeOnLevel
				else:
					theLevel = self.nighttimeOnLevel

				if self.debugDevice: mmLib_Log.logForce("Debugging Device " + self.deviceName + " while MMDayTime is " + str(indigo.variables['MMDayTime'].value) + ". New Level requested is " + str(theLevel))

				if int(theLevel) > 0:
					if self.debugDevice: mmLib_Log.logForce("    " + self.deviceName + " processing set brightness level to " + theLevel)
					self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': theLevel, 'retry': 2})

		return 0

	def processSustainEvent(self, theEvent, eventParameters):

		return 0

	#
	#	processUnoccupationEvent(theEvent, eventParameters) - when a controller, (usually a motion sensor) has an event, it sends the event to a loaddevice through this routine
	#
	#	theHandler format must be
	#		theHandler(theEvent, eventParameters) where:
	#
	#		theEvent is the text representation of a single event type listed above: we handle ['UnoccupiedAll'] here only
	#		eventParameters is a Dict with the following:
	#
	# thePublisher				The name of the Registered publisher (see above) who is sending the event
	# theEvent					The text name of the event to be sent (see subscribeToEvents below)
	# theSubscriber				The Text Name of the Subscriber to receive the event
	# publisherDefinedData		Any data the publisher chooses to include with the event (for example, if it
	# 								is an indigo command event, we might include the whole indigo command record here)
	# timestamp					The time (in seconds) the event is being published/distributed
	#
	def processUnoccupationEvent(self, theEvent, eventParameters):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " received \'" + theEvent + "\' Event: " + str(eventParameters))


		if self.theIndigoDevice.onState == True:

			# the Device is on, turn it off, but ponly if both ON and sustain groups are unoccupied
			if len(self.listOccupiedControllers(self.allControllerGroups, True)):
				if self.debugDevice: mmLib_Log.logForce( "    There are one or more occupied controllers remaining. No Action Taken.")
				return 0

			if self.unoccupationDelay:
				# do it after the suitable delay
				mmLib_Low.registerDelayedAction({'theFunction': self.offDelayCallback, 'timeDeltaSeconds': self.unoccupationDelay, 'theDevice': self.deviceName, 'timerMessage': "offDelayCallback"})
			else:
				# do it now
				self.offDelayCallback({})
		else:
			# none of the delay callbacks are valid now
			mmLib_Low.cancelDelayedAction(self.offDelayCallback)
			mmLib_Low.cancelDelayedAction(self.offCallback)

		return 0

	#
	# 	offDelayCallback - We received an Unoccupied event, then had a timer delay, but now we are done... the light needs to go off
	#	but before we turn it off... check to see if there are any beep or flash warnings that need to happen
	#
	def offDelayCallback(self, parameters):

		if self.theIndigoDevice.onState == True:

			# the Device is on, turn it off

			if self.supportsWarning not in ['flash', 'beep']:
				# no warning, just off
				self.offCallback({})
			else:
				if self.supportsWarning == 'flash':
					self.queueCommand({'theCommand': 'flash', 'theDevice': self.deviceName, 'theValue': 0,
									   'defeatTimerUpdate': 'flash', 'retry': 2})
				elif self.supportsWarning == 'beep':
					self.queueCommand(
						{'theCommand': 'beep', 'theDevice': self.deviceName, 'theValue': 0, 'repeat': 1, 'retry': 2})
				# now set a timeout for the reall off command
				mmLib_Low.registerDelayedAction( {'theFunction': self.offCallback, 'timeDeltaSeconds': 60, 'theDevice': self.deviceName, 'timerMessage': "offCallback"})
		else:
			mmLib_Log.logWarning( self.deviceName + " is concluding its off delay and is trying to turn off, but its not on.")

		return 0

	#
	# 	offCallback - We received an Unoccupied event, then may have had a timer delay and a flash/beep, but now we are done... the light goes off now
	#
	def offCallback(self, parameters):

		# warnings are finished... actually turn off the device now
		self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': 0, 'retry': 2})

		return 0





	#
	# 	listOccupiedControllers - return a list of controllers that are on
	#
	def listOccupiedControllers(self, checkControllers, full):

		theList = []

		if checkControllers:

			for devName in checkControllers:
				theController = mmLib_Low.MotionMapDeviceDict.get(devName, 0)
				if theController and theController.onlineState == mmLib_Low.AUTOMATIC_MODE_ACTIVE and theController.occupiedState == True:
					if full:
						theList.append(str(theController.deviceName + " - " + mmLib_Low.getIndigoVariable(theController.occupationIndigoVar, "unknown reason")))
					else:
						theList.append(theController.deviceName)

		return theList

	#
	# setControllersOnOfflineState - for all of our controllers
	#	We actually put the controller offline because the load device (switch) is the UI for the controller(motion sensor)
	#	its the only way to put the motion sensor to sleep for other devices (Water pump and HVAC for example)
	#

	def setControllersOnOfflineState(self,requestedState):

		if requestedState == mmLib_Low.AUTOMATIC_MODE_SLEEP:
			# we dont support bringing everything offline at once
			theList = [self.onControllerName]
		else:
			# we do support bringing everything online at once
			theList = self.allControllerGroups

		for member in theList:
			if not member: break
			memberDev = mmLib_Low.MotionMapDeviceDict.get(member,0)
			if memberDev:
				if self.debugDevice: mmLib_Log.logForce( "#### " + self.deviceName + " is asking "+ str(memberDev.deviceName) + " to adopt an onoffline state of " + requestedState + ".")
				memberDev.setOnOffLine(requestedState)

		return(0)

	#
	# getAreaOnState - are any of our controllers currently in an ON state?
	#
	def getAreaOnState(self, theControllers):

		for otherControllerName in theControllers:
			if not otherControllerName: break
			theController = mmLib_Low.MotionMapDeviceDict.get(otherControllerName,0)
			if theController:
				if theController.getOnState():
					return (otherControllerName + " is ON")
		return(False)

	#
	# getAreaOccupiedState - are any of our controllers currently in an occupied state?
	#
	def getAreaOccupiedState(self, theControllers):

		# If any of our controllers are "Occupied", return True

		for otherControllerName in theControllers:

			# If one of our Off Timers are running, return "Occupied with that timer value

			scheduledOffTime = mmLib_Low.delayedFunctionKeys.get(self.offDelayCallback,0)
			if not scheduledOffTime:
				scheduledOffTime = mmLib_Low.delayedFunctionKeys.get(self.offCallback,0)
			if scheduledOffTime:
				theTimeString = mmLib_Low.minutesAndSecondsTillTime(scheduledOffTime)
				return(self.deviceName + ":" + " timeout in " + str(theTimeString))

			if not otherControllerName: break
			theController = mmLib_Low.MotionMapDeviceDict.get(otherControllerName,0)
			if theController:
				if theController.onlineState == mmLib_Low.AUTOMATIC_MODE_ACTIVE and theController.occupiedState == True:
					mmLib_Log.logVerbose(otherControllerName + " is is keeping device " + self.deviceName + " on")
					try:
						resultMessage = mmLib_Low.readIndigoVariable(theController.occupationIndigoVar)
					except:
						pass

					if resultMessage != 'n/a': return(otherControllerName + ":" + resultMessage)
					else: return(otherControllerName)

			else:
				mmLib_Log.logWarning(otherControllerName + ", is being referenced by " + self.deviceName + ", however there is no such MotionMap device.")

		return(False)

	#
	# deviceMotionStatus - display the motion status of a device
	#

	def deviceMotionStatus(self):

		theMessage = '\n\n==== DeviceStatus for ' + self.deviceName + '====\n'

		theMessage = theMessage + "\nonControllerName = " + self.onControllerName + "\n sustainControllerName = " + self.sustainControllerName + "\n\n"

		if self.theIndigoDevice.onState == True:
			scheduledOffTime = mmLib_Low.delayedFunctionKeys.get(self.offDelayCallback,0)
			if not scheduledOffTime:
				scheduledOffTime = mmLib_Low.delayedFunctionKeys.get(self.offCallback,0)
			if scheduledOffTime:
				theTimeString = mmLib_Low.minutesAndSecondsTillTime(scheduledOffTime)
				theMessage = theMessage + str("\'" + self.deviceName + "\'" + " is scheduled to turn off in " + str(theTimeString) + ".\n")
			else:
				theMessage = theMessage + str("WARNING " + "\'" + self.deviceName + "\'" + " is on but not scheduled to turn off.\n" )
				onGroup = self.listOccupiedControllers(self.allControllerGroups, True)
				if onGroup: theMessage = theMessage + str("  Related Controllers Reporting Occupied: " + str(onGroup) + "\n")
		else:

			if self.ourNonvolatileData["AUTOMATICMODE"] == mmLib_Low.AUTOMATIC_MODE_ACTIVE:
				onlineMessage = " Online Mode Active."
			else:
				onlineMessage = ""

			theMessage = theMessage + str("\'" + self.deviceName + "\'" + " is not on." + onlineMessage + "\n")

		theMessage = theMessage + mmLib_Low.mmGetDelayedProcsList({'theDevice':self.deviceName})
		theMessage = theMessage + "\n==== DeviceStatus End ====\n"

		mmLib_Log.logReportLine(theMessage)

		return 0

	#
	# 		mmDayNightTransition - process day/night transition
	#
	def mmDayNightTransition(self,eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce( "Processing " + eventID + " for " + self.deviceName)

		#
		if self.ourNonvolatileData["AUTOMATICMODE"] != mmLib_Low.AUTOMATIC_MODE_NOT_POSSIBLE:
			# Note what the last setting was
			restoreAutomaticMode = self.ourNonvolatileData["AUTOMATICMODE"]
		else:
			# automatic mde not possible, dont do anything with this
			restoreAutomaticMode = 0
			
		processBrightness = True		# assume we are going to process brightness (unless the logic below changes this)
		areaIsOccupied = self.getAreaOccupiedState(self.allControllerGroups)

		# If its a manual control device, leave it alone. If the device is off, and the ONController says unoccupied, leave it off
		# In all other cases, process the brightness as indicated above
		if self.manualControl or (self.theIndigoDevice.onState == False and not self.getAreaOnState([self.onControllerName])):
			processBrightness = False
		if self.debugDevice: mmLib_Log.logForce("#######" + self.deviceName + " has processBrightness variable set to " +str(processBrightness) + " at startup.")

		# now get the current Brightness
		try:
			currentBrightness = int(self.theIndigoDevice.states["brightnessLevel"])
		except:
			# Must be an on/off device
			if self.theIndigoDevice.onState == False:
				currentBrightness = 0
			else:
				currentBrightness = 100

		newBrightnessVal = currentBrightness		# assume no change

		if areaIsOccupied:
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " is processing mmDayNightTransition of " + str(eventID) + ". AutomaticMode NonVolitile Value is " + str(self.ourNonvolatileData["AUTOMATICMODE"]))
			if areaIsOccupied:
				if self.debugDevice: mmLib_Log.logForce("       processBrightness is " + str(processBrightness) + ". area is occupied according to " + str(areaIsOccupied) + ". currentBrightness is " + str(currentBrightness))
			else:
				if self.debugDevice: mmLib_Log.logForce("       processBrightness is " + str(processBrightness) + ". area is not occupied. currentBrightness is " + str(currentBrightness))

		# do day/night processing

		if eventID == 'isDayTime':
			#
			#  process night to day transition
			#
			
			# If the device supports automaticmode settings. Its a new day now, so we re-enable automatic
			if restoreAutomaticMode: 
				restoreAutomaticMode = mmLib_Low.AUTOMATIC_MODE_ACTIVE
				
			# special processing... skip if current brightness is already brighter than daytime level

			if areaIsOccupied:
				# special processing... skip if current brightness is already brighter than daytime level
				if int(self.daytimeOnLevel) > 0 and int(currentBrightness) > int(self.daytimeOnLevel):
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Skipping brightness adjustment because current brightness is already brighter than daytime level")
				else:
					newBrightnessVal = self.daytimeOnLevel		# If daytime level is 0, this will force the load device off

		else:
			#
			#  process day to night transition
			#

			if areaIsOccupied:
				# special processing... skip if current brightness is already dimmer than nighttimeOnLevel level
				if int(currentBrightness) and int(currentBrightness) < int(self.nighttimeOnLevel):
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Skipping brightness adjustment because current brightness is already dimmer than nighttimeOnLevel level")
				else:
					newBrightnessVal = self.nighttimeOnLevel

		# do automaticMode reset if needed
		if restoreAutomaticMode:
			# this will turn the device automatic regardless of when it was put offline
			self.setAutomaticModeLow(restoreAutomaticMode)		# Its daytime now, let the controller operate the light again


		# if we are going to process brightness and the current brightness does not match the expected brightness
		# change it

		if 	processBrightness and (int(currentBrightness) != int(newBrightnessVal)):
			if self.debugDevice: mmLib_Log.logForce("Day/Night transition for device: " + self.deviceName + " from brightness " + str(currentBrightness) + " to brightness " + str(newBrightnessVal) + " with ramp 360")
			# use ramp mode 360 to smooth the brightness transition
			self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': newBrightnessVal,'defeatTimerUpdate': 'dayNightTransition','ramp':360, 'retry': 2})
			# while the ramp is happening, we should avoid sending status requests (it stops the ramp)

			# mmLib_Low.delayDelayedAction(self.periodicStatusUpdateRequest, 600)	# delay the delay action 10 minutes ### Note Removed, this is handled in the 'brighten' comand now

			# If we just turned thee off, clear the off timers
			if newBrightnessVal == "0":
				# none of the delay callbacks are valid now
				mmLib_Low.cancelDelayedAction(self.offDelayCallback)
				mmLib_Low.cancelDelayedAction(self.offCallback)


		return 0

	def setAutomaticModeLow(self, newAutomaticMode):
		
		if self.debugDevice: mmLib_Log.logForce("Requesting Offline Mode of " +  newAutomaticMode + " for device: " + self.deviceName)
		self.setControllersOnOfflineState(newAutomaticMode)  # we are turning automatic mode on or off
		# Mark our new nonvolatile state
		self.ourNonvolatileData["AUTOMATICMODE"] = newAutomaticMode

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + "'s Automatic mode has been set to " + newAutomaticMode + ".")

		return 0

	#
	# periodicStatusUpdateRequest - status requests every now and then
	#
	def periodicStatusUpdateRequest(self, parameters):

		self.queueCommand({'theCommand': 'sendStatusRequest', 'theDevice': self.deviceName, 'theValue': 999, 'retry': 2})

		renewalStatusRequestTimeDelta = random.randint(3600, 3600 * 2)	# return timer reset value in seconds (between 1 and 2 hours)

		mmLib_Log.logVerbose("Sent Status Update Request for device: " + self.deviceName + ". Will send another in " + str(round(renewalStatusRequestTimeDelta/60.0, 2)) + " minutes.")

		if self.theIndigoDevice.onState == True and not self.noMax:
			if self.maxOnTime:
				secondsDelta = time.mktime(time.localtime()) - self.lastUpdateTimeSeconds
				if self.maxOnTime < secondsDelta:
					mmLib_Log.logWarning( self.deviceName + " has been on for " + str(datetime.timedelta(seconds=secondsDelta)) + " which exceeds its maximum on-time of " + str(datetime.timedelta(seconds=self.maxOnTime)) + ". It is being forced off.")
					self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': 0, 'retry': 2})

		return renewalStatusRequestTimeDelta

	#
	# deviceTime - do device housekeeping... this should happen once a minute
	#
	#def deviceTime(self):
	#	return 0

