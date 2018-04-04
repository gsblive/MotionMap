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

import indigo
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

######################################################
#
# mmCompanion - Companion Device, usually a dimmer or switch, not loadDevice, working as a set with a load Device
#
######################################################
class mmCompanion(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):

		super(mmCompanion, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.loadDeviceName = theDeviceParameters["loadDeviceName"]
			mmLib_Low.statisticsQueue.append(self)		# insert into request-status deque

			# we are going to republish our command events so the Load device can subscribe
			mmLib_Events.registerPublisher(['DevRcvCmd'], self.deviceName)

			# register for the indigo events we want

			#mmLib_Events.subscribeToEvents(['AtributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {}, self.deviceName)
			mmLib_Events.subscribeToEvents(['DevRcvCmd'], ['Indigo'], self.receivedCommandEvent, {} , self.deviceName)
			mmLib_Events.subscribeToEvents(['DevCmdComplete'], ['Indigo'], self.completeCommandEvent, {} , self.deviceName)
			mmLib_Events.subscribeToEvents(['DevCmdErr'], ['Indigo'], self.errorCommandEvent, {} , self.deviceName)

			# GB Fix Me subscribe on behalf of the Load Devices - This will be moved where it belongs in Load Device when we change the config file format to include companions with Load entry
			try:
				theLoadDevice = mmLib_Low.MotionMapDeviceDict[self.loadDeviceName]
				# Tell the load device to send updates messages to us VIA INDIGO COMMAND OVER THE WIRE (so the hardware displays the right brightness and on state)
				theLoadDevice.companions.append(self)
				mmLib_Events.subscribeToEvents(['DevRcvCmd'], [self.deviceName], theLoadDevice.receivedCommandEvent, {}, theLoadDevice.deviceName)
			except:
				mmLib_Log.logForce("Cannot add companion " + self.deviceName + " to loadDevice " + self.loadDeviceName + ", because loadDevice does not exist yet")


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
	# receivedCommand - we received a command from our companion device. There is a bug in the insteon code that causes companion fast-Ons to only tell the
	#					load device to perform a regular on. This causes the loadDevice's device-change event to only report the normal-on value (instead of the 100% value).
	#					The way we have to fix this is to issue a status request to the maseter after we get a fast-on from the companion. This method
	#					overrides normal behaviors to add code to perform this action.
	#
	def receivedCommandEvent(self, eventID, eventParameters ):
		theInsteonCommand = eventParameters['cmd']

		super(mmCompanion, self).receivedCommandEvent(eventID, eventParameters)  # Normal Base Class operation

		try:
			theCommandByte = theInsteonCommand.cmdBytes[0]
			if self.debugDevice: mmLib_Log.logForce("Companion " + self.deviceName + " received command " + str(theCommandByte))
		except:
			if self.debugDevice: mmLib_Log.logForce("Companion " + self.deviceName + " received command unrecognized by MotionMap")
			theCommandByte = "unknown"


		if self.loadDeviceName:
			if self.debugDevice: mmLib_Log.logForce("Companion " + self.deviceName + " attempting event distribution for commandByte: " + str(theCommandByte))
			mmLib_Events.distributeEvent(self.deviceName, eventID, 0, eventParameters)	# distribute to all subscribers

		return




	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################




