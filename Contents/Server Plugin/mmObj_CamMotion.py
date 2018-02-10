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

class anIndigoDev:

	def __init__(self, theValue, theName):
		self.onState = theValue
		self.name = theName

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

		self.currentOnState = False

		super(mmCamMotion, self).__init__(theDeviceParameters)  # Initialize Base Class

		self.influentialLights = filter(None, theDeviceParameters["influentialLights"].split(';'))

		self.supportedCommandsDict.update({'motionEvent': self.camMotionEvent})

		self.exclusionLights = filter(None, theDeviceParameters["exclusionLights"].split(';'))

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

	def getOnState(self):

		return(self.currentOnState)

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

		mmLib_Log.logForce("### Motion Event (ON) for " + self.deviceName)
		#mmLib_Log.logForce("   Camera Info: \n" + str(camDev))
		self.currentOnState = True

		origDev = anIndigoDev(False,self.deviceName)
		newDev = anIndigoDev(True,self.deviceName)

		self.deviceUpdated(origDev, newDev)

		mmLib_Low.registerDelayedAction({'theFunction': self.camMotionTimeout, 'timeDeltaSeconds': 30, 'theDevice': self.deviceName,'timerMessage': "camMotionTimeout", 'offTimerType': "Timeout"})
		return('Dque')		# we are complete... dequeue the command (if async)


	def camMotionTimeout(self, theParameters):

		mmLib_Log.logForce("### Motion Event (Implied OFF) for " + self.deviceName + ".")
		self.currentOnState = False
		origDev = anIndigoDev(True,self.deviceName)
		newDev = anIndigoDev(False,self.deviceName)

		self.deviceUpdated(origDev, newDev)

		#self.receivedCommandLow(mmComm_Insteon.kInsteonOff)  # kInsteonOff = 19

		return(0)


