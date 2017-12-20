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
import random

kLoadDeviceTimeSeconds = 60

######################################################
#
# mmLoad - Load Device, usually a Dimmer or Switch
#
######################################################
class mmLoad(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):

		super(mmLoad, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.maxNonMotionTime = int(theDeviceParameters["maxNonMotionTime"]) * 60		# its defined in config file in minutes... keep it handy in seconds
			self.maxOnTime = int(theDeviceParameters["maxOnTime"]) * 60
			self.specialFeatures = theDeviceParameters["specialFeatures"].split(';')		# Can be a list, split by semicolons... normalize it into a proper list
			self.daytimeOnLevel = theDeviceParameters["daytimeOnLevel"]
			self.nighttimeOnLevel = theDeviceParameters["nighttimeOnLevel"]
			self.onControllers = filter(None, theDeviceParameters["onControllers"].split(';'))  # Can be a list, split by semicolons... normalize it into a proper list
			self.sustainControllers = filter(None, theDeviceParameters["sustainControllers"].split(';'))
			self.combinedControllers = self.onControllers + self.sustainControllers
			mmLib_Low.subscribeToControllerEvents(self.combinedControllers, ['on'], self.processControllerEvent)
			mmLib_Low.subscribeToControllerEvents(self.combinedControllers, ['off'], self.processControllerEvent)
			self.companions = []
			mmLib_Low.loadDeque.append(self)						# insert into loadDevice deque
			mmLib_Low.statisticsQueue.append(self)					# insert into statistics deque

			random.seed()
			initialStatusRequestTimeDelta = random.randint(60,660)		# somewhere between 1 to 11 minutes from now
			#mmLib_Log.logForce("### TIMER " + self.deviceName + " Will send Status Request in " + str(round(initialStatusRequestTimeDelta/60.0,2)) + " minutes.")

			when = time.mktime(time.localtime()) + initialStatusRequestTimeDelta

			mmLib_Low.registerDelayedAction(self.periodicStatusUpdateRequest, when)		# Send a status request every so often

			self.scheduledOffTimer = 0
			self.scheduledOffTimerType = 'none'
			self.offTimerSubType = self.scheduledOffTimerType
			self.supportsWarning = 0
			if 'flash' in self.specialFeatures:
				self.supportsWarning = 'flash'
			elif 'beep' in self.specialFeatures:
				self.supportsWarning = 'beep'

			# Initialize bedtime mode

			if 'bedtime' in self.specialFeatures:
				self.bedtimeMode = mmLib_Low.BEDTIMEMODE_OFF					# its possibe, but off
			else:
				self.bedtimeMode = mmLib_Low.BEDTIMEMODE_NOT_POSSIBLE

			self.supportedCommandsDict.update({'bedtimeModeOn':self.bedtimeModeOn, 'devStatus':self.devStatus})

			mmLib_Low.mmSubscribeToEvent('isDayTime', self.mmDayNightTransition)
			mmLib_Low.mmSubscribeToEvent('isNightTime', self.mmDayNightTransition)
			mmLib_Low.mmSubscribeToEvent('initComplete', self.completeInit)

	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################

	#
	# deviceUpdated -
	#
	#
	# deviceUpdated - tell the companions what to do
	#
	def deviceUpdated(self, origDev, newDev):

		processCompanions=1
		mmLib_Log.logVerbose(self.deviceName + " update.")

		if self.defeatTimerUpdate:
			mmLib_Log.logVerbose(self.deviceName + " processing " + str(self.defeatTimerUpdate) + " command, not updating timers and resetting flash flag.")
			self.defeatTimerUpdate = 0
			processCompanions=0
		else:
			if origDev.onState != newDev.onState:
				if newDev.onState == True:
					if self.listOnControllers(self.combinedControllers):
						newOffTimerType = 'MaxOccupancy'
					else:
						newOffTimerType = 'NonMotion'
				else:
					newOffTimerType = 'none'

				self.updateOffTimerCallback(newOffTimerType)

			super(mmLoad, self).deviceUpdated(origDev, newDev)  # the base class just keeps track of the time since last change


		# do bedtimeMode reset if needed
		if newDev.onState == True and self.bedtimeMode == mmLib_Low.BEDTIMEMODE_ON and origDev.onState == False:
			self.bedtimeMode = mmLib_Low.BEDTIMEMODE_OFF
			mmLib_Log.logForce("Bedtime Mode OFF for device: " + self.deviceName)
			self.setControllersOnOfflineState('on')


		if processCompanions and self.companions:
			if newDev.__class__ == indigo.DimmerDevice:
				if origDev.brightness == newDev.brightness: processCompanions=0
			elif origDev.onState == newDev.onState: processCompanions=0

			if processCompanions:
				mmLib_Log.logVerbose("Updated loadDevice: " + self.deviceName + ". " + " Value: " + str(self.getBrightness()) + " Send commands to companions: " + str(self.companions))
				initialBrightness = self.getBrightness()
				for theCompanion in self.companions:
					# debounce the command, dont send it if the value is already correct
					if theCompanion.getBrightness() == initialBrightness :
						mmLib_Log.logVerbose("Device: " + theCompanion.deviceName + " already has the appropriate value: " + str(initialBrightness))
						mmLib_CommandQ.flushQ(theCompanion, {'theCommand': 'brighten'}, ["theCommand"])
					else:
						theCompanion.queueCommand({'theCommand':'brighten', 'theDevice':theCompanion.deviceName, 'theValue':initialBrightness, 'retry':2})
		return(0)



	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	def completeCommand(self, theInsteonCommand ):
		super(mmLoad, self).completeCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# receivedCommand - we received a command from our device. The base object will do most of the work... we want to process special commands here, like bedtime mode
	#
	def receivedCommand(self, theInsteonCommand ):

		#
		# do the normal processing
		# ========================
		super(mmLoad, self).receivedCommand(theInsteonCommand)  			# execute Base Class
		mmLib_Log.logVerbose("Check for bedtime mode: " + self.deviceName)

		#
		# do the special processing
		# ========================

		try:
			theCommandByte = theInsteonCommand.cmdBytes[0]
		except:
			theCommandByte = 0

		# if this device handles bedtimemode, process it now

		if self.bedtimeMode > mmLib_Low.BEDTIMEMODE_NOT_POSSIBLE:

			# look for bedtimeMode activation  (double click off)
			# mmLow.kInsteonOffFast = 17
			if theCommandByte == 20 : self.bedtimeModeOn( {'theCommand':'bedtimeModeOn', 'theDevice':self.deviceName} )

		#
		# Load devices also help the motion sensors calculate dead batteries by notifying them when a user is in a room pressing buttons

		if theCommandByte == 17 or theCommandByte == 20:	#kInsteonOn = 17, kInsteonOffFast = 20
			for theControllerName in self.combinedControllers:
				if not theControllerName: break
				theController = mmLib_Low.MotionMapDeviceDict[theControllerName]
				theController.loadDeviceNotificationOfOn()

		return(0)


	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	#def errorCommand(self, theInsteonCommand ):
	#	super(mmHVACCommands, self).errorCommand(theInsteonCommand)	# Nothing special here, forward to the Base class





	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	# bedtimeModeOn - turn bedtime mode on if its Nighttime
	#
	def bedtimeModeOn(self, theCommandParameters ):

		theResult = 0

		if self.bedtimeMode == mmLib_Low.BEDTIMEMODE_OFF and indigo.variables['MMDayTime'].value == 'false':
			mmLib_Log.logForce("Bedtime Mode ON for device: " + self.deviceName)
			self.bedtimeMode = mmLib_Low.BEDTIMEMODE_ON
			self.setControllersOnOfflineState('off')	# its ok that this command isn't queued, it doesnt send a message just updates state in Indigo
			self.queueCommand({'theCommand':'beep', 'theDevice':self.deviceName, 'theValue':0, 'repeat':1, 'retry':2})
			self.queueCommand({'theCommand':'brighten', 'theDevice':self.deviceName, 'theValue':0, 'retry':2})

		return(theResult)


	#
	# 	devStatus - print the status of the device
	#
	def devStatus(self, theCommandParameters):

		self.deviceMotionStatus()


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self):

		mmLib_Log.logVerbose(self.deviceName + " is completing its initialization tasks.")

		if self.theIndigoDevice.onState == True:
			onGroup = self.listOnControllers(self.combinedControllers)
			# should we turn it off?
			if not onGroup:
				self.updateOffTimerCallback('NonMotion')
			else:
				# a motion sensor is on, set up an auto timer to turn it off
				self.updateOffTimerCallback('MaxOccupancy')
		else:
			# should we turn it on?
			onGroup = self.listOnControllers(self.onControllers)
			if onGroup:
				if indigo.variables['MMDayTime'].value == 'true':
					newBrightnessVal = self.daytimeOnLevel
				else:
					newBrightnessVal = self.nighttimeOnLevel
				
				self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': newBrightnessVal,'defeatTimerUpdate': 'initialization', 'retry': 2})
				# we turned the light on, set up an auto timer to turn it off
				self.updateOffTimerCallback('MaxOccupancy')

		return 0

	#
	#	processControllerEvent(theEvent, theControllerDev) - when a controller, (usually a motion sensor) has an event, it sends the event to a loaddevice through this routine
	#
	#	theHandler format must be
	#		theHandler(theEvent, theControllerDev) where:
	#
	#		theEvent is the text representation of a single event type listed above: we handle 'on' here only
	#		theControllerDev is the mmInsteon of the controller that detected the event
	#
	def processControllerEvent(self, theEvent, theControllerDev):

		newOffTimerType = 'none'

		# if we are currently not processing motion events, bail early
		if indigo.variables['MMDefeatMotion'].value == 'true': return(0)

		mmLib_Log.logVerbose(self.deviceName + " is being asked to process \'" + theEvent + "\' event by " + theControllerDev.deviceName)

		if theEvent == 'on':
			# its either an on controller or a sustain controller, either way, we have to reset the timers to Max
			newOffTimerType = 'MaxOccupancy'

			if indigo.variables['MMDayTime'].value == 'true':
				theLevel = self.daytimeOnLevel
			else:
				theLevel = self.nighttimeOnLevel

			if theControllerDev.deviceName in self.onControllers:
				# Process as an 'on' event
				mmLib_Log.logVerbose(self.deviceName + " received an \'on\' event from " + theControllerDev.deviceName + ". Requested Brightness level: " + str(theLevel))
				if int(theLevel) > 0 and self.theIndigoDevice.onState == False:
					self.queueCommand({'theCommand':'brighten', 'theDevice':self.deviceName, 'theValue':theLevel, 'retry':2})

		elif theEvent == 'off':
			# if all the controllerdevices are off, revert to the shorter occupancy timeout
			if self.theIndigoDevice.onState == True and not self.listOnControllers(self.combinedControllers):
				newOffTimerType = 'NonMotion'
		else:
			mmLib_Log.logForce(self.deviceName + "Unsupported Event type " + theEvent)

		if newOffTimerType != 'none': self.updateOffTimerCallback(newOffTimerType)

		return 0


	#
	# 	updateOffTimerCallback - Reset the timers based on load state change
	#
	def updateOffTimerCallback(self, newTimerType):

		if newTimerType == 'MaxOccupancy':
			newOffTimer = time.mktime(time.localtime()) + self.maxOnTime
		elif newTimerType == 'NonMotion':
			newOffTimer = time.mktime(time.localtime()) + self.maxNonMotionTime
		else:
			newOffTimer = 0

		if newOffTimer:
			if self.supportsWarning:
				# Set flash or off timer, depending on special features
				newTimerType = newTimerType + ' 1 Minute Warning'
				newOffTimer = newOffTimer - 60

			# the timer functions only support one item in the queue per device, so you dont have to flush the queue
			self.scheduledOffTimer = mmLib_Low.registerDelayedAction(self.offTimerCallback, newOffTimer)
			mmLib_Log.logVerbose(">>> " + self.deviceName + " requested/result timer: " + str(newOffTimer) + " / " + str(self.scheduledOffTimer))

		else:
			mmLib_Low.cancelDelayedAction(self.offTimerCallback)
			self.scheduledOffTimer = 0

		self.scheduledOffTimerType = newTimerType
		mmLib_Log.logVerbose(self.deviceName + " Timer set to " + newTimerType + " in " + str(mmLib_Low.minutesAndSecondsTillTime(self.scheduledOffTimer)))

		return 0


	#
	# 	offTimerCallback - flash or beep before turning off if necessary
	#
	def offTimerCallback(self):
		mmLib_Log.logForce("\'" + self.deviceName + "\' CallBack type " + self.scheduledOffTimerType)

		if self.scheduledOffTimerType in ['MaxOccupancy','NonMotion','Final Minute']:
			self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': 0, 'retry': 2})
			self.scheduledOffTimer = 0
			self.scheduledOffTimerType = 'none'

		elif 'Warning' in self.scheduledOffTimerType:
			if self.supportsWarning == 'flash':
				self.queueCommand({'theCommand': 'flash', 'theDevice': self.deviceName, 'theValue': 0, 'defeatTimerUpdate': 'flash','retry': 2})
			else:
				self.queueCommand({'theCommand': 'beep', 'theDevice': self.deviceName, 'theValue': 0, 'repeat': 1, 'retry': 2})

			self.scheduledOffTimer = time.mktime(time.localtime()) + 60
			self.scheduledOffTimerType = 'Final Minute'
			self.scheduledOffTimer = mmLib_Low.registerDelayedAction(self.offTimerCallback, self.scheduledOffTimer)
		else:
			mmLib_Log.logForce(self.deviceName + "Unknown callBack type " + self.scheduledOffTimerType)
			self.scheduledOffTimer = 0
			self.scheduledOffTimerType = 'none'

		return 0


	#
	# 	listOnControllers - return a list of controllers that are on
	#
	def listOnControllers(self, checkControllers):
		theList = []

		if checkControllers:

			for devName in checkControllers:
				try:
					theController = mmLib_Low.MotionMapDeviceDict[devName]
				except:
					mmLib_Log.logForce(self.deviceName + "Check Controllers... No Such controller " + str(devName))
					continue

				if theController.theIndigoDevice.onState == True:
					theList.append(theController.deviceName)

		return theList

	#
	# setControllersOnOfflineState - for all of our controllers
	#	We actually put the controller offline because the load device (switch) is the UI for the controller(motion sensor)
	#	its theonly wat to put the motion sensor to sleep for other devices (Water pump and HVAC for example)
	#
	def setControllersOnOfflineState(self,requestedState):

		for otherControllerName in self.combinedControllers:
			if not otherControllerName: break
			theController = mmLib_Low.MotionMapDeviceDict[otherControllerName]
			theController.setOnOffLine(requestedState)
		return(0)


	#
	# getAreaOccupiedState - are any of our controllers currently in an occupied state?
	#
	def getAreaOccupiedState(self, theControllers):

		# If any of our controllers are "Occupied", return True

		#mmLog.logForce( self.deviceName + " is iterating controllers in: " + str(self.combinedControllers))
		for otherControllerName in theControllers:
			if not otherControllerName: break
			theController = mmLib_Low.MotionMapDeviceDict[otherControllerName]
			if theController.onlineState == 'on':	# and theController.occupiedState == True:	# nope, cant turn off yet
				mmLib_Log.logVerbose(otherControllerName + " is is keeping device " + self.deviceName + " on")
				return(True)
		return(False)

	#
	# deviceMotionStatus - display the motion status of a device
	#
	def deviceMotionStatus(self):

		if self.theIndigoDevice.onState == True:

			if self.scheduledOffTimer:
				theTimeString = mmLib_Low.minutesAndSecondsTillTime(self.scheduledOffTimer)
				mmLib_Log.logForce("\'" + self.deviceName + "\'" + " is scheduled to turn off in " + str(theTimeString) + " due to " + self.scheduledOffTimerType + ".")
				onGroup = self.listOnControllers(self.combinedControllers)
				if onGroup: mmLib_Log.logForce("  Related Controllers Reporting ON: " + str(onGroup))
			else:
				mmLib_Log.logForce("WARNING " + "\'" + self.deviceName + "\'" + " is on but not scheduled to turn off." )
		else:

			if self.bedtimeMode == mmLib_Low.BEDTIMEMODE_ON:
				bedtimeMessage = " Bedtime Mode Active."
			else:
				bedtimeMessage = ""

			mmLib_Log.logForce("\'" + self.deviceName + "\'" + " is not on." + bedtimeMessage)
			mmLib_Low.printDelayedAction(self.offTimerCallback)
		return 0

	#
	# 		mmDayNightTransition - process day/night transition
	#
	def mmDayNightTransition(self):

		# do day/night processing

		if indigo.variables['MMDayTime'].value == 'false':
			localDaytime = False
		else:
			localDaytime = True

		if localDaytime == True:
			#
			#  process night to day transition
			newBrightnessVal = self.daytimeOnLevel

			# do bedtimeMode reset if needed
			if self.bedtimeMode == mmLib_Low.BEDTIMEMODE_ON:
				self.bedtimeMode = mmLib_Low.BEDTIMEMODE_OFF
				mmLib_Log.logForce("Bedtime Mode OFF for device: " + self.deviceName)
				self.setControllersOnOfflineState(
					'on')  # we are turning badtime mode off, so start commands from our controllers again
		else:
			#
			#  process day to night transition
			newBrightnessVal = self.nighttimeOnLevel


		# process day/night brightness transitions
		# If the device is on, set its brightness to the appropriate level, but only if there is nobody in the room
		if self.theIndigoDevice.onState == True and self.theIndigoDevice.__class__ == indigo.DimmerDevice and self.getAreaOccupiedState(self.combinedControllers) == False:
			mmLib_Log.logForce("Day/Night transition for device: " + self.deviceName)
			self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': newBrightnessVal,'defeatTimerUpdate': 'dayNightTransition', 'retry': 2})

	#
	# periodicStatusUpdateRequest - status requests every now and then
	#
	def periodicStatusUpdateRequest(self):

		self.queueCommand({'theCommand': 'sendStatusRequest', 'theDevice': self.deviceName, 'theValue': 999, 'retry': 2})

		renewalStatusRequestTimeDelta = random.randint(3600, 3600 * 2)  # then repeat between 1-2 hours
		mmLib_Log.logVerbose("Sent Status Update Request for device: " + self.deviceName + ". Will send another in " + str(round(renewalStatusRequestTimeDelta/60.0, 2)) + " minutes.")
		when = time.mktime(time.localtime()) + renewalStatusRequestTimeDelta
		mmLib_Low.registerDelayedAction(self.periodicStatusUpdateRequest, when)  # renew status request time

		return 0

	#
	# deviceTime - do device housekeeping... this should happen once a minute
	#
	#def deviceTime(self):
	#	return 0

