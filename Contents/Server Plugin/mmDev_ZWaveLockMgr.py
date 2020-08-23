__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

# import json
# import os
# import traceback
# import datetime

try:
	import indigo
except:
	pass

import mmLib_Log
import mmLib_Low
import mmLib_Events
import mmComm_Insteon
import mmObj_OccupationGroup
import mmComm_Indigo
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
import random
import datetime

kLoadDeviceTimeSeconds = 60
kBlackOutTimeSecondsAfterOff = 10


######################################################
#
# mmZLockMgr - Z-Wave Lock Manager
#
######################################################
class mmZLockMgr(mmComm_Indigo.mmIndigo):

	def __init__(self, theDeviceParameters):

		super(mmZLockMgr, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.debugDevice: mmLib_Log.logForce("Initializing " + self.deviceName )
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.doorLocks = theDeviceParameters["lockDeviceNames"].split(';')  # Can be a list, split by semicolons... normalize it into a proper list

			for aLock in self.doorLocks:
				theLockDevice = mmLib_Low.MotionMapDeviceDict.get(aLock,0)
				if theLockDevice:
					mmLib_Log.logForce( self.deviceName + " Found Lock Device \'" + str(aLock) + "\'.")
				else:
					mmLib_Log.logForce( self.deviceName + " ### Could not find Lock Device \'" + str(aLock) + "\'.")


	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################

	#
	# deviceUpdatedEvent -
	#
	#
	# deviceUpdatedEvent - tell the companions what to do
	#
	def deviceUpdatedEvent(self, eventID, eventParameters):

		return (0)

	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	def completeCommandEvent(self, eventID, eventParameters):
		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " received complete Command Event from \'" + eventParameters['publisher'] + "\'.")
		return (0)

	#
	# receivedCommand - we received a command from our device. The base object will do most of the work... we want to process special commands here, like bedtime mode
	#
	def receivedCommandEvent(self, eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " received command event from \'" + eventParameters['publisher'] + "\'.")

		return (0)

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	def errorCommandEvent(self, eventID, eventParameters  ):
		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " received error command event from \'" + eventParameters['publisher'] + "\'.")
		return (0)

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	# printLockInfo - turn bedtime mode on if its Nighttime
	#
	def printLockInfo(self, theCommandParameters):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Entering printLockInfo")
		return (0)

	#
	# 	devStatus - print the status of the device
	#
	def devStatus(self, theCommandParameters):

		return (0)

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################

	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self, eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " Entering completeInit." )

		mmLib_Low.registerDelayedAction({'theFunction': self.PeriodicTime,
											 'timeDeltaSeconds': 60*60,
											 'theDevice': self.deviceName,
											 'timerMessage': "PeriodicTime"})

		return 0

	def PeriodicTime(self, eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " Entering PeriodicTime." )

		return 0
