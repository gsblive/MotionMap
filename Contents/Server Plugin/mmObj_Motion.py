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

kMotionDevTolerableMotionBounceTime = 2	#if off/on transition time is > 2 seconds, the device is not bouncing
kMotionDevMaxSequentialBounces = 50	# if there are more than 50 bounces in a row, there may be a problem (usually requires a battery replacement or reset of parameters)
OccupiedStateList = ['UnoccupiedAll', 'OccupiedAll', 'Unknown']

try:
	import indigo
except:
	pass

import mmLib_Log
import mmLib_Low
import mmLib_Events
import mmComm_Insteon
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
import random
from datetime import datetime, timedelta

######################################################
#
# mmMotion - Motion Sensor Device
#
######################################################
class mmMotion(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):

		random.seed()

		# set things that must be setup before Base Class
		self.lastOnTimeSeconds = 0
		self.lastOffTimeSeconds = 0

		super(mmMotion, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.maxMovement = theDeviceParameters["maxMovement"]	# the amount of time (in minutes) that the motion sense can stay "ON" for sustained occupancy
			self.minMovement = theDeviceParameters["minMovement"]	# the amount of time (in minutes) that motion sense is "OFF" that constitutes no occupancy
			mmLib_Low.controllerDeque.append(self)		# insert into device-time deque

			self.occupiedState = 2
			self.supportedCommandsDict = {}
			self.controllerMissedCommandCount = 0
			self.previousMotionOff = 0

			mmLib_Events.registerPublisher(['on', 'off', 'OccupiedAll', 'UnoccupiedAll'], self.deviceName)

			self.supportedCommandsDict.update({})

			self.ourNonvolatileData = mmLib_Low.initializeNVDict(self.deviceName)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "rapidTransitionTimeList", [])
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "problemReportTime", 0)
			s = str(self.deviceName + ".Occupation")
			self.occupationIndigoVar = s.replace(' ', '.')
			mmLib_Low.getIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState])

			self.supportedCommandsDict.update({'devStatus': self.devStatus})

			# register for the indigo events we want

			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.initializationComplete, {}, self.deviceName)


			mmLib_Events.subscribeToEvents(['AtributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes':{'onState':0}}, self.deviceName)
			#mmLib_Events.subscribeToEvents(['DevRcvCmd'], ['Indigo'], self.receivedCommandEvent, {}, self.deviceName)
			#mmLib_Events.subscribeToEvents(['DevCmdComplete'], ['Indigo'], self.completeCommandEvent, {}, self.deviceName)
			#mmLib_Events.subscribeToEvents(['DevCmdErr'], ['Indigo'], self.errorCommandEvent, {}, self.deviceName)


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
	# getOccupancyTimeout - return an int that indicates the number of minutes that must transpire before a non-occupancy state is assumed
	#
	def getOccupancyTimeout(self):
		return int(self.minMovement)

	#
	# setOnOffLine - select motionsensor's online/offline state
	#
	#	we support the following requestedStates:
	#
	#	'on'			The motion sensor received an on signal
	#	'off'			The motion sensor received an off signal
	#	'bedtime'		The motion sensor is sleeping till morning
	def setOnOffLine(self, requestedState):

		if self.onlineState != requestedState:
			if self.debugDevice: mmLib_Log.logForce("Setting " + self.deviceName + " onOfflineState to \'" + requestedState + "\'.")

			self.onlineState = requestedState
			self.processOccupation(1)

		return(0)


	#
	# getSecondsSinceState - how many seconds since the device was in the given on/off state
	#
	def getSecondsSinceState(self, theState):
		if self.onlineState in ['off','bedtime']: return(int(60*60*24))	# default to a high number if the device is offline

		if theState == 'on':
			theStateTime = self.lastOnTimeSeconds
		else:
			theStateTime = self.lastOffTimeSeconds

		return(int(time.mktime(time.localtime()) - theStateTime))


	def getOnState(self):

		return(self.theIndigoDevice.onState)

	#
	# setLastUpdateTimeSeconds - note the time when the device changed state
	#

	def setLastUpdateTimeSeconds(self):

		super(mmMotion, self).setLastUpdateTimeSeconds()  # Call Base Class

		if self.getOnState() == True:
			self.lastOnTimeSeconds = self.lastUpdateTimeSeconds
		else:
			self.lastOffTimeSeconds = self.lastUpdateTimeSeconds
		return()

	#
	# delayProcForOnStateTimeout - if the device went ON 24 hours ago and never went off... it must be offline
	#
	def delayProcForOnStateTimeout(self, theParameters):
		mmLib_Log.logWarning(self.deviceName + " received \'on\' command 24 hours ago and never received off... changing onOffline state to \'off\'.")
		self.setOnOffLine('off')
		return 0


	# delayProcForMaxOccupancy - the device has been marked as occupied for the max amount of time
	#
	def	delayProcForMaxOccupancy(self, theParameters):

		if self.debugDevice: mmLib_Log.logForce("Motion sensor " + self.deviceName + " has been occupied for the maximum amount of time.")
		mmLib_Low.cancelDelayedAction(self.delayProcForNonOccupancy)  # Its unoccupied, clear non occupied timer too
		self.occupiedState = False
		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState])
		mmLib_Events.distributeEvents(self.deviceName, ['UnoccupiedAll'], 0, {})  # dispatch to everyone who cares

		return 0		# Cancel timer



	# delayProcForNonOccupancy - the device seems to indicate area vacant
	#
	def delayProcForNonOccupancy(self, theParameters):

		if self.debugDevice: mmLib_Log.logForce("Motion sensor " + self.deviceName + " is indicating non-occupied.")
		mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)  # Its unoccupied, clear max occupation timer too
		self.occupiedState = False
		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState])
		mmLib_Events.distributeEvents(self.deviceName, ['UnoccupiedAll'], 0, {})  # dispatch to everyone who cares

		return 0		# Cancel timer



	#
	# deviceTime - check to see if the area is occupied or not, dispatch events accordingly
	#
	def deviceTime(self):
		return(0)



	#
	# initializationComplete - Finalize initialization and start running
	#
	def initializationComplete(self,eventID, eventParameters):

		self.processOccupation(1)
		return(0)


	def processOccupation(self, forceDelivery):

		if self.debugDevice: mmLib_Log.logForce("ProcessOccuption for " + self.deviceName + ". ForceDelivery = " + str(forceDelivery)+ ". onLineState = " + str(self.onlineState) + ". onState = " + str(self.getOnState()))

		if self.onlineState != 'on':
			self.occupiedState = False	# if the device is offline (or bedtime mode), assume it is also unoccupied.
			# if there are any delay procs, delete them, they are not valid anymore 
			mmLib_Low.cancelDelayedAction(self.delayProcForNonOccupancy)
			mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)
			mmLib_Log.logForce( "Motion sensor " + self.deviceName + " is going offline because it\'s \'onlineState\' is " + str(self.onlineState))
			if self.onlineState == 'off':
				mmLib_Low.setIndigoVariable(self.occupationIndigoVar, "# Offline #")
			else:
				mmLib_Low.setIndigoVariable(self.occupationIndigoVar, "# Bedtime #")
			mmLib_Events.distributeEvents(self.deviceName, ['UnoccupiedAll'], 0, {})  # dispatch to everyone who cares
			return(0)

		if self.occupiedState == 2:
			# this is initialization time, processing is special
			if self.getOnState() == False:
				self.occupiedState = False
				mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState])
				# initial update to all devices who care
				if self.occupiedState:
					newEvents = ['OccupiedAll']
				else:
					newEvents = ['UnoccupiedAll']
				try:
					mmLib_Events.distributeEvents(self.deviceName, newEvents, 0, {})  # dispatch to everyone who cares
				except Exception as exception:
					mmLib_Log.logError("Motion sensor " + self.deviceName + " failed to distribute events: " + str(newEvents) + ". Exception: " + str(exception))
				return(0)
			else:
				if self.debugDevice: mmLib_Log.logForce("Motion sensor " + self.deviceName + " is initializing to Occupied.")


		if self.getOnState() == True:
			# device is indicating motion, so set the timeout to the Maximum
			timeDeltaSeconds = int(self.maxMovement) * 60
			mmLib_Low.cancelDelayedAction(self.delayProcForNonOccupancy)
			mmLib_Low.registerDelayedAction( {	'theFunction': self.delayProcForMaxOccupancy,
											  	'timeDeltaSeconds': timeDeltaSeconds,
				 								'theDevice': self.deviceName,
												'timerMessage': "Motion Sensor MaxOccupancy Timer"})
		else:
			# device is NOT indicating motion, so set timeout to the minimum
			timeDeltaSeconds = int(self.minMovement) * 60
			mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)
			mmLib_Low.registerDelayedAction( {	'theFunction': self.delayProcForNonOccupancy,
											  	'timeDeltaSeconds': timeDeltaSeconds,
				 								'theDevice': self.deviceName,
												'timerMessage': "Motion Sensor NonOccupancy Timer"})
		# either way, we are occupied for now
		newOccupiedState = True

		if timeDeltaSeconds:
			ft = datetime.now() + timedelta(seconds=timeDeltaSeconds)
			varString = " ( Till " + '{:%-I:%M %p}'.format(ft) + " )"
			mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[newOccupiedState] + varString)
		else:
			mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[newOccupiedState])

		# figure out what state we should be in
		
		if forceDelivery or self.occupiedState != newOccupiedState:	# occupiedState will be 2 to start... and will always allow the code below
		
			if self.debugDevice: mmLib_Log.logForce("Occupied State for " + self.deviceName + " has changed to " + str(OccupiedStateList[newOccupiedState]))
	
			self.occupiedState = newOccupiedState
			mmLib_Events.distributeEvents(self.deviceName, [OccupiedStateList[newOccupiedState]], 0, {})  # dispatch to everyone who cares

	#
	# dispatchOnOffEvents - we received a command from our motion Sensor, process it
	#
	def dispatchOnOffEvents(self, theCommandByte ):

		# process Motion here
		self.deviceTime()		# this will process occupancy events
		if theCommandByte == mmComm_Insteon.kInsteonOn:	#kInsteonOn = 17
			mmLib_Events.distributeEvents(self.deviceName, ['on'], 0, {})  # dispatch to everyone who cares
			#self.dispatchEventToDeque(self.onDeque, 'on')							# process on
		elif theCommandByte == mmComm_Insteon.kInsteonOff:		#kInsteonOff = 19
			mmLib_Events.distributeEvents(self.deviceName, ['off'], 0, {})  # dispatch to everyone who cares
			#self.dispatchEventToDeque(self.offDeque, 'off')							# process off
		else:
			mmLib_Log.logVerbose("Invalid insteon event received for " + self.deviceName + " of " + str(theCommandByte))

		return(0)


	#
	# countBounce
	#	Check to see if the device is rapidly cycling between on and off
	#
	def countBounce(self):

		deltaSeconds = self.getSecondsSinceState('off')
		if deltaSeconds > kMotionDevTolerableMotionBounceTime:
			# the multisensor isnt looping, reset counter and list.
			self.ourNonvolatileData["rapidTransitionTimeList"] = []
			self.ourNonvolatileData["problemReportTime"] = 0
		else:
			# count the sequential transaction
			self.ourNonvolatileData["rapidTransitionTimeList"].append(str(time.ctime(time.mktime(time.localtime()))) + " Reporting only " + str(deltaSeconds) + " seconds of off time.")
			if len(self.ourNonvolatileData["rapidTransitionTimeList"]) == kMotionDevMaxSequentialBounces:
				self.reportFullStatus(1)		# report the problem
				# we reported the problem, now reset
				self.ourNonvolatileData["rapidTransitionTimeList"] = []
				self.ourNonvolatileData["problemReportTime"] = 0

		return(0)
	#
	# deviceUpdated
	#
	# we separated this into two routines because CamMotion needs access to the lower level routine
	def	deviceUpdatedEvent(self, eventID, eventParameters):

		newOnState = eventParameters.get('onState', 'na')

		if self.debugDevice: mmLib_Log.logForce("deviceUpdatedEvent for " + self.deviceName + ". newOnState = " + str(newOnState) + ". onlineState = " + str(self.onlineState))

		if self.onlineState == 'off' and newOnState == True:
			if self.debugDevice: mmLib_Log.logForce("Bringing " + self.deviceName + " back online.")
			self.setOnOffLine('on')

		if self.onlineState == 'on':

			if newOnState != 'na':
				mmLib_Log.logVerbose(self.deviceName + ": Motion Onstate = " + str(newOnState))
				super(mmMotion, self).deviceUpdatedEvent(eventID, eventParameters)  # the base class just keeps track of the time since last change
				self.controllerMissedCommandCount = 0			# Reset this because it looks like are controller is alive (battery report uses this)
				if newOnState == True:
					mmLib_Low.registerDelayedAction({'theFunction': self.delayProcForOnStateTimeout,
													 'timeDeltaSeconds': int(60 * 60 * 24),
													 'theDevice': self.deviceName,
													 'timerMessage': "Motion Sensor OnStateTimeout Timer"})
					# we are detecting motion
					if self.debugDevice:
						mmLib_Log.logForce( "Motion Sensor " + self.deviceName + " received update event: ON")

					self.countBounce()	# Collect Metrics regarding on/off sequences to tell if the sensor is bouncing

					# And dispatch the ON event
					self.dispatchOnOffEvents( mmComm_Insteon.kInsteonOn )	#kInsteonOn = 17

				else:
					mmLib_Low.cancelDelayedAction(self.delayProcForOnStateTimeout)
					# We are detecting non-motion
					if self.debugDevice: mmLib_Log.logForce("Motion Sensor " + self.deviceName + " received update event: OFF")

					self.previousMotionOff = time.mktime(time.localtime())
					# And dispatch the ON event
					self.dispatchOnOffEvents(mmComm_Insteon.kInsteonOff )	#kInsteonOff = 19

				# do occupation event processing
				self.processOccupation(0)

			else:
				mmLib_Log.logDebug(self.deviceName + ": Received duplicate command: Onstate = " + str(newOnState))

		return(0)

	#
	# devStatus
	#
	def devStatus(self, theCommandParameters):

		self.reportFullStatus(0)

		return (0)

	#
	# loadDeviceNotificationOfOn - called from Load Devices
	# A load device associated with this motion sensor was manually turned on, note it for Battery performance tests
	#
	def loadDeviceNotificationOfOn(self):
		self.controllerMissedCommandCount = self.controllerMissedCommandCount + 1

		return(0)

	#
	# reportFullStatus - report debounce Problem for this device, if any
	#
	def reportFullStatus(self, sendEmail):

		theBody = "Debounce Report for " + self.deviceName

		if sendEmail:
			# send an email indicating the problem
			theBody = theBody + str("\r####### ")
		else:
			# just reporting status
			theBody = theBody + str("\r")

		listLength = len(self.ourNonvolatileData["rapidTransitionTimeList"])

		# report Online State
		theBody = theBody + "\rOnline State is: " + self.onlineState + "\r"

		# report Occupied State
		theBody = theBody + "It's reporting " + OccupiedStateList[self.occupiedState] + "\r"

		# Report When Occupation will end (if any)
		if OccupiedStateList[self.occupiedState] == "Occupied":
			projectedUnoccupiedEventTime = "Unknown Time"
			UnoccupiedReason = "of undefined reasons"
			if self.getOnState() == True:
				# sensor is showing ON, so delayProcForMaxOccupancy occupiedState transition now
				executionTime = int(mmLib_Low.findDelayedAction(self.delayProcForMaxOccupancy))
				if executionTime != 0:
					UnoccupiedReason = "maximum allowable time for motion has been reached"
					projectedUnoccupiedEventTime = mmLib_Low.minutesAndSecondsTillTime(executionTime)
					#projectedUnoccupiedEventTime = str(time.ctime(executionTime))
				else:
					mmLib_Log.logForce("#### " + self.deviceName + " is reporting occupied (while ON), yet there is no delayProcForMaxOccupancy delayProc registered to turn it off.")
			else:
				# sensor is showing OFF, so delayProcForNonOccupancy controls occupiedState transition now
				executionTime = int(mmLib_Low.findDelayedAction(self.delayProcForNonOccupancy))
				if executionTime != 0:
					UnoccupiedReason = "motion has stopped"
					projectedUnoccupiedEventTime = mmLib_Low.minutesAndSecondsTillTime(executionTime)
					#projectedUnoccupiedEventTime = str(time.ctime(executionTime))
				else:
					mmLib_Log.logForce("#### " + self.deviceName + " is reporting occupied (while OFF), yet there is no delayProcForNonOccupancy delayProc registered to turn it off.")

			theBody = theBody + "Will become Unoccupied in " + projectedUnoccupiedEventTime + " because " + UnoccupiedReason + "\r"

		if listLength > 1:
			theBody = str(theBody + self.deviceName + "'s number of off/on cycle times less than " + str(kMotionDevTolerableMotionBounceTime) + " seconds: " + str(listLength))

			theBody = theBody + "\rLast " + str(listLength) + " sequential off/on transition times to ON: \r"
			for newTimeStr in self.ourNonvolatileData["rapidTransitionTimeList"]:
				theBody = theBody + "\r" + newTimeStr
		else:
			theBody = theBody + "No sequential off/on transition times less than " + str(kMotionDevTolerableMotionBounceTime) + " seconds."

		mmLib_Log.logReportLine(theBody)

		if sendEmail:
			# send an email indicating the problem
			# only allow sending emails every 24 hours for this device
			if not self.ourNonvolatileData["problemReportTime"] or int(time.mktime(time.localtime()) - int(self.ourNonvolatileData["problemReportTime"])) > 60*60*24:
				theBody = "\r" + theBody + "\r"
				theSubject = str("MotionMap2 " + str(indigo.variables["MMLocation"].value)+ " MotionSensor Failure Report: " + self.deviceName)
				theRecipient = "greg@GSBrewer.com"
				indigo.server.sendEmailTo(theRecipient, subject=theSubject, body=theBody)
				# update the problem report time
				self.ourNonvolatileData["problemReportTime"] = time.mktime(time.localtime())
				self.ourNonvolatileData["problemReportTimeHumanReadable"] = '{:%a %b %-d, %Y %-I:%M %p}'.format(datetime.now())
			else:
				mmLib_Log.logWarning( self.deviceName + " is reporting MotionSensorFailure, but email was supressed due to recent delivery at " + str(self.ourNonvolatileData["problemReportTimeHumanReadable"]))


	#
	# checkBattery - report the status of this device's battery
	# 	FORCE it to the log
	#	returns 0 if good battery, nonzero if bad
	#
	def checkBattery(self, theCommandParameters):

		addString = ""

		# if the device is ON, see if has been on too long
		if self.controllerMissedCommandCount > mmLib_Low.MOTION_MAX_MISSED_COMMANDS:
			newString =  self.deviceName + " has missed " + str(self.controllerMissedCommandCount) + " events. The battery is likely dead"
			addString = addString + newString + "\n"
			mmLib_Log.logForce(newString)

		if self.getOnState() == True:
			if self.getSecondsSinceUpdate() > mmLib_Low.MOTION_MAX_ON_TIME:
				newString =  self.deviceName + " has been on for " + str(int(self.getSecondsSinceUpdate()) / int(60*60)) + " hours. The device may need to be reset or the battery may be dead"
				addString = addString + newString + "\n"
				mmLib_Log.logForce(newString)
				indigo.device.turnOff(self.devIndigoID)	# doesnt honor the unresponsive flag because this just sets statte in indigo (no command is sent to the device)
		else:
			if self.getSecondsSinceUpdate() > mmLib_Low.MOTION_MAX_OFF_TIME:
				newString =  self.deviceName + " has been off for " + str(int(self.getSecondsSinceUpdate()) / int(24*60*60)) + " days. The device may need to be reset or the battery may be dead "
				addString = addString + newString + "\n"
				mmLib_Log.logForce(newString)

		return(addString)
