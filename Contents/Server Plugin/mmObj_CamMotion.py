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
import mmLib_Events
import mmComm_Indigo
import mmObj_Motion
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
import mmComm_Insteon

############################################################################################
#
#	Note This MM Object is designed to be used with Indigo 7.4, Cynical SecuritySpy Plugin 2.4.3 with the following configuration
#
#	CamMotion Devices are reliant on the companion SecuritySpy DVR application AND the Cynical SecuritySpy Indigo plugin
#	Both of these apps must be installed and configured to provide camera events to Indigo... The two or more devices are:
#		Type: Cynical SecuritySpy
#		Model: Server
#		Settings: Host:[blank if running on the same computer as indigo] Port: 8002 [default] UserName and Password as defined in SecuritySpy Web Access
#
#		-and-
#
#		Type: Cynical SecuritySpy
#		Model: Camera
#		Settings: Select the SecuritySpy camera in this popup
#
#	To use this MM device, you have to make an Indigo Trigger that responds to:
#
#	Trigger:
#		Type: Cynical SecuritySpy Event [From Popup]
#		Event: Camera Motion
#		Settings:
#				Camera: Select the SecuritySpy Camera Name in this popup
#				Maximum Rate: 10 by default
#				Detection: Motion Capture (from popup)
#				Reason: Anything (from popup)
#
#	Condition: As needed
#
#	Action:
#		Type: Server Action/Script and File Actions/Execute Script/(Python code below)
#
#indigo.server.log("=== Received Motion Event from CamName ===")
#mmId = indigo.variables["MMListenerName"].value
#mmPlugin = indigo.server.getPlugin(mmId)
#if mmPlugin.isEnabled():
#	mmPlugin.executeAction("executeMMCommand", deviceId=0, props={'theCommand':'motionEvent','theDevice':'CamHouseParkingMotion','theCam':"CamHouseParking",'theMode':'IMMED'})
#else:
#	indigo.server.log("MotinMap not Enabled")
#
############################################################################################


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
		if self.debugDevice: mmLib_Log.logForce( " === Initializing " + self.deviceName + ".")

		self.influentialLights = filter(None, theDeviceParameters["influentialLights"].split(';'))
		self.influentialTimeout = int(theDeviceParameters["influentialTimeout"])

		self.supportedCommandsDict.update({'motionEvent': self.camMotionEvent})

		self.exclusionLights = filter(None, theDeviceParameters["exclusionLights"].split(';'))
		self.minMovementSeconds = (int(self.minMovement) * 60)

		# A camera is not a true indigo device (its virtual), so we have to maintain a credible lastUpdate time ourselves...
		# Cameras have a static "minMovementSeconds" timeout imposed by come code below, so since we dont know when the last time the camera saw motion, we have to guess..
		# We are claiming above that the camera is not detecting movement, so lets make sure setInitialOccupiedState below will back us up on that...
		# To do that we claim that the last update was "minMovement" minutes ago (converted to seconds), then the math in setInitialOccupiedState will work out the rest.
		self.lastUpdateTimeSeconds = int(time.mktime(time.localtime()) - self.minMovementSeconds)

		# this is a virtual device, so it wont really get events... We have some action groups or triggers that call us through executeCommand function
		# we convert those messages to update events and distribute them as if we were indigo, so register for the update events here
		#mmLib_Events.subscribeToEvents('AttributeUpdate', 'Indigo', self.deviceUpdatedEvent, {}, self.deviceName)	# already done by mmMotion

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
				mmLib_Log.logForce(self.deviceName + " Check Load Devices... No Such device " + str(devName) + ".")
				continue

			if timeDelta < theDeltaTime: theDeltaTime = timeDelta

		# mmLib_Log.logForce(self.deviceName + " === Lowest time delta is: " + str(theDeltaTime))

		return(theDeltaTime)



	# Add the motion stop event for the camMotionEvent below.
	def	processMotionEventOn(self, updateOnly):

		if(not updateOnly):
			mmLib_Log.logForce("### Motion Event (ON) for " + self.deviceName + ".")
			# mmLib_Log.logForce("   Camera Info: \n" + str(camDev))
			self.currentOnState = True

			# convert it to an event and distribute it to continue processing with the mmMotion object

			# distribute it on behalf of indigo o it goes to the mmMotion object in the right format
			mmLib_Events.distributeEvents('Indigo', ['AttributeUpdate'], self.deviceName, {'onState':True})

			mmLib_Low.registerDelayedAction(
				{'theFunction': self.camMotionTimeout, 'timeDeltaSeconds': self.minMovementSeconds, 'theDevice': self.deviceName,
				 'timerMessage': "camMotionTimeout", 'offTimerType': "Timeout"})
		else:
			mmLib_Low.delayDelayedAction(self.camMotionTimeout, self.minMovementSeconds)

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
			mmLib_Log.logForce(" +++ Additional Motion Detected. Updating Timeout on " + self.deviceName + ", extending off timer.")
			self.processMotionEventOn(True)
			return('Dque')

		# At night, If the motion is likely a result of a nearby influential light, exit
		if indigo.variables['MMDayTime'].value == 'false':
			deltaTime = self.getInfluentialLoadChangeDelta()

			if( deltaTime < self.influentialTimeout ):	# timeout configurable in the config file
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

		self.processMotionEventOn(False)

		return('Dque')		# we are complete... dequeue the command (if async)


	def camMotionTimeout(self, theParameters):

		mmLib_Log.logForce("### Motion Event (Implied OFF) for " + self.deviceName + ".")
		self.currentOnState = False

		#	publish this event on behalf of indigo so it goes to the mmMotion object in the right format
		mmLib_Events.distributeEvents('Indigo', ['AttributeUpdate'], self.deviceName, {'onState':False})


		return(0)


