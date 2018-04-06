
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

import mmComm_Indigo
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
#from contextlib import suppress

occupationRelatedEvents = ['occupied','unoccupied','occupiedAll','unoccupiedAll']
occupationEvents = ['occupied','occupiedAll' ]	# occupation only, not unoccupation
EventToOccupiedStateDict = {'unoccupied': "OccupiedPartial", 'unoccupiedAll': "UnoccupiedAll", 'occupied': "OccupiedPartial",
							'occupiedAll': "OccupiedAll", 'unknown': "Unknown"}


######################################################
#
# mmOccupation - Virtual Device used to relay occupation events
#
# Events Supported: 'occupied', 'unoccupied', 'occupiedAll' and 'unoccupiedAll'
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

			mmLib_Events.registerPublisher(occupationRelatedEvents, self.deviceName)
			
			# Subscribe to requested occupancy event
			mmLib_Events.subscribeToEvents(occupationRelatedEvents, self.members, self.receiveOccupationEvent2, {}, self.deviceName)

			self.occupiedAllDict = {}
			self.unoccupiedAllDict = {}
			self.occupiedPartialDict = {}

			# now make a copy of Members into UnoccupiedAll... we have to assume unoccupied to start... later each motion sensor will update us
			for member in self.members: self.unoccupiedAllDict[member] = time.strftime("%m/%d/%Y %I:%M:%S")


			# Dict of events we support, and which of the above lists get added to and deleted from for each event type
			self.occupationdictAnalyticsMatrix =	{
													'occupied': {'deleteFrom': [self.unoccupiedAllDict,self.occupiedAllDict], 'addTo': [self.occupiedPartialDict]},
													'unoccupied': {'deleteFrom': [self.unoccupiedAllDict,self.occupiedAllDict], 'addTo': [self.occupiedPartialDict]},
													'occupiedAll': {'deleteFrom': [self.unoccupiedAllDict,self.occupiedPartialDict], 'addTo': [self.occupiedAllDict]},
													'unoccupiedAll': {'deleteFrom': [self.occupiedAllDict,self.occupiedPartialDict], 'addTo': [self.unoccupiedAllDict]}
													}

			self.supportedCommandsDict.update({'devStatus':self.devStatus})

			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.completeInit, {}, self.deviceName)

	#
	# updateSubscribers - Send all our subscribers an update message with our current occupation Status
	#
	def updateSubscribers(self,theEvent):

		if len(self.occupiedAllDict) == len(self.members):
			# highest priority... all members are reporting full occupancy
			newEvents = ['occupiedAll','occupied']
		elif len(self.unoccupiedAllDict) == len(self.members):
			# next highest priority... all members are reporting no occupancy
			newEvents = ['unoccupiedAll','unoccupied']
		else:
			# We are partially occupied send the appropriate event
			if theEvent:
				if theEvent in occupationEvents:
					newEvents = ['occupied']
				else:
					newEvents = ['unoccupied']
			else:
				# this is init time, lets manufacture an event that represents our current state
				if len(self.occupiedPartialDict):
					newEvents = ['occupied']
				else:
					newEvents = ['unoccupied']

		mmLib_Events.distributeEvents(self.deviceName, newEvents, 0, {})

		# and update the indigo variable
		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, EventToOccupiedStateDict.get(newEvents[0], 'Unknown'))

		return 0

	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self,eventID, eventParameters):

		self.updateSubscribers(0)

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

		theMessage = '\n\n==== DeviceStatus for ' + self.deviceName + '====\n'

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

		mmLib_Log.logReportLine(theMessage)

													   
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

		self.updateSubscribers('unoccupied')

		self.scheduledDeactivationTimeSeconds = 0

		return 0	# do not continue timer





	#
	# receiveOccupationEvent2 - we received an activation event, process it
	#
	#			The type of occupation event we have been looking for is reported here. Based on the any/all mode factor,
	# 			determine if we should schedule the activation event to later occur in deviceTime above
	#

	def receiveOccupationEvent2(self, theEvent, eventParameters):

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


		if theEvent == 'occupiedAll':
			# Clearly, all unoccupied events pending are no longer valid
			if self.unoccupiedRelayDelaySeconds:							# if unoccupied timer is running, stop it
				mmLib_Low.cancelDelayedAction(self.unoccupiedTimerProc)		# This handles exception so it will cancel only if it exists
				self.scheduledDeactivationTimeSeconds = 0

			self.updateSubscribers(theEvent)		# let the subscribers know about our change

		else:

			# now distribute the proper unoccupied events for any subscribers (delay as necessary)

			# relay the event or set a timer to do so
			if not self.unoccupiedRelayDelaySeconds:
				self.unoccupiedTimerProc({})
			else:
				mmLib_Low.registerDelayedAction({'theFunction': self.unoccupiedTimerProc, 'timeDeltaSeconds': self.unoccupiedRelayDelaySeconds, 'theDevice': self.deviceName, 'timerMessage': "unoccupiedTimerProc"})
				self.scheduledDeactivationTimeSeconds = int(time.mktime(time.localtime()) + self.unoccupiedRelayDelaySeconds)

		return 0




