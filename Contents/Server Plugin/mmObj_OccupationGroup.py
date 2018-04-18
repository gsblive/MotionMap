
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
			for member in self.members: self.unoccupiedAllDict[member] = time.strftime("%m/%d/%Y %I:%M:%S")


			# Dict of events we support, and which of the above lists get added to and deleted from for each event type
			self.occupationdictAnalyticsMatrix =	{
													'OccupiedPartial': {'deleteFrom': [self.unoccupiedAllDict,self.occupiedAllDict], 'addTo': [self.occupiedPartialDict]},
													'OccupiedAll': {'deleteFrom': [self.unoccupiedAllDict,self.occupiedPartialDict], 'addTo': [self.occupiedAllDict]},
													'UnoccupiedAll': {'deleteFrom': [self.occupiedAllDict,self.occupiedPartialDict], 'addTo': [self.unoccupiedAllDict]}
													}

			self.supportedCommandsDict.update({'devStatus':self.devStatus})

			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.completeInit, {}, self.deviceName)

	#
	# updateSubscribers - Send all our subscribers an update message with our current occupation Status
	#
	def updateSubscribers(self, skipEvent):

		newEvents = self.getOccupiedState()

		if self.debugDevice: mmLib_Log.logForce("Occupation Group " + self.deviceName + " calculated events " + str(newEvents) + " for delivery.")

		# only report this update to subscribers if it has changed
		if self.lastReportedOccupationEvent != newEvents:
			self.lastReportedOccupationEvent = newEvents
			if newEvents[0] != skipEvent:
				if self.debugDevice: mmLib_Log.logForce("    " + self.deviceName + " Delivering events " + str(newEvents) + " to all subscribers.")
				mmLib_Events.distributeEvents(self.deviceName, newEvents, 0, {})
			else:
				if self.debugDevice: mmLib_Log.logForce( "Occupation Group " + self.deviceName + " Skipping delivery of event \'" + str(skipEvent) + "\'.")

		else:
			if self.debugDevice: mmLib_Log.logForce("    No delivery necessary. No Change to previous delivery.")

		# either way, update the indigo variable
		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, newEvents[0])

		return 0

	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self,eventID, eventParameters):

		self.updateSubscribers('UnoccupiedAll')		# skip UnoccupiedAll events because that is the default at startup time

		return 0

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

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "occupiedAll", str(self.occupiedAllDict))
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "occupiedPartial", str(self.occupiedPartialDict))
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "unoccupiedAll", str(self.unoccupiedAllDict))
		theMessage = theMessage + "\n\n"

		if self.scheduledDeactivationTimeSeconds:
			theMessage = theMessage + str("    \'Unoccupied\' Event pending. To be delivered in " + str( mmLib_Low.minutesAndSecondsTillTime(self.scheduledDeactivationTimeSeconds)))

		theMessage = theMessage + '\n==== End DeviceStatus for ' + self.deviceName + ' ====\n'
		theMessage = theMessage + "\n"

		mmLib_Log.logReportLine(theMessage)

		return 0

	#
	# For occupation Group... On State is true if it is fully occupied
	#
	def getOnState(self):

		if len(self.occupiedAllDict) == len(self.members):
			return(True)
		else:
			return(False)

	def getOccupiedState(self):

		if len(self.occupiedAllDict) == len(self.members):
			# highest priority... all members are reporting full occupancy
			newEvents = ['OccupiedAll']
			self.occupiedState = True
		elif len(self.unoccupiedAllDict) == len(self.members):
			# next highest priority... all members are reporting no occupancy
			newEvents = ['UnoccupiedAll']
			self.occupiedState = False
		else:
			# We are partially occupied send the appropriate event
			newEvents = ['OccupiedPartial']
			self.occupiedState = True

		return(newEvents)

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





	#
	# receiveOccupationEvent - we received an activation event, process it
	#
	#			The type of occupation event we have been looking for is reported here. Based on the any/all mode factor,
	# 			determine if we should schedule the activation event to later occur in deviceTime above
	#

	def receiveOccupationEvent(self, theEvent, eventParameters):

		if self.debugDevice: mmLib_Log.logForce("Occupation Group " + self.deviceName + " received \'" + theEvent + "\' event from " + eventParameters['publisher'])

		theTimeString = time.strftime("%m/%d/%Y %I:%M:%S")
		
		dictAnalyticsMatrix = self.occupationdictAnalyticsMatrix[theEvent]
		
		# Add and delete the publisher to/from the analytics dictionaries
		
		for delDict in dictAnalyticsMatrix['deleteFrom']:
			try:
				del delDict[eventParameters['publisher']]  # no longer fully occupied full for sure
			except:
				pass

		for addDict in dictAnalyticsMatrix['addTo']:
			addDict[eventParameters['publisher']] = theTimeString


		if theEvent in ['OccupiedAll', 'OccupiedPartial']:

			# Process the ocupied event... Clearly

			# All unoccupied events pending are no longer valid
			if self.unoccupiedRelayDelaySeconds:							# if unoccupied timer is running, stop it
				mmLib_Low.cancelDelayedAction(self.unoccupiedTimerProc)		# This handles exception so it will cancel only if it exists
				self.scheduledDeactivationTimeSeconds = 0

			self.updateSubscribers(0)		# let the subscribers know about our change

		else:

			# now distribute the unoccupiedAll event to any subscribers (delay as necessary)

			# relay the event or set a timer to do so
			if not self.unoccupiedRelayDelaySeconds:
				self.unoccupiedTimerProc({})
			else:
				mmLib_Low.registerDelayedAction({'theFunction': self.unoccupiedTimerProc, 'timeDeltaSeconds': self.unoccupiedRelayDelaySeconds, 'theDevice': self.deviceName, 'timerMessage': "unoccupiedTimerProc"})
				self.scheduledDeactivationTimeSeconds = int(time.mktime(time.localtime()) + self.unoccupiedRelayDelaySeconds)
				ft = datetime.now() + timedelta(seconds=self.unoccupiedRelayDelaySeconds)
				varString = mmLib_Low.getIndigoVariable(self.occupationIndigoVar, "Unknown")
				varString = varString.partition(' ')[0] + " ( Till " + '{:%-I:%M %p}'.format(ft) + " )"
		 		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, varString)
		return 0

	#
	# loadDeviceNotificationOfOn - called from Load Devices... we pass it through to member controllers
	#
	def loadDeviceNotificationOfOn(self):
		self.controllerMissedCommandCount = self.controllerMissedCommandCount + 1

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
			memberDev = mmLib_Low.MotionMapDeviceDict.get(member, 0)
			if memberDev:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " sending forceTimeout to \'" + member + "\'.")
				memberDev.forceTimeout(BlackOutTimeSecs)

		# Now process the call for ourselves
		if self.scheduledDeactivationTimeSeconds:  # if unoccupied timer is running, stop it
			mmLib_Low.cancelDelayedAction(self.unoccupiedTimerProc)  # This handles exception so it will cancel only if it exists
			self.unoccupiedTimerProc({})

		return 0