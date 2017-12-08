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
			mmLib_Low.statusQueue.append(self)		# insert into request-status deque

			# append to the loadDevice's companion list
			try:
				theLoadDevice = mmLib_Low.MotionMapDeviceDict[self.loadDeviceName]
				theLoadDevice.companions.append(self)
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
	def receivedCommand(self, theInsteonCommand ):

		super(mmCompanion, self).receivedCommand(theInsteonCommand)  # Normal Base Class operation
		try:
			theCommandByte = theInsteonCommand.cmdBytes[0]
			mmLib_Log.logVerbose("Companion " + self.deviceName + " received command " + str(theCommandByte))
		except:
			mmLib_Log.logVerbose("Companion " + self.deviceName + " received command unrecognized by MotionMap")
			theCommandByte = "unknown"

		theLoadDevice = 0
		if self.loadDeviceName:
			try:
				theLoadDevice = mmLib_Low.MotionMapDeviceDict[self.loadDeviceName]
				if theCommandByte in [mmLib_Low.kInsteonOn, mmLib_Low.kInsteonOff, mmLib_Low.kInsteonOnFast, mmLib_Low.kInsteonOffFast]:
					newBrightness = self.getBrightness()
					mmLib_Log.logVerbose("Device " + self.deviceName + " brightness is now " + str(newBrightness) + " Update Maseter " + self.loadDeviceName + " to " + str(newBrightness))
					theLoadDevice.queueCommand({'theCommand':'brighten', 'theDevice':self.loadDeviceName, 'theValue':newBrightness, 'retry':2})
			except:
				mmLib_Log.logVerbose("Device " + self.deviceName + " cannot queue status request for loadDevice " + self.loadDeviceName + ", because loadDevice does not exist")

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):
		super(mmCompanion, self).deviceUpdated(origDev, newDev)  # the base class just keeps track of the time since last change
		# do companion update behavior
		return(0)

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmCompanion: " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmCompanion: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmCompanion: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process


