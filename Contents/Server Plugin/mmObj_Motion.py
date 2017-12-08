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
import mmComm_Insteon
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections

######################################################
#
# mmMotion - Motion Sensor Device
#
######################################################
class mmMotion(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):

		# set things that must be setup before Base Class
		self.lastOnTimeSeconds = 0
		self.lastOffTimeSeconds = 0

		super(mmMotion, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.maxMovement = theDeviceParameters["maxMovement"]	# the amount of time (in minutes) that the motion sense can stay "ON" for sustained occupancy
			self.minMovement = theDeviceParameters["minMovement"]	# the amount of time (in minutes) that motion sense is "OFF" that constitutes no occupancy
			mmLib_Low.mmRegisterForTimer(self.deviceTime, 60)		# give us a kick every minute
			mmLib_Low.controllerDeque.append(self)		# insert into device-time deque
			self.occupiedState = 2
			self.supportedCommandsDict = {}
			self.controllerMissedCommandCount = 0

			self.onDeque = deque()				# make responder deque for 'on' events
			self.offDeque = deque()				# make responder deque for 'off' events
			self.occupiedDeque = deque()		# make responder deque for 'occupied' events
			self.unoccupiedDeque = deque()		# make responder deque for 'unoccupied' events

			self.supportedCommandsDict.update({})


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
	# getOccupancyTimeout - return an int that indicates the number of minutes that must transpire before a non-occupancy state is assumed
	#
	def getOccupancyTimeout(self):
		return int(self.minMovement)

	#
	# setOnOffLine - select motionsensor's online/offline state
	#
	#	we support the following requestedStates:
	#
	#	'on'			The motion sensor received an on signal
	#	'off'			The motion sensor received an off signal
	def setOnOffLine(self, requestedState):

		if self.onlineState != requestedState:
			mmLib_Log.logForce("Setting " + self.deviceName + " onOfflineState to " + requestedState)

			if self.onlineState == 'on':		#force occupiedstate to match the new online state
				self.dispatchEventToDeque(self.occupiedDeque, 'occupied')				# process occupancy
			else:
				self.dispatchEventToDeque(self.unoccupiedDeque, 'unoccupied')				# process unoccupied

		self.onlineState = requestedState

		return(0)
	#
	# addToControllerEventDeque - add theHandler to be called when any of the events listed in theEvents occur
	#
	#	we support the following events:
	#
	#	'on'			The motion sensor received an on signal
	#	'off'			The motion sensor received an off signal
	#	'occupied'		The motion sensor has determined the area is occupied
	#	'unoccupied'	The motion sensor has determined the area is unoccupied
	#
	#	theHandler format must be
	#		theHandler(theEvent, theControllerDev) where:
	#
	#		theEvent is the text representation of a single event type listed above
	#		theControllerDev is the mmInsteon of the controller that detected the event
	#
	def addToControllerEventDeque(self, theEvents, theHandler):
		for theEvent in theEvents:
			mmLib_Log.logDebug("Adding handler " + str(theHandler) + " to " + theEvent + " Deque of " + self.deviceName)
			if theEvent == 'on':
				self.onDeque.append(theHandler)				# insert into 'on' deque
			elif theEvent == 'off':
				self.offDeque.append(theHandler)			# insert into 'off' deque
			elif theEvent == 'occupied':
				self.occupiedDeque.append(theHandler)		# insert into 'occupied' deque
			elif theEvent == 'unoccupied':
				self.unoccupiedDeque.append(theHandler)		# insert into 'unoccupiedDeque' deque
			else:
				mmLib_Log.logVerbose("Invalid event " + theEvent + " requested from " + self.deviceName)

		return(0)

	#
	# dispatchEventToDeque - Touch all devices in the deque given.
	#	theQueue, theEvent: as defined in theHandler info at addToControllerEventDeque()
	#
	def dispatchEventToDeque(self, theQueue, theEvent):

		for aHandler in theQueue:
			aHandler(theEvent, self)

		return(0)

	#
	# getSecondsSinceState - how many seconds since the device was in the given on/off state
	#
	def getSecondsSinceState(self, theState):
		if self.onlineState == 'off': return(int(60*60*24))	# default to a high number if the device is offline

		if theState == 'on':
			theStateTime = self.lastOnTimeSeconds
		else:
			theStateTime = self.lastOffTimeSeconds

		return(int(time.mktime(time.localtime()) - theStateTime))

	#
	# setLastUpdateTimeSeconds - note the time when the device changed state
	#
	def setLastUpdateTimeSeconds(self):

		super(mmMotion, self).setLastUpdateTimeSeconds()  # Call Base Class

		if self.theIndigoDevice.onState == True:
			self.lastOnTimeSeconds = self.lastUpdateTimeSeconds
		else:
			self.lastOffTimeSeconds = self.lastUpdateTimeSeconds
		return()

	#
	# deviceTime - do device housekeeping... this should happen once a minute
	#
	def deviceTime(self):

		mmLib_Log.logDebug("====Running Motion Device Time for " + self.deviceName)

		timeDeltaSeconds = self.getSecondsSinceUpdate()
		timeDeltaMinutes = int(timeDeltaSeconds/60)

		if self.theIndigoDevice.onState == True:
			if int(timeDeltaMinutes) < int(self.maxMovement):
				newOccupiedState = True
			else:
				newOccupiedState = False
		else:
			if int(timeDeltaMinutes) < int(self.minMovement):
				newOccupiedState = True
			else:
				newOccupiedState = False

		if self.occupiedState == 2 or self.occupiedState != newOccupiedState:
			self.occupiedState = newOccupiedState
			mmLib_Log.logVerbose("Occupied State for " + self.deviceName + " has changed to " + str(self.occupiedState) + " OnState, Min, Max, Current: " + str(self.theIndigoDevice.onState) + " " + str(self.minMovement) + " " + str(self.maxMovement) + " " + str(timeDeltaMinutes))
			#
			# Tell all the loadDevices about the occupancy change

			if self.onlineState == 'on':
				if newOccupiedState == True:	# it has acctually just become true
					self.dispatchEventToDeque(self.occupiedDeque, 'occupied')				# process occupancy
				else:
					self.dispatchEventToDeque(self.unoccupiedDeque, 'unoccupied')				# process unoccupied

		return(0)

	#
	# receivedCommandLow - we received a command from our motion Sensor, process it
	#
	def receivedCommandLow(self, theCommandByte ):

		# process Motion here
		self.deviceTime()		# this will process occupancy events
		if theCommandByte == 17:	#kInsteonOn = 17
			self.dispatchEventToDeque(self.onDeque, 'on')							# process on
		elif theCommandByte == 19:	#kInsteonOff = 19
			self.dispatchEventToDeque(self.offDeque, 'off')							# process off
		else:
			mmLib_Log.logVerbose("Invalid insteon event received for " + self.deviceName + " of " + str(theCommandByte))

		return(0)

	#
	# receivedCommand - we received a command from our motion Sensor, process it
	# All processing actually comes from the update routine below... this is here for debugging only
	#
	def receivedCommand(self, theInsteonCommand ):

		# process Insteon Motion command received here
		try:
			theCommandByte = theInsteonCommand.cmdBytes[0]
			mmLib_Log.logVerbose("Motion Sensor " + self.deviceName + " received command " + str(theCommandByte))
		except:
			mmLib_Log.logVerbose("Motion Sensor " + self.deviceName + " received command unrecognized by MotionMap")
			theCommandByte = "unknown"

		# In order for us to be able to respond to server events, we have to handle this event in the deviceUpdated Routine below
		# and not call receivedCommandLow from here. This routine is present in case we need to handle direct events sometime in the future.

		return(0)

	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):


		if self.onlineState == 'on':

			if origDev.onState != newDev.onState:
				mmLib_Log.logVerbose(newDev.name + ": Motion Onstate = " + str(newDev.onState))
				super(mmMotion, self).deviceUpdated(origDev, newDev)  # the base class just keeps track of the time since last change
				self.controllerMissedCommandCount = 0			# Reset this because it looks like are controller is alive (battery report uses this)
				if newDev.onState == True:
					self.receivedCommandLow( 17 )	#kInsteonOn = 17
				else:
					self.receivedCommandLow(19 )	#kInsteonOff = 19
			else:
				mmLib_Log.logDebug(newDev.name + ": Received duplicate command: Onstate = " + str(newDev.onState))


		return(0)


	#
	# loadDeviceNotificationOfOn - called from Load Devices
	# A load device associated with this motion sensor was manually turned on, note it for Battery performance tests
	#
	def loadDeviceNotificationOfOn(self):
		self.controllerMissedCommandCount = self.controllerMissedCommandCount + 1

		return(0)


	#
	# checkBattery - report the status of this device's battery
	# 	FORCE it to the log
	#	returns 0 if good battery, nonzero if bad
	#
	def checkBattery(self):

		addString = ""

		# if the device is ON, see if has been on too long
		if self.controllerMissedCommandCount > mmLib_Low.MOTION_MAX_MISSED_COMMANDS:
			newString =  self.deviceName + " has missed " + str(self.controllerMissedCommandCount) + " events. The battery is likely dead"
			addString = addString + newString + "\n"
			mmLib_Log.logForce(newString)

		if self.theIndigoDevice.onState == True:
			if self.getSecondsSinceUpdate() > mmLib_Low.MOTION_MAX_ON_TIME:
				newString =  self.deviceName + " has been on for " + str(int(self.getSecondsSinceUpdate()) / int(60*60)) + " hours. The device may need to be reset or the battery may be dead"
				addString = addString + newString + "\n"
				mmLib_Log.logForce(newString)
				indigo.device.turnOff(self.devIndigoID)	# doesnt honor the unresponsive flag because this just sets statte in indigo (no command is sent to the device)
		else:
			if self.getSecondsSinceUpdate() > mmLib_Low.MOTION_MAX_OFF_TIME:
				newString =  self.deviceName + " has been off for " + str(int(self.getSecondsSinceUpdate()) / int(24*60*60)) + " days. The device may need to be reset or the battery may be dead "
				addString = addString + newString + "\n"
				mmLib_Log.logForce(newString)

		return(addString)
