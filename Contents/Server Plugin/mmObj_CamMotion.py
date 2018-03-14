__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

# import json
#import os
#import traceback
from datetime import datetime

import indigo
import mmLib_Log
import mmLib_Low
import mmComm_Indigo
import mmObj_Motion
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
import mmComm_Insteon


######################################################
#
# mmCamMotion - SubModel of multisensorDevice above
#
######################################################
class mmCamMotion(mmObj_Motion.mmMotion):

	#
	# __init__
	#
	def __init__(self, theDeviceParameters):

		self.currentOnState = False	# we have to assume we have no motion to start with (cameras dont save a motion state)

		super(mmCamMotion, self).__init__(theDeviceParameters)  # Initialize Base Class

		self.influentialLights = filter(None, theDeviceParameters["influentialLights"].split(';'))

		self.supportedCommandsDict.update({'motionEvent': self.camMotionEvent})

		self.exclusionLights = filter(None, theDeviceParameters["exclusionLights"].split(';'))

		# A camera is not a true indigo device (its virtual), so we have to maintain a credible lastUpdate time ourselves...
		# Cameras have a static 30 second timeout imposed by come code below, so since we dont know when the last time the camera saw motion, we have to guess..
		# We are claiming above that the camera is not detecting movement, so lets make sure setInitialOccupiedState below will back us up on that...
		# To do that we claim that the last update was "minMovement" minutes ago (converted to seconds), then the math in setInitialOccupiedState will work out the rest.
		self.lastUpdateTimeSeconds = int(time.mktime(time.localtime()) - (int(self.minMovement) * 60))


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
	# setInitialOccupiedState - check to see if the area is occupied or not, dispatch events accordingly
	#
	def setInitialOccupiedState(self):

		#originalOccupiedState = self.occupiedState

		super(mmCamMotion, self).setInitialOccupiedState()  # the base class just keeps track of the time since last change
		#mmLib_Log.logForce("### setInitialOccupiedState for " + self.deviceName + " currentOccupiedState is " + str(self.occupiedState) + ". Original On State and Occupancy State was " + str(self.currentOnState) + " and " + str(originalOccupiedState))

		if self.currentOnState == True:
			self.processMotionEventOn()


	def getOnState(self):

		return(self.currentOnState)

	#
	# getSecondsSinceUpdate - how many seconds since the device has changed state
	#	This normally happens in Indigo.py, but alas, this is not a true indigo device (its virtual)
	#
	def getSecondsSinceUpdate(self):
		# mmLib_Log.logForce("###    Returning secondsSinceLastUpdate for " + self.deviceName + " of " + str((time.mktime(time.localtime()) - self.lastUpdateTimeSeconds)))
		return int(time.mktime(time.localtime()) - self.lastUpdateTimeSeconds)


	def getInfluentialLoadChangeDelta(self):
		# go through the influential load devices and look for the most recent on/off change
		theDeltaTime = 100000

		for devName in self.influentialLights:
			try:
				theDev = mmLib_Low.MotionMapDeviceDict[devName]
				timeDeltaStruct = (datetime.now() - theDev.theIndigoDevice.lastChanged)
				timeDelta = timeDeltaStruct.seconds
				# Only care when lights are going off... If a light goes on and makes another light go on... thats OK
				if theDev.theIndigoDevice.onState == True:
					# we dont care about this light for now, it is on so OK if we dont report it on the influential list
					continue
				# mmLib_Log.logForce("=== " + self.deviceName + "\'s Time delta for " + devName + " is: " + str(timeDelta))
			except:
				mmLib_Log.logForce(self.deviceName + " Check Load Devices... No Such device " + str(devName))
				continue

			if timeDelta < theDeltaTime: theDeltaTime = timeDelta

		# mmLib_Log.logForce(self.deviceName + " === Lowest time delta is: " + str(theDeltaTime))

		return(theDeltaTime)



	# Add the motion stop event for the camMotionEvent below. And process the event
	def	processMotionEventOn(self):

		mmLib_Log.logForce("### Motion Event (ON) for " + self.deviceName)
		# mmLib_Log.logForce("   Camera Info: \n" + str(camDev))
		self.currentOnState = True

		origDev = mmLib_Low.anIndigoDev(False, self.deviceName)
		newDev = mmLib_Low.anIndigoDev(True, self.deviceName)

		self.deviceUpdated(origDev, newDev)

		mmLib_Low.registerDelayedAction(
			{'theFunction': self.camMotionTimeout, 'timeDeltaSeconds': 30, 'theDevice': self.deviceName,
			 'timerMessage': "camMotionTimeout", 'offTimerType': "Timeout"})



	#
	# camMotionEvent
	# we only support motion detected command, then the motion stop is implied 30 seconds later
	#
	def camMotionEvent(self, theCommandParameters):

		# If we are still processing a motion event... debounce it, dont do anything

		try:
			timeForNonMotion = mmLib_Low.delayedFunctionKeys[self.camMotionTimeout]
		except:
			timeForNonMotion = 0

		if( timeForNonMotion ):
			# Ignore the phantom transition/motion due to light change
			mmLib_Log.logForce(" === Debouncing motion on " + self.deviceName + " we havent had a motionOff event yet")
			return('Dque')

		# At night, If the motion is likely a result of a nearby influential light, exit
		if indigo.variables['MMDayTime'].value == 'false':
			deltaTime = self.getInfluentialLoadChangeDelta()

			if( deltaTime < 6 ):
				# Ignore the phantom transition/motion due to light change
				mmLib_Log.logForce(" === Ignoring phantom motion on " + self.deviceName + " because recent transition of influential light occurred " + str(deltaTime) + " seconds ago.")
				return('Dque')

		# If any of the exclusion lights are on, exit
		for aLight in self.exclusionLights:
			try:
				lightDev = indigo.devices[aLight]
				if lightDev.onState == True:
					mmLib_Log.logForce( " === Ignoring motion on " + self.deviceName + " because exclusion light " + lightDev.name + " is already on.")
					return('Dque')
			except:
				mmLib_Log.logWarning(self.deviceName + " is referencing an unknown exclusion light named " + aLight + ".")

		try:
			camDev = indigo.devices[theCommandParameters["theCam"]]
		except:
			camDev = "Unknown"

		self.processMotionEventOn()

		return('Dque')		# we are complete... dequeue the command (if async)


	def camMotionTimeout(self, theParameters):

		mmLib_Log.logForce("### Motion Event (Implied OFF) for " + self.deviceName + ".")
		self.currentOnState = False
		origDev = mmLib_Low.anIndigoDev(True,self.deviceName)
		newDev = mmLib_Low.anIndigoDev(False,self.deviceName)

		self.deviceUpdated(origDev, newDev)

		#self.receivedCommandLow(mmComm_Insteon.kInsteonOff)  # kInsteonOff = 19

		return(0)


