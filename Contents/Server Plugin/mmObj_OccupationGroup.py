
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
EventToOccupiedStateDict = {'unoccupied': "Unoccupied", 'unoccupiedAll': "UnoccupiedAll", 'occupied': "Occupied",
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
			self.actionControllerCount = len(self.members)
			self.unoccupiedRelayDelaySeconds = int(theDeviceParameters["unoccupiedRelayDelayMinutes"]) * 60
			self.scheduledDeactivationTimeSeconds = 0
			s = str(self.deviceName + ".Group.Occupation")
			self.occupationIndigoVar = s.replace(' ', '.')

			mmLib_Events.registerPublisher(occupationRelatedEvents, self.deviceName)
			
			# Subscribe to requested occupancy event
			mmLib_Events.subscribeToEvents(occupationRelatedEvents, self.members, self.receiveOccupationEvent, {}, self.deviceName)

			self.occupiedDict = {}
			self.unoccupiedDict = {}
			self.occupiedFullDict = {}
			self.unoccupiedFullDict = {}

			self.supportedCommandsDict.update({'devStatus':self.devStatus})

			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.completeInit, {}, self.deviceName)


	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self,eventID, eventParameters):


		# Go through the member list and set initial occupation values, propogate result to subscribers.
		# count the members in each of our lists to determine which event we should relay
		#     i.e. if we have a 'occupiedFull' condition, it would take priority over unoccupiedDict

		if len(self.occupiedFullDict) == len(self.members):
			# highest priority... all members are reporting full occupancy
			newEvent = 'occupiedFull'
		elif len(self.unoccupiedFullDict) == len(self.members):
			# next highest priority... all members are reporting no occupancy
			newEvent = 'unoccupiedFull'
		elif len(self.occupiedDict):
			# next highest priority... one or some members are reporting occupancy
			newEvent = 'occupied'
		elif len(self.unoccupiedDict):
			# lowest priority... one or some members are reporting no occupancy
			newEvent = 'unoccupied'
		else:
			newEvent = 0			# no Events to deliver

		if newEvent:
			mmLib_Events.distributeEvent(self.deviceName, newEvent, 0, {})

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

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "occupied", str(self.occupiedDict))
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "occupiedFull", str(self.occupiedFullDict))
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "unoccupied", str(self.unoccupiedDict))
		theMessage = theMessage + "\n"

		theMessage = theMessage + '{0:<3} {1:<18} {2:<100}'.format(" ", "unoccupiedFull", str(self.unoccupiedFullDict))
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
		if len(self.unoccupiedFullDict) == len(self.members):
			# everything is unoccupied, send 'unoccupiedAll'
			newEvent = 'unoccupiedAll'
		else:
			# someone is occupied in the list, so send a simple 'occupied' event
			newEvent = 'unoccupied'

		mmLib_Events.distributeEvent(self.deviceName, newEvent, 0, {})	# deliver the event
		# update indigo variable
		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, EventToOccupiedStateDict.get(newEvent, 'Unknown'))

		self.scheduledDeactivationTimeSeconds = 0

		return 0	# do not continue timer


	#
	# receiveOccupationEvent - we received an activation event, process it
	#
	#			The type of occupation event we have been looking for is reported here. Based on the any/all mode factor,
	# 			determine if we should schedule the activation event to later occur in deviceTime above
	#
	def receiveOccupationEvent(self, theEvent, eventParameters):

		if theEvent in ['occupiedAll','unoccupiedAll']:
			self.occupationDisposition = 'full'
		else:
			self.occupationDisposition = eventParameters.get('occupationDisposition', 'full')

		theTimeString = time.strftime("%m/%d/%Y %I:%M:%S")

		if theEvent in occupationEvents:
			# a device showing occupation, process it.
			# put publisher into the proper list... self.occupiedDict, self.unoccupiedDict
			# subtract from the unoccupied list and add to the occupied list

			if self.unoccupiedRelayDelaySeconds:							# if unoccupied timer is running, stop it
				mmLib_Low.cancelDelayedAction(self.unoccupiedTimerProc)		# This handles exception so it will cancel only if it exists
				self.scheduledDeactivationTimeSeconds = 0

			#with suppress(KeyError) : del self.unoccupiedDict[eventParameters['publisher']]				# no longer unoccupied
			try:
				del self.unoccupiedDict[eventParameters['publisher']]									# no longer unoccupied
			except:
				pass
			try:
				del self.unoccupiedFullDict[eventParameters['publisher']]  # by definition, can no longer be fully occupied
			except:
				pass

			self.occupiedDict[eventParameters['publisher']] = theTimeString				# definitely occupied


			if self.occupationDisposition == 'full':
				self.occupiedFullDict[eventParameters['publisher']] = theTimeString		# this time, fully occupied
			else:
				#with suppress(KeyError): del self.occupiedFullDict[eventParameters['publisher']]		# no longer fully occupied
				try:
					del self.occupiedFullDict[eventParameters['publisher']]  # no longer fully occupied
				except:
					pass


			if len(self.occupiedFullDict) == len(self.members):
				# All members are occupied full, send 'occupiedAll'
				newEvent = 'occupiedAll'
			else:
				# someone is not occupied in the member list, so send a simple 'unoccupied' event
				newEvent = 'occupied'

			mmLib_Events.distributeEvent(self.deviceName, newEvent, 0, {})
			mmLib_Low.setIndigoVariable(self.occupationIndigoVar, EventToOccupiedStateDict.get(newEvent, 'Unknown'))

		else:
			# a device has sent an Unoccupied Event. Now it could be that the occupants have just been still for a bit, so give them a chance to
			# move around as directed by unoccupiedRelayDelaySeconds

			# put the publisher in the right lists

			#with suppress(KeyError): del self.occupiedFullDict[eventParameters['publisher']]  		# no longer fully occupied full for sure
			try:
				del self.occupiedFullDict[eventParameters['publisher']]  # no longer fully occupied full for sure
			except:
				pass
			self.unoccupiedDict[eventParameters['publisher']] = theTimeString  		# its at least partially unoccupied

			if self.occupationDisposition == 'full':
				#with suppress(KeyError): del self.occupiedDict[eventParameters['publisher']]  		# also fully unoccupied, so subtract from occupied dict as well
				self.unoccupiedFullDict[eventParameters['publisher']] = theTimeString		# this time, fully occupied
				try:
					del self.occupiedDict[eventParameters['publisher']]  # by definition, cann no longer be occupied
				except:
					pass

			# now distribute the proper unoccupied events for any subscribers (delay as necessary)

			# relay the event or set a timer to do so
			if not self.unoccupiedRelayDelaySeconds:
				self.unoccupiedTimerProc({})
			else:
				mmLib_Low.registerDelayedAction({'theFunction': self.unoccupiedTimerProc, 'timeDeltaSeconds': self.unoccupiedRelayDelaySeconds, 'theDevice': self.deviceName, 'timerMessage': "unoccupiedTimerProc"})
				self.scheduledDeactivationTimeSeconds = int(time.mktime(time.localtime()) + self.unoccupiedRelayDelaySeconds)


		return 0





