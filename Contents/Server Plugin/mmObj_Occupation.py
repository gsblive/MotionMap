
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
import mmComm_Indigo
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections


######################################################
#
# mmOccupation - Virtual Device used for Scene commands
#
######################################################
class mmOccupation(mmComm_Indigo.mmIndigo):


	def __init__(self, theDeviceParameters):
		super(mmOccupation, self).__init__(theDeviceParameters)
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.occupationEvent = theDeviceParameters["occupationEvent"]
			self.when = theDeviceParameters["when"]
			self.mode = theDeviceParameters["mode"]
			self.actionControllers = theDeviceParameters["actionControllers"].split(';')  # Can be a list, split by semicolons... normalize it into a proper list
			self.actionControllerCount = len(self.actionControllers)
			self.activateAction = theDeviceParameters["activateAction"]
			self.activateDelaySeconds = int(theDeviceParameters["activateDelayMinutes"]) * 60
			if self.occupationEvent == 'occupied':
				# We have to be careful that the actionControllers dont become unoccupied before our actionEvents get a chance to run, so set the floor for the activateDelay
				occupancyTimeout =  mmLib_Low.calculateControllerOccupancyTimeout(self.actionControllers, 'lowest') * 60
				if occupancyTimeout < self.activateDelaySeconds:
					mmLib_Log.logForce("**** mmOccupation " + self.deviceName + " ActivateDelay is too high for actionControllers, resetting to " + str(occupancyTimeout/60))
					self.activateDelaySeconds = occupancyTimeout
			self.deactivateAction = theDeviceParameters["deactivateAction"]
			self.deactivateDelaySeconds = int(theDeviceParameters["deactivateDelayMinutes"]) * 60
			self.scheduledDeactivationTime = 0
			self.scheduledActivationTime = 0
			self.isActive = 0

			if self.activateDelaySeconds:
				self.activationDelayTimerFrequency = self.activateDelaySeconds/2

			if self.deactivateDelaySeconds:
				self.deactivationDelayTimerFrequency = self.deactivateDelaySeconds/2

			mmLib_Low.subscribeToControllerEvents(self.actionControllers, [self.occupationEvent], self.receiveActivationEvent)

			# Subscribe to unlatch events in all cases for debounce (the opposite of the requested occupancy event)
			if self.occupationEvent == 'occupied': mmLib_Low.subscribeToControllerEvents(self.actionControllers, ['unoccupied'], self.receiveDeactivationEvent)
			elif self.occupationEvent == 'unoccupied': mmLib_Low.subscribeToControllerEvents(self.actionControllers, ['occupied'], self.receiveDeactivationEvent)
			elif self.occupationEvent == 'on': mmLib_Low.subscribeToControllerEvents(self.actionControllers, ['off'], self.receiveDeactivationEvent)
			elif self.occupationEvent == 'off': mmLib_Low.subscribeToControllerEvents(self.actionControllers, ['on'], self.receiveDeactivationEvent)
			else: mmLib_Log.logForce("**** mmOccupation " + self.deviceName + " Initialization: Illegal Event type " + str(self.occupationEvent))

			self.monitorGroup = []

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

		nItems = len(self.monitorGroup)

		if self.mode == 'any':
			mmLib_Log.logForce("mmOccupation \'" + self.deviceName + "\' is monitoring an \'" + self.occupationEvent + "\' controller list for any items. It currently contains " + str(self.monitorGroup))
		else:
			mmLib_Log.logForce("mmOccupation \'" + self.deviceName + "\' is monitoring an \'" + self.occupationEvent + "\' controller list for " + str(self.actionControllerCount) + " items. It currently contains " + str(nItems) + " : " + str(self.monitorGroup))

		mmLib_Log.logForce("  activation time and deactivation time are: " + str(self.scheduledActivationTime) + " and " + str(self.scheduledDeactivationTime) + ".")

		if self.isActive:
			mmLib_Log.logForce("  Indigo Action Group \'" + self.activateAction + "\' is currently Active" )
		else:
			mmLib_Log.logForce("  Indigo Action Group \'" + self.activateAction + "\' is currently Inactive" )

		if self.activateAction:
			if self.scheduledActivationTime:
				theTimeString = mmLib_Low.minutesAndSecondsTillTime(self.scheduledActivationTime)
				mmLib_Log.logForce("  It is scheduled to become Active and it\'s Activation Indigo Action Group \'" + self.activateAction + "\' is scheduled to run in " + str(theTimeString) + "." )
			else:
				mmLib_Log.logForce("  It\'s Activation Indigo Action Group \'" + self.activateAction + "\' is not currently scheduled to run" )
		else:
			mmLib_Log.logForce("  ERROR: No Activation Routine listed. " )
			
		if self.deactivateAction:
			if self.scheduledDeactivationTime:
				mmLib_Log.logForce("  It is scheduled to become Inactive and it\'s Deactivation Indigo Action Group \'" + self.deactivateAction + "\' is scheduled to run in " + str(self.scheduledDeactivationTime-time.mktime(time.localtime())) + " seconds. " )
			else:
				mmLib_Log.logForce("  It\'s Deactivation Indigo Action Group \'" + self.deactivateAction + "\' is not currently scheduled to run" )
		else:
			mmLib_Log.logForce("  It has no Deactivation Routine listed, will become Inactive in " + str(self.scheduledDeactivationTime-time.mktime(time.localtime())) + " seconds. " )


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	#
	# doActivation - Run activation Routine
	#
	def doActivation(self, parameters):
		if not self.isActive and self.activateAction :
			indigo.actionGroup.execute(self.activateAction)
		self.isActive = 1
		self.scheduledActivationTime = 0

	#
	# doDeactivation - Run Deactivation Routine
	#
	def doDeactivation(self, parameters):
		if self.isActive and self.deactivateAction :
			indigo.actionGroup.execute(self.deactivateAction)
		self.isActive = 0
		self.scheduledDeactivationTime = 0


	#
	# receiveActivationEvent - we received an activation event, process it
	#
	#			The type of occupation event we have been looking for is reported here. Based on the any/all mode factor,
	# 			determine if we should schedule the activation event to later occur in deviceTime above
	#
	def receiveActivationEvent(self, theEvent, theControllerDev):

		processIt = 0

		if theControllerDev.deviceName not in self.monitorGroup:
			self.monitorGroup.append(theControllerDev.deviceName)
			mmLib_Log.logVerbose("mmOccupation \'" + self.deviceName + "\' received an " + str(theEvent) + " event from " + theControllerDev.deviceName + ". " +  str(self.occupationEvent) + " list is now: " + str(self.monitorGroup))

		if not self.scheduledActivationTime:
			mmLib_Log.logVerbose("   mmOccupation event was not latched, continuing processing")
			if self.mode == 'any':
				processIt = 1
			elif self.mode == 'all':
				if len(self.monitorGroup) == self.actionControllerCount:
					processIt = 1
			else:
				mmLib_Log.logForce("mmOccupation \'" + self.deviceName + "\' illegal mode type \'" + str(self.mode) + "\'")

			if processIt:
				self.scheduledDeactivationTime = 0
				mmLib_Low.cancelDelayedAction(self.doDeactivation)
				if not self.activateDelaySeconds:
					self.doActivation({})
				else:
					mmLib_Low.registerDelayedAction({'theFunction': self.doActivation, 'timeDeltaSeconds': self.activateDelaySeconds, 'theDevice': self.deviceName, 'timerMessage': "doActivation"})


	#
	# receiveDeactivationEvent - we received a deactivation event, process it
	#
	#			The opposite of our occupation is reported here. Based on the any/all mode factor,
	# 			determine if the occupation has now ended and if we should schedule any deactivation event to later occur in deviceTime above
	#
	def receiveDeactivationEvent(self, theEvent, theControllerDev):

		processIt = 0

		try:
			self.monitorGroup.remove(theControllerDev.deviceName)
			mmLib_Log.logVerbose("mmOccupation \'" + self.deviceName + "\' received " + str(theEvent) + " event from " + theControllerDev.deviceName + ". " +  str(self.occupationEvent) + " list is now: " + str(self.monitorGroup))
		except:
			mmLib_Log.logVerbose("   mmOccupation event was not in the monitorGroup, stop processing")
			return

		if not self.scheduledDeactivationTime:

			if self.mode == 'all':
				#if we receive any deActivation event, we can deactivate
				processIt = 1
			elif self.mode == 'any':
				# the list has to become empty to deactivate
				if not self.monitorGroup:
					processIt = 1
			else:
				mmLib_Log.logForce("mmOccupation \'" + self.deviceName + "\' illegal mode type \'" + str(self.mode) + "\'")

			if processIt:
				self.scheduledActivationTime = 0
				mmLib_Low.cancelDelayedAction(self.doActivation)
				if not self.deactivateDelaySeconds:
					self.doDeactivation({})
				else:
					mmLib_Low.registerDelayedAction({'theFunction': self.doDeactivation, 'timeDeltaSeconds': self.deactivateDelaySeconds, 'theDevice': self.deviceName, 'timerMessage': "doDeactivation"})




