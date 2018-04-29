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
from collections import deque
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
			self.daytimeOnLevel = theDeviceParameters["daytimeOnLevel"]
			self.nighttimeOnLevel = theDeviceParameters["nighttimeOnLevel"]
			self.onControllers = filter(None, theDeviceParameters["onControllers"].split(';'))  # Can be a list, split by semicolons... normalize it into a proper list
			self.sustainControllers = filter(None, theDeviceParameters["sustainControllers"].split(';'))
			self.combinedControllers = self.onControllers + self.sustainControllers							# combinedControllers contain both sustainControllers and onControllers
			self.lastOffCommandTime = 0
			self.allControllerGroups = []
			self.ourNonvolatileData = mmLib_Low.initializeNVDict(self.deviceName)

			# Initialize bedtime mode

			if 'bedtime' in self.specialFeatures:
				mmLib_Low.initializeNVElement(self.ourNonvolatileData, "bedtimeMode", mmLib_Low.BEDTIMEMODE_OFF)	# initialize to its possibe, but off
			else:
				mmLib_Low.initializeNVElement(self.ourNonvolatileData, "bedtimeMode", mmLib_Low.BEDTIMEMODE_NOT_POSSIBLE)

			# We obsoleted on/off motionsensor support in favor of Occupation events from occupation groups. But to do that, the motion sensors need to be in groups.
			# This transition allows to deal with only one "MotionSensor" (real or virtual) at a time... we dont have to do check loops to see if they all agree on state
			# If there are multiple sensors, thie groups will hide that complexity from the Load device, reducing messages and improving performance.
			# However, we dont want to have to clutter up the config file with a bunch of very specific motion sensor groups, so we make them on the fly here.
			#
			# Make OccupationGroup (self.deviceName'_OG') and SustainGroup (self.deviceName'_SG') as necessary
			#

			if theDeviceParameters["onControllers"]:
				if len(self.onControllers) > 1:
					onControllerName = 'OG_' + self.deviceName
					mmObj_OccupationGroup.mmOccupationGroup({'deviceType': 'OccupationGroup', 'deviceName': onControllerName, 'members': theDeviceParameters["onControllers"],'unoccupiedRelayDelayMinutes': 0, 'debugDeviceMode': theDeviceParameters["debugDeviceMode"]})
				else:
					onControllerName = theDeviceParameters["onControllers"]

				if onControllerName: self.allControllerGroups.append(onControllerName)
				if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Subscribing to [\'OccupiedAll\', \'OccupiedPartial\']" + " from " + str([onControllerName]))
				mmLib_Events.subscribeToEvents(['OccupiedAll', 'OccupiedPartial'], [onControllerName], self.processOccupationEvent, {}, self.deviceName)

			if theDeviceParameters["sustainControllers"] or theDeviceParameters["onControllers"]:
				if len(self.sustainControllers) > 1:
					sustainControllerName = 'SG_' + self.deviceName
					mmObj_OccupationGroup.mmOccupationGroup({'deviceType': 'OccupationGroup', 'deviceName': sustainControllerName, 'members': theDeviceParameters["sustainControllers"],'unoccupiedRelayDelayMinutes': 0, 'debugDeviceMode': theDeviceParameters["debugDeviceMode"]})
				else:
					sustainControllerName = theDeviceParameters["sustainControllers"]

				if sustainControllerName: self.allControllerGroups.append(sustainControllerName)
				if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Subscribing to [\'UnoccupiedAll\']" + " from " + str(self.allControllerGroups))
				mmLib_Events.subscribeToEvents(['UnoccupiedAll'], self.allControllerGroups, self.processUnoccupationEvent, {}, self.deviceName)

			# Load devices with no controllers can stay on forever
			if len(self.allControllerGroups):
				self.maxOnTime = int(60*60*24)													# 24 hour maximum for any device with controllers
			else:
				self.maxOnTime = int(0)															# If no controllers, no timeout


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

			self.supportedCommandsDict.update({'bedtimeModeOn':self.bedtimeModeOn, 'devStatus':self.devStatus})

			mmLib_Events.subscribeToEvents(['isNightTime','isDayTime'], ['MMSys'], self.mmDayNightTransition, {}, self.deviceName)
			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.completeInit, {}, self.deviceName)
			
			# register for update events
			if self.theIndigoDevice.__class__ == indigo.DimmerDevice:
				mmLib_Events.subscribeToEvents(['AtributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes':{'onState':0, 'brightness':0}} , self.deviceName)
			else:
				# mmLib_Log.logForce( self.deviceName + " Is Subscribing to event \'AttributeUpdate\' with handlerDefinedData of " + str({'monitoredAttributes':{'onState':0}}))
				mmLib_Events.subscribeToEvents(['AtributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes':{'onState':0}} , self.deviceName)

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

		# do bedtimeMode reset if needed
		if newOnState == True and self.ourNonvolatileData["bedtimeMode"] == mmLib_Low.BEDTIMEMODE_ON:
			self.ourNonvolatileData["bedtimeMode"] = mmLib_Low.BEDTIMEMODE_OFF
			mmLib_Log.logReportLine("Bedtime Mode OFF for device: " + self.deviceName)
			self.setControllersOnOfflineState('on')


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
	# receivedCommand - we received a command from our device. The base object will do most of the work... we want to process special commands here, like bedtime mode
	#
	def receivedCommandEvent(self, eventID, eventParameters ):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " received command event from \'" + eventParameters['publisher'] + "\'.")

		theInsteonCommand = eventParameters['cmd']

		# if it was an off or fast off, clear the command queue, no other commands are important that are waiting
		#


		#
		# do the normal processing
		# ========================
		super(mmLoad, self).receivedCommandEvent(eventID, eventParameters)  			# execute Base Class
		mmLib_Log.logVerbose("Check for bedtime mode: " + self.deviceName)

		#
		# do the special processing
		# ========================

		try:
			theCommandByte = theInsteonCommand.cmdBytes[0]
		except:
			theCommandByte = 0

		# if this device handles bedtimemode, process it now

		if self.ourNonvolatileData["bedtimeMode"] > mmLib_Low.BEDTIMEMODE_NOT_POSSIBLE:

			# look for bedtimeMode activation  (double click off)
			# mmComm_Insteon.kInsteonOffFast = 20
			if theCommandByte == mmComm_Insteon.kInsteonOffFast : self.bedtimeModeOn( {'theCommand':'bedtimeModeOn', 'theDevice':self.deviceName} )

		#
		# Load devices also help the motion sensors calculate dead batteries by notifying them when a user is in a room pressing buttons

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
	#
	#def errorCommandEvent(self, eventID, eventParameters  ):
	#	super(mmHVACCommands, self).errorCommand(theInsteonCommand)	# Nothing special here, forward to the Base class





	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	# bedtimeModeOn - turn bedtime mode on if its Nighttime
	#
	def bedtimeModeOn(self, theCommandParameters ):

		theResult = 0

		#mmLib_Log.logForce( self.deviceName + " is being called to turn on Bedtime mode. Current Mode is: " + str(self.ourNonvolatileData["bedtimeMode"]))

		if self.ourNonvolatileData["bedtimeMode"] == mmLib_Low.BEDTIMEMODE_OFF and indigo.variables['MMDayTime'].value == 'false':
			mmLib_Log.logReportLine("Bedtime Mode ON for device: " + self.deviceName)
			self.ourNonvolatileData["bedtimeMode"] = mmLib_Low.BEDTIMEMODE_ON

			self.setControllersOnOfflineState('bedtime')	# its ok that this command isn't queued, it doesnt send a message just updates state in Indigo
			self.queueCommand({'theCommand':'beep', 'theDevice':self.deviceName, 'theValue':0, 'repeat':1, 'retry':2})
			self.queueCommand({'theCommand':'brighten', 'theDevice':self.deviceName, 'theValue':0, 'retry':2})

			# update nv file so we know we are supposed to be in bedtime mode if the server restarts during the night
			mmLib_Low.cacheNVDict()


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

		if self.debugDevice: mmLib_Log.logForce( self.deviceName + " completeInit. bedtimeMode NV Value is " + str(self.ourNonvolatileData["bedtimeMode"]))

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

		# If the device is ON, but the associated Motion Sensors say it should be off, turn it off.

		try:
			for member in self.allControllerGroups:
				if not member: return 0
				memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
				if memberDev:
					if self.debugDevice: mmLib_Log.logForce( self.deviceName + " calling " + member + ".getOccupiedState")
					if memberDev.getOccupiedState() != 'UnoccupiedAll': return 0	# at least one member is occupied, so being ON now is fine
				else:
					mmLib_Log.logWarning(self.deviceName + " found no mmDevice called " + member + " while trying to access getOccupiedState")
					return(0)

				# if we got here all members are showing unoccupied, turn off our device

			if self.debugDevice: mmLib_Log.logForce( "Turning deivce " + self.deviceName + " off as all coltrollers are reporting Unoccupied")
			self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': 0, 'retry': 2})

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

		if self.lastOffCommandTime and int(time.mktime(time.localtime())) - self.lastOffCommandTime < kBlackOutTimeSecondsAfterOff:
				mmLib_Log.logForce( "=== " + self.deviceName + " is ignoring /'" + theEvent + "/' controller event from " + theControllerDev.deviceName + " " + str(int(time.mktime(time.localtime())) - self.lastOffCommandTime) + " seconds after user off command.")
				return(0)

		mmLib_Log.logVerbose(self.deviceName + " is being asked to process \'" + theEvent + "\' event by " + theControllerDev.deviceName)

		# none of the delay callbacks are valid now
		mmLib_Low.cancelDelayedAction(self.offDelayCallback)
		mmLib_Low.cancelDelayedAction(self.offCallback)

		if self.theIndigoDevice.onState == False:
			# the light is off, should we turn it on? Doesnt matter if this is a sustain or ON controller. Just care about bedtime mode.
			if self.ourNonvolatileData["bedtimeMode"] != mmLib_Low.BEDTIMEMODE_ON:
				if indigo.variables['MMDayTime'].value == 'true':
					theLevel = self.daytimeOnLevel
				else:
					theLevel = self.nighttimeOnLevel

				if int(theLevel) > 0:
					self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': theLevel, 'retry': 2})

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

			# the Device is on, turn it off

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
	def listOccupiedControllers(self, checkControllers):

		mmLib_Log.logForce(self.deviceName + " running listOccupiedControllers")
		theList = []

		if checkControllers:

			for devName in checkControllers:
				theController = mmLib_Low.MotionMapDeviceDict.get(devName, 0)
				if theController and theController.onlineState == 'on' and theController.occupiedState == True:
					theList.append(theController.deviceName)

		mmLib_Log.logForce(self.deviceName + " exit listOccupiedControllers")
		return theList

	#
	# setControllersOnOfflineState - for all of our controllers
	#	We actually put the controller offline because the load device (switch) is the UI for the controller(motion sensor)
	#	its the only wat to put the motion sensor to sleep for other devices (Water pump and HVAC for example)
	#
	def setControllersOnOfflineState(self,requestedState):

		for member in self.allControllerGroups:
			if not member: break
			memberDev = mmLib_Low.MotionMapDeviceDict.get(member,0)
			if memberDev: memberDev.setOnOffLine(requestedState)
		return(0)



	#
	# getAreaOccupiedState - are any of our controllers currently in an occupied state?
	#
	def getAreaOccupiedState(self, theControllers):

		# If any of our controllers are "Occupied", return True

		for otherControllerName in theControllers:
			if not otherControllerName: break
			theController = mmLib_Low.MotionMapDeviceDict.get(otherControllerName,0)
			if theController and theController.onlineState == 'on' and theController.occupiedState == True:
				mmLib_Log.logVerbose(otherControllerName + " is is keeping device " + self.deviceName + " on")
				return(True)
		return(False)

	#
	# deviceMotionStatus - display the motion status of a device
	#

	def deviceMotionStatus(self):

		theMessage = '\n\n==== DeviceStatus for ' + self.deviceName + '====\n'

		if self.theIndigoDevice.onState == True:
			scheduledOffTime = mmLib_Low.delayedFunctionKeys.get(self.offDelayCallback,0)
			if not scheduledOffTime:
				scheduledOffTime = mmLib_Low.delayedFunctionKeys.get(self.offCallback,0)
			if scheduledOffTime:
				theTimeString = mmLib_Low.minutesAndSecondsTillTime(scheduledOffTime)
				theMessage = theMessage + str("\'" + self.deviceName + "\'" + " is scheduled to turn off in " + str(theTimeString) + ".\n")
			else:
				theMessage = theMessage + str("WARNING " + "\'" + self.deviceName + "\'" + " is on but not scheduled to turn off.\n" )
				onGroup = self.listOccupiedControllers(self.allControllerGroups)
				if onGroup: theMessage = theMessage + str("  Related Controllers Reporting Occupied: " + str(onGroup) + "\n")
		else:

			if self.ourNonvolatileData["bedtimeMode"] == mmLib_Low.BEDTIMEMODE_ON:
				bedtimeMessage = " Bedtime Mode Active."
			else:
				bedtimeMessage = ""

			theMessage = theMessage + str("\'" + self.deviceName + "\'" + " is not on." + bedtimeMessage + "\n")

		theMessage = theMessage + mmLib_Low.mmGetDelayedProcsList({'theDevice':self.deviceName})
		theMessage = theMessage + "\n==== DeviceStatus End ====\n"

		mmLib_Log.logReportLine(theMessage)

		return 0

	#
	# 		mmDayNightTransition - process day/night transition
	#
	def mmDayNightTransition(self,eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " is processing mmDayNightTransition of " + str(eventID) + ". bedtimeMode NV Value is " + str(self.ourNonvolatileData["bedtimeMode"]))

		# do day/night processing

		if eventID == 'isDayTime':
			#
			#  process night to day transition
			newBrightnessVal = self.daytimeOnLevel

			# do bedtimeMode reset if needed
			if self.ourNonvolatileData["bedtimeMode"] == mmLib_Low.BEDTIMEMODE_ON:
				self.ourNonvolatileData["bedtimeMode"] = mmLib_Low.BEDTIMEMODE_OFF
				mmLib_Log.logReportLine("Bedtime Mode OFF for device: " + self.deviceName)
				self.setControllersOnOfflineState('on')  # we are turning badtime mode off, so start commands from our controllers again
		else:
			#
			#  process day to night transition
			newBrightnessVal = self.nighttimeOnLevel

			# if we are supposed to be in bedtime mode (based on NV variable) and we are transitioning into night, we might have restarted
			# put us back into bedtime mode
			if self.ourNonvolatileData["bedtimeMode"] == mmLib_Low.BEDTIMEMODE_ON:
				mmLib_Log.logReportLine("Restoring Bedtime Mode ON for device: " + self.deviceName)
				self.setControllersOnOfflineState('bedtime')	# its ok that this command isn't queued, it doesnt send a message just updates state in Indigo

		# process day/night brightness transitions
		# If the device is on, set its brightness to the appropriate level, but only if there is nobody in the room
		if self.theIndigoDevice.onState == True and self.theIndigoDevice.__class__ == indigo.DimmerDevice and self.getAreaOccupiedState(self.allControllerGroups) == False and int(newBrightnessVal) != int(self.theIndigoDevice.states["brightnessLevel"]):
			mmLib_Log.logReportLine("Day/Night transition for device: " + self.deviceName)
			self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': newBrightnessVal,'defeatTimerUpdate': 'dayNightTransition', 'retry': 2})

	#
	# periodicStatusUpdateRequest - status requests every now and then
	#
	def periodicStatusUpdateRequest(self, parameters):

		self.queueCommand({'theCommand': 'sendStatusRequest', 'theDevice': self.deviceName, 'theValue': 999, 'retry': 2})

		renewalStatusRequestTimeDelta = random.randint(3600, 3600 * 2)	# return timer reset value in seconds (between 1 and 2 hours)

		mmLib_Log.logVerbose("Sent Status Update Request for device: " + self.deviceName + ". Will send another in " + str(round(renewalStatusRequestTimeDelta/60.0, 2)) + " minutes.")

		if self.theIndigoDevice.onState == True:
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

