
__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

# import json
#import os
#import traceback

try:
	import indigo
except:
	pass

import mmLib_Log
import mmLib_Low
import mmLib_Events

import mmComm_Indigo
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
#from contextlib import suppress
from datetime import datetime, timedelta

occupationRelatedEvents = ['OccupiedPartial','OccupiedAll','UnoccupiedAll']


######################################################
#
# mmOccupation - Virtual Device used to relay occupation events
#
# Events Supported: 'OccupiedPartial', 'OccupiedAll' and 'UnoccupiedAll'
#
######################################################
class mmOccupationGroup(mmComm_Indigo.mmIndigo):


	def __init__(self, theDeviceParameters):
		super(mmOccupationGroup, self).__init__(theDeviceParameters)
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.members = theDeviceParameters["members"].split(';')  # Can be a list, split by semicolons... normalize it into a proper list
			self.unoccupiedRelayDelaySeconds = int(theDeviceParameters["unoccupiedRelayDelayMinutes"]) * 60
			self.defeatBlackout = int(theDeviceParameters.get("defeatBlackout", 0))
			self.scheduledDeactivationTimeSeconds = 0
			s = str(self.deviceName + ".Group.Occupation")
			self.occupationIndigoVar = s.replace(' ', '.')
			self.lastReportedOccupationEvent = 'none'
			self.occupiedState = 'none'

			mmLib_Events.registerPublisher(occupationRelatedEvents, self.deviceName)
			
			# Subscribe to requested occupancy event
			mmLib_Events.subscribeToEvents(occupationRelatedEvents, self.members, self.receiveOccupationEvent, {}, self.deviceName)

			self.occupiedAllDict = {}
			self.unoccupiedAllDict = {}
			self.occupiedPartialDict = {}

			# now make a copy of Members into UnoccupiedAll... we have to assume unoccupied to start... later each motion sensor will update us
			# Update... Consider the state of the existing members' motion sensors

			for member in self.members:
				self.unoccupiedAllDict[member] = time.strftime("%m/%d/%Y %I:%M:%S")


			# Dict of events we support, and which of the above lists get added to and deleted from for each event type
			self.occupationdictAnalyticsMatrix =	{
													'OccupiedPartial': {'deleteFrom': [self.unoccupiedAllDict,self.occupiedAllDict], 'addTo': [self.occupiedPartialDict]},
													'OccupiedAll': {'deleteFrom': [self.unoccupiedAllDict,self.occupiedPartialDict], 'addTo': [self.occupiedAllDict]},
													'UnoccupiedAll': {'deleteFrom': [self.occupiedAllDict,self.occupiedPartialDict], 'addTo': [self.unoccupiedAllDict]}
													}

			self.supportedCommandsDict.update({'devStatus':self.devStatus})

			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.completeInit, {}, self.deviceName)

	# resetIndigoVariableToReflectState
	# At initialization time, the Dictionaries and timers have all been reset.. we have to rebuild internal state with only the current mmembers' state. Then update the indigo variable.

	# def resetIndigoVariableToReflectState(self):


	#
	# updateSubscribers - Send all our subscribers an update message with our current occupation Status
	#
	def updateSubscribers(self, skipEvent):

		newEvent = self.getOccupiedState()

		if self.debugDevice: mmLib_Log.logForce("Occupation Group " + self.deviceName + " calculated events " + str(newEvent) + " for delivery.")

		# only report this update to subscribers if it has changed
		if self.lastReportedOccupationEvent != newEvent:
			self.lastReportedOccupationEvent = newEvent
			if newEvent != skipEvent:
				if self.debugDevice: mmLib_Log.logForce("    " + self.deviceName + " Delivering events " + str(newEvent) + " to all subscribers. defeatBlackout = "+ str(self.defeatBlackout))
				mmLib_Events.distributeEvents(self.deviceName, [newEvent], 0, {'defeatBlackout':self.defeatBlackout})
				# GB Fix me... If the load device skips this event, the occupationGroup and the device are out of sync
			else:
				if self.debugDevice: mmLib_Log.logForce( "Occupation Group " + self.deviceName + " Skipping delivery of event \'" + str(skipEvent) + "\'.")

		else:
			if self.debugDevice: mmLib_Log.logForce("    No delivery necessary. No Change to previous delivery.")

		# either way, update the indigo variable
		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, newEvent)

		return 0

	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self,eventID, eventParameters):

		self.initializeOccupiedState()
		self.updateSubscribers('UnoccupiedAll')		# skip UnoccupiedAll events because that is the default at startup time

		return 0

	#
	# deviceMotionStatus - check the motion status of a device
	#
	def deviceMotionStatus(self):

		self.devStatus({})
		return(0)

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	# 	All commands in this section must have a single parameter theCommandParameters - a list of parameters
	# 	And all commands must be registered in self.supportedCommandsDict variable
	#
	######################################################################################

	#
	#  devStatus - Display Status for this occupation event...
	#				Is the device showing occupied, is an action scheduled based on the occupation status, etc.
	#
	def	devStatus(self, theCommandParameters):

		theMessage = '\n\n==== DeviceStatus for ' + self.deviceName + ' ====\n'

		theMessage = theMessage + '\n Last Reported Occupation Event = ' + str(self.lastReportedOccupationEvent) + " OccupiedState = " + str(self.occupiedState)
		theMessage = theMessage + "\n"
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "Group", "Members/When")
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "All", str(self.members))
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "OccupiedAll", str(self.occupiedAllDict))
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "OccupiedPartial", str(self.occupiedPartialDict))
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "UnoccupiedAll", str(self.unoccupiedAllDict))
		theMessage = theMessage + "\n\n"

		if self.scheduledDeactivationTimeSeconds:
			theMessage = theMessage + str("    \'UnoccupiedAll\' Event pending. To be delivered in " + str( mmLib_Low.minutesAndSecondsTillTime(self.scheduledDeactivationTimeSeconds)))

		theMessage = theMessage + '\n==== End DeviceStatus for ' + self.deviceName + ' ====\n'
		theMessage = theMessage + "\n"

		mmLib_Log.logReportLine(theMessage)

		return 0

	#
	# For occupation Group... On State is true if any members are True
	#
	def getOnState(self):

		if self.onlineState != 'on': return(False)

		for member in self.members:
			if not member: continue
			memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
			if memberDev and memberDev.getOnState(): return(True)
		return(False)


	#
	# For occupation Group... Occupied State is true if it is fully occupied
	#
	def getOccupiedState(self):


		if len(self.occupiedAllDict) == len(self.members):
			# highest priority... all members are reporting full occupancy
			newEvent = 'OccupiedAll'
			self.occupiedState = True
		elif len(self.unoccupiedAllDict) == len(self.members):
			# next highest priority... all members are reporting no occupancy
			newEvent = 'UnoccupiedAll'
			self.occupiedState = False
		else:
			# We are partially occupied send the appropriate event
			newEvent = 'OccupiedPartial'
			self.occupiedState = True

		return(newEvent)

	#
	# initializeOccupiedState... Startup time (after a delay) set our initial occupation state
	#
	def initializeOccupiedState(self):

		occupancyCount = 0
		initialOccupancy = 'Unknown'

		for member in self.members:
			if not member: continue
			memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
			if memberDev:
				theState = memberDev.getOccupiedState()
				if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Obtaining initial occupied state from " + memberDev.deviceName + ". Result: \'" + str(theState) + "\'.")
				if theState == 'Unknown':
					mmLib_Log.logWarning(self.deviceName + " detects " + memberDev.deviceName + " with initial occupied state of \'Unknown\' we will have to run this process again.")
					# put in a process to run this again in a few seconds.
					mmLib_Low.registerDelayedAction({'theFunction': self.retryInitializeOccupiedState, 'timeDeltaSeconds': 5,'theDevice': self.deviceName, 'timerMessage': "retryInitializeOccupiedState"})
					return(0)

				# Its not an unknown state... set our analytics dictionaries correctly

				self.updateAnalyticsMatrix(theState, {'publisher':memberDev.deviceName})

				if theState == 'UnoccupiedAll':
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " detects " + memberDev.deviceName + " with initial occupied state of \'UnoccupiedAll\'.")
				else:
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " detects " + memberDev.deviceName + " with initial occupied state of \'" + theState + "\'. Counting up to see if we are fully occupied.")
					# there is some kind of occupancy here... increment the counter
					occupancyCount = occupancyCount+1

		if occupancyCount:
			# some level of occupancy, is it full?
			if len(self.members) == initialOccupancy:
				initialOccupancy = 'OccupiedAll'
			else:
				initialOccupancy = 'OccupiedPartial'
			self.occupiedState = True
		else:
			# no occupancy
			initialOccupancy = 'UnoccupiedAll'
			self.occupiedState = False

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " determined its initial occupancy of " + memberDev.deviceName + " with initial occupied state of \'" + initialOccupancy + "\'.")

		#GB Fix me... Im not sure if we need to deliver this event to subscribers... or is this handled elsewhere. testing indicates it isnt necessary

		return(0)


	def retryInitializeOccupiedState(self, parameters):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " retrying initializeOccupiedState.")

		self.initializeOccupiedState()
		return(0)

	#
	# setOnOffLine - we have to pass this command to the members
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

			for member in self.members:
				if not member: break
				memberDev = mmLib_Low.MotionMapDeviceDict.get(member,0)
				if memberDev: memberDev.setOnOffLine(requestedState)

		return(0)


													   
	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	#
	# unoccupiedTimerProc
	#
	#	The area was determined as unoccupied a while ago.. after a suitable delay (as defined by unoccupiedRelayDelaySeconds), relay the event.
	#
	def unoccupiedTimerProc(self, parameters):

		self.scheduledDeactivationTimeSeconds = 0
		self.updateSubscribers(0)

		return 0	# do not continue timer


	def updateAnalyticsMatrix(self, theEvent, eventParameters):

		if self.debugDevice: mmLib_Log.logForce( "Occupation Group " + self.deviceName + " received \'" + theEvent + "\' event from " + eventParameters['publisher'])

		theTimeString = time.strftime("%m/%d/%Y %I:%M:%S")

		# The occupationdictAnalyticsMatrix contains addition/deletion instructions for all event types in all
		# occupationDictionaries ( occupiedAllDict, occupiedPartialDict, unoccupiedAllDict }
		# follow those instructions to track occupation levels of member controllers (motions sensors and other occupation groups)

		dictAnalyticsMatrix = self.occupationdictAnalyticsMatrix[theEvent]

		# Add and delete the publisher to/from the analytics dictionaries

		for delDict in dictAnalyticsMatrix['deleteFrom']:
			try:
				del delDict[eventParameters['publisher']]  # no longer fully occupied for sure
			except:
				pass

		for addDict in dictAnalyticsMatrix['addTo']:
			addDict[eventParameters['publisher']] = theTimeString

		return(0)

	#
	# receiveOccupationEvent - we received an activation (occupied or unoccupied) event, process it
	#
	#			The type of occupation event we have been looking for is reported here. Based on the any/all mode factor,
	# 			determine if we should schedule the activation event to later occur in deviceTime above
	#

	def receiveOccupationEvent(self, theEvent, eventParameters):

		if self.debugDevice: mmLib_Log.logForce("Occupation Group " + self.deviceName + " received \'" + theEvent + "\' event from " + eventParameters['publisher'])

		self.updateAnalyticsMatrix(theEvent, eventParameters)

		theEvent = self.getOccupiedState()		# the rest is based on our current group event state
		if self.debugDevice: mmLib_Log.logForce("Occupation Group " + self.deviceName + " calculated LocalState as \'" + str(theEvent) + "\'.")

		if theEvent in ['OccupiedAll', 'OccupiedPartial']:
			# Process the ocupied event... Clearly All unoccupied events pending are no longer valid
			if self.unoccupiedRelayDelaySeconds:							# if unoccupied timer is running, stop it
				mmLib_Low.cancelDelayedAction(self.unoccupiedTimerProc)		# This handles exception so it will cancel only if it exists
				self.scheduledDeactivationTimeSeconds = 0

			self.updateSubscribers(0)		# let the subscribers know about our change

		else:

			# now distribute the unoccupiedAll event to any subscribers (delay as necessary)

			# relay the event or set a timer to do so
			if not self.unoccupiedRelayDelaySeconds:
				if self.debugDevice: mmLib_Log.logForce("Occupation Group " + self.deviceName + " executing unoccupiedTimerProc immediately. unoccupiedRelayDelaySeconds value set to 0")
				self.unoccupiedTimerProc({})
			else:
				if self.debugDevice: mmLib_Log.logForce("Occupation Group " + self.deviceName + " registering delayed action \'unoccupiedTimerProc\' for execution in " + str(mmLib_Low.secondsToMinutesAndSecondsString(self.unoccupiedRelayDelaySeconds)))
				mmLib_Low.registerDelayedAction({'theFunction': self.unoccupiedTimerProc, 'timeDeltaSeconds': self.unoccupiedRelayDelaySeconds, 'theDevice': self.deviceName, 'timerMessage': "unoccupiedTimerProc"})
				# update the variable to reflect upcoming action
				self.scheduledDeactivationTimeSeconds = int(time.mktime(time.localtime()) + self.unoccupiedRelayDelaySeconds)
				ft = datetime.now() + timedelta(seconds=self.unoccupiedRelayDelaySeconds)
				varString = mmLib_Low.getIndigoVariable(self.occupationIndigoVar, "Unknown")
				if self.debugDevice: mmLib_Log.logForce("Occupation Group " + self.deviceName + " with indigoVarName of " + str(self.occupationIndigoVar) + " varString = " + str(varString))
				varString = varString.partition(' ')[0] + " ( Non-Motion Timeout at " + '{:%-I:%M %p}'.format(ft) + " )"
				mmLib_Low.setIndigoVariable(self.occupationIndigoVar, varString)
		return 0


	#
	# loadDeviceNotificationOfOn - called from Load Devices... we pass it through to member controllers
	#
	def loadDeviceNotificationOfOn(self):

		for member in self.members:
			if not member: break
			memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
			if memberDev:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " sending loadDeviceNotificationOfOn to \'" + member + "\'.")
				memberDev.loadDeviceNotificationOfOn()

		return (0)


	#
	# forceTimeout - The device we are controlling was manually turned off, so cancel our offTimers if there are any
	#
	def forceTimeout(self,BlackOutTimeSecs):

		# Forward this call to all of our members

		for member in self.members:
			if not member: break
			# If member is unoccupied, no need to propogate timeout
			if member in self.unoccupiedAllDict:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " skipping forceTimeout to \'" + member + "\' because its already unoccupied.")
				continue
			memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
			if memberDev:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " sending forceTimeout to \'" + member + "\'.")
				memberDev.forceTimeout(BlackOutTimeSecs)

		# Now process the call for ourselves
		if self.scheduledDeactivationTimeSeconds:  # if unoccupied timer is running, stop it
			mmLib_Low.cancelDelayedAction(self.unoccupiedTimerProc)  # This handles exception so it will cancel only if it exists
			self.unoccupiedTimerProc({})

		return 0