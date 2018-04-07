
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

resetEventMap = 	{
					'OccupiedPartial':['OccupiedAll','UnoccupiedAll'],
					'OccupiedAll':['UnoccupiedAll','OccupiedPartial'],
					'UnoccupiedAll':['OccupiedAll','OccupiedPartial'],
					'on':['off'],
					'off':['on']
					}

######################################################
#
# mmOccupation - Virtual Device used for Scene commands
#
######################################################
class mmOccupationAction(mmComm_Indigo.mmIndigo):


	def __init__(self, theDeviceParameters):
		super(mmOccupationAction, self).__init__(theDeviceParameters)
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.occupationEvent = theDeviceParameters["occupationEvent"]		# 'on', 'off', 'OccupiedPartial', 'OccupiedAll' or 'UnoccupiedAll'
			self.resetEvents = []
			self.allEvents = []
			self.resetEvents = resetEventMap.get(self.occupationEvent,0)

			if self.resetEvents:
				self.allEvents = self.resetEvents[:]
				self.allEvents.append(self.occupationEvent)
			else:
				mmLib_Log.logForce( self.deviceName + " Is initializing with unsupported event \'" + self.occupationEvent + "\'.")

			self.actionController = theDeviceParameters["actionController"]  			# can be an OccupationGroup
			self.activateAction = theDeviceParameters["activateAction"]
			self.isActive = 0

			# Subscribe to requested occupancy event
			if self.debugDevice: mmLib_Log.logForce( "  Indigo Action Group \'" + self.deviceName + "\' is requesting events " + str(self.allEvents) + " from " + self.actionController + ".")
			mmLib_Events.subscribeToEvents(self.allEvents, [self.actionController], self.receiveOccupationEvent, {}, self.deviceName)

			self.supportedCommandsDict.update({'devStatus':self.devStatus})


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

		if self.isActive:
			mmLib_Log.logForce("  Indigo Action Group \'" + self.activateAction + "\' is currently Active due to recent \'" + self.occupationEvent + "\' event." )
			mmLib_Log.logForce("    Currently waiting for \'" + self.resetEvents + "\' event before becoming eligible for activation again." )
		else:
			mmLib_Log.logForce( "mmOccupation \'" + self.deviceName + "\' is waiting for a \'" + self.occupationEvent + "\' event from " + str(self.actionController))




	#
	# receiveOccupationEvent - we received an activation event, process it
	#
	#			The type of occupation event we have been looking for is reported here. Based on the any/all mode factor,
	# 			determine if we should schedule the activation event to later occur in deviceTime above
	#
	def receiveOccupationEvent(self, theEvent, eventParameters):

		if self.debugDevice: mmLib_Log.logForce( "  Indigo Action Group \'" + self.deviceName + "\' received \'" + theEvent + "\' event from " + eventParameters['publisher'] + ".")

		if theEvent == self.occupationEvent:
			if not self.isActive:
				if self.activateAction: indigo.actionGroup.execute(self.activateAction)
				self.isActive = 1
		elif theEvent in self.resetEvents:
			self.isActive = 0
		else:
			mmLib_Log.logWarning("mmOccupation \'" + self.deviceName + "\' received an unsupported Event \'" + str(theEvent) + "\' from " + eventParameters['publisher'] + ".")

