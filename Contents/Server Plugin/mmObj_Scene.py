

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

######################################################
#
# mmScene - Virtual Device used for Scene commands
#
######################################################
class mmScene(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):
		super(mmScene, self).__init__(theDeviceParameters)
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " processing initialization.")

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " theDeviceParameters are: " + str(theDeviceParameters))

		self.onControllers = [_f for _f in theDeviceParameters["onControllers"].split(';') if _f]  # Can be a list, split by semicolons... normalize it into a proper list
		self.sustainControllers = [_f for _f in theDeviceParameters["sustainControllers"].split(';') if _f]
		self.combinedControllers = self.onControllers + self.sustainControllers							# combinedControllers contain both sustainControllers and onControllers
		self.allControllerGroups = []

		if self.initResult == 0:

			#
			# Set object variables
			#

			self.sceneNumberDay = str(theDeviceParameters["sceneNumberDay"])
			self.sceneNumberNight = str(theDeviceParameters["sceneNumberNight"])

			self.devIndigoAddress = mmLib_Low.makeSceneAddress(self.sceneNumberDay + "/" + self.sceneNumberNight)
			mmLib_Log.logVerbose("Initializing Scene " + str(self.devIndigoAddress) + ": " + self.deviceName + ", " + self.devIndigoAddress + ", " + self.devIndigoID)
			self.members = theDeviceParameters["members"].split(';')  # Can be a list, split by semicolons... normalize it into a proper list
			self.expectedOnState = False

			self.supportedCommandsDict.update({'sceneOn': self.sendSceneOn, 'sceneOff': self.sendSceneOff, 'devStatus':self.devStatus})

			del self.supportedCommandsDict['sendStatusRequest']

			mmLib_Events.subscribeToEvents(['DevRcvCmd'], ['Indigo'], self.receivedCommandEvent, {} , self.deviceName)
			mmLib_Events.subscribeToEvents(['DevCmdComplete'], ['Indigo'], self.completeCommandEvent, {} , self.deviceName)
			mmLib_Events.subscribeToEvents(['DevCmdErr'], ['Indigo'], self.errorCommandEvent, {} , self.deviceName)

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


	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	# 	All commands in this section must have a single parameter theCommandParameters - a list of parameters
	# 	And all commands must be registered in self.supportedCommandsDict variable
	#
	######################################################################################

	#
	# devStatus - Print Status information for this device to the log
	#
	def	devStatus(self,theCommandParameters):
		mmLib_Log.logForce("sceneDevice status." + self.deviceName + " has no status handler routine.")

	#
	#  Send a Scene Off Request
	#
	def sendSceneOff(self, theCommandParameters):

		mmLib_Log.logVerbose("Issuing SceneOn " + self.deviceName)
		indigo.insteon.sendSceneOff(int(self.sceneNumberDay), sendCleanUps=False)	# does not honor unresponsive because this is not really a device
		self.expectedOnState = False

		return(0)

	#
	#  Send a Scene On Request
	#
	def sendSceneOn(self, theCommandParameters):

		mmLib_Log.logVerbose("Issuing SceneOn " + self.deviceName)
		if indigo.variables["isDaylight"].value == 'true':
			indigo.insteon.sendSceneOn(int(self.sceneNumberDay), sendCleanUps=False) # does not honor unresponsive because this isnt really a device
		else:
			if self.sceneNumberNight:
				indigo.insteon.sendSceneOn(int(self.sceneNumberNight),sendCleanUps=False)  # does not honor unresponsive because this isnt really a device

		self.expectedOnState = True

		return(0)

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################



	#
	#  Verify completion of a Scene Request
	#
	def verifyScene(self):

		verificationCommandsSent = 0

		for theMember in self.members:
			# if the expected ON state is not correct, enqueue a command to fix it
			try:
				mmMemberDev = mmLib_Low.MotionMapDeviceDict[theMember]
				if mmMemberDev.theIndigoDevice.onState != self.expectedOnState:
					mmLib_Log.logForce("While processing Scene " + self.deviceName + ", a Device didnt change: " + theMember)
					mmMemberDev.queueCommand({'theCommand':'onOffDevice', 'theDevice':theMember, 'theValue':self.expectedOnState, 'retry':2})
					verificationCommandsSent = verificationCommandsSent + 1
			except:
				mmLib_Log.logWarning("Scene " + self.deviceName + " references member that does not exist: " + theMember)

		if verificationCommandsSent == 0:
			mmLib_Log.logForce("No verifications were needed for Scene " + self.deviceName)

		return(0)

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
		self.sendSceneOn({})
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

		self.sendSceneOff({})

		return 0
