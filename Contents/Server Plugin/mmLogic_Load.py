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
			self.lastOffCommandTime = 0
			#mmLib_Low.subscribeToControllerEvents(self.combinedControllers, ['on'], self.processControllerEvent, self.deviceName)
			#mmLib_Low.subscribeToControllerEvents(self.combinedControllers, ['off'], self.processControllerEvent, self.deviceName)
			mmLib_Events.subscribeToEvents(['on','off'], self.combinedControllers, self.processControllerEvent, {}, self.deviceName)
			self.companions = []
			mmLib_Low.loadDeque.append(self)						# insert into loadDevice deque
			mmLib_Low.statisticsQueue.append(self)					# insert into statistics deque

			random.seed()
			initialStatusRequestTimeDelta = random.randint(60,660)		# somewhere between 1 to 11 minutes from now
			#mmLib_Log.logForce("### TIMER " + self.deviceName + " Will send Status Request in " + str(round(initialStatusRequestTimeDelta/60.0,2)) + " minutes.")

			mmLib_Low.registerDelayedAction({'theFunction': self.periodicStatusUpdateRequest, 'timeDeltaSeconds': initialStatusRequestTimeDelta, 'theDevice': self.deviceName, 'timerMessage': "periodicStatusUpdateRequest"})
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
			mmLib_Log.logReportLine("Bedtime Mode OFF for device: " + self.deviceName)
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
						mmLib_CommandQ.flushQ(theCompanion, {'theDevice':theCompanion.deviceName,'theCommand': 'brighten'}, ["theCommand"])
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


		# if it was an off or fast off, clear the command queue, no other commands are important that are waiting
		#


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
			# mmComm_Insteon.kInsteonOffFast = 20
			if theCommandByte == mmComm_Insteon.kInsteonOffFast : self.bedtimeModeOn( {'theCommand':'bedtimeModeOn', 'theDevice':self.deviceName} )

		#
		# Load devices also help the motion sensors calculate dead batteries by notifying them when a user is in a room pressing buttons

		if theCommandByte == mmComm_Insteon.kInsteonOn or theCommandByte == mmComm_Insteon.kInsteonOnFast:	#kInsteonOn = 17, kInsteonOnFast = 18
			for theControllerName in self.combinedControllers:
				#if not theControllerName: break
				theController = mmLib_Low.MotionMapDeviceDict[theControllerName]
				theController.loadDeviceNotificationOfOn()
		elif theCommandByte == mmComm_Insteon.kInsteonOff or theCommandByte == mmComm_Insteon.kInsteonOffFast:
			# defeat the motion sensors for a couple seconds to keep the light from coming back on immediately
			self.lastOffCommandTime = int(time.mktime(time.localtime()))


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

		#mmLib_Log.logForce( self.deviceName + " is being called to turn on Bedtime mode. Current Mode is: " + str(self.bedtimeMode))

		if self.bedtimeMode == mmLib_Low.BEDTIMEMODE_OFF and indigo.variables['MMDayTime'].value == 'false':
			mmLib_Log.logReportLine("Bedtime Mode ON for device: " + self.deviceName)
			self.bedtimeMode = mmLib_Low.BEDTIMEMODE_ON
			self.setControllersOnOfflineState('off')	# its ok that this command isn't queued, it doesnt send a message just updates state in Indigo
			self.queueCommand({'theCommand':'beep', 'theDevice':self.deviceName, 'theValue':0, 'repeat':1, 'retry':2})
			self.queueCommand({'theCommand':'brighten', 'theDevice':self.deviceName, 'theValue':0, 'retry':2})

		return(theResult)


	#
	# 	devStatus - print the status of the device
	#
	def devStatus(self, theCommandParameters):

		theResult = self.deviceMotionStatus()
		return(theResult)

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self):

		newCallbackType = 'MaxOccupancy'	#assume Max Occupancy unless proven empty area
		mmLib_Log.logVerbose(self.deviceName + " is completing its initialization tasks.")

		if self.theIndigoDevice.onState == True:
			# The device is on, should we schedule to turn it off based on non occupancy?
			# note that if there are no controllers, controllers cannot influence turning the light off, so it defaults to MaxOccupancy (above)
			if self.combinedControllers and not self.listOnControllers(self.combinedControllers):
				newCallbackType = 'NonMotion'
		else:
			# The device is Off, should we turn it on?
			if self.onControllers and self.listOnControllers(self.onControllers):
				# Yes we have some controllers and they are reporting occupied
				if indigo.variables['MMDayTime'].value == 'true':
					newBrightnessVal = int(self.daytimeOnLevel)
				else:
					newBrightnessVal = int(self.nighttimeOnLevel)

				# if there is a new brightness value (non zero), go ahead and turn the device on
				if newBrightnessVal:
					mmLib_Log.logForce(self.deviceName + " is being turned on because its motionSensor shows occupancy during initialization. Brightness value is " + str(newBrightnessVal))
					self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': newBrightnessVal,'defeatTimerUpdate': 'initialization', 'retry': 2})
					# we turned the light on, set up an auto timer to turn it off
			else:
				# The device is off and nothing is reporting occupied... turn off timers
				newCallbackType = 'none'

		# refresh the timers to whatever we figured out above
		self.updateOffTimerCallback(newCallbackType)

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
	#		theHandler(eventID, eventParameters)
	#
	#	where eventParameters is a dict containing:
	#
	# thePublisher				The name of the Registered publisher (see above) who is sending the event
	# theEvent					The text name of the event to be sent (see subscribeToEvents below)
	# theSubscriber				The Text Name of the Subscriber to receive the event
	# publisherDefinedData		Any data the publisher chooses to include with the event (for example, if it
	# 								is an indigo command event, we might include the whole indigo command record here)
	# timestamp					The time (in seconds) the event is being published/distributed
	def processControllerEvent(self, theEvent, eventParameters):

		newOffTimerType = 'none'
		theControllerDev = mmLib_Low.MotionMapDeviceDict[eventParameters['publisher']]

		# if we are currently not processing motion events, bail early
		if indigo.variables['MMDefeatMotion'].value == 'true': return(0)

		if self.lastOffCommandTime and theEvent == 'on':
			if int(time.mktime(time.localtime())) - self.lastOffCommandTime < 10:
				mmLib_Log.logForce( "=== " + self.deviceName + " is ignoring ON controller event from " + theControllerDev.deviceName + " " + str(int(time.mktime(time.localtime())) - self.lastOffCommandTime) + " seconds after user off command.")
				return(0)

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
				if self.theIndigoDevice.onState == False:
					# the ight is off, should we turn it on?
					if int(theLevel) > 0:
						self.queueCommand({'theCommand':'brighten', 'theDevice':self.deviceName, 'theValue':theLevel, 'retry':2})
					else:
						# the light isnt on and the new level is also off, clear the off timer
						newOffTimerType = 'none'
			else:
				# must be a sustain controller.. if the light is off, clear the timer
				if self.theIndigoDevice.onState == False: newOffTimerType = 'none'

		elif theEvent == 'off':
			# if all the controllerdevices are off, revert to the shorter occupancy timeout
			if self.theIndigoDevice.onState == True and not self.listOnControllers(self.combinedControllers):
				newOffTimerType = 'NonMotion'
		else:
			mmLib_Log.logForce(self.deviceName + "Unsupported Event type " + theEvent)
			return 0

		self.updateOffTimerCallback(newOffTimerType)

		return 0


	#
	# 	updateOffTimerCallback - Reset the timers based on load state change
	#
	def updateOffTimerCallback(self, newTimerType):

		# if we are setting max occupancy and self.maxOnTime is 0, there is no limit... fall through to newOffTimer = 0 and cancel timer
		if newTimerType == 'MaxOccupancy' and self.maxOnTime:
			newOffTimer = self.maxOnTime
		elif newTimerType == 'NonMotion':
			newOffTimer = self.maxNonMotionTime
		elif newTimerType == 'Final Minute':
			newOffTimer = 60
		else:
			newOffTimer = 0

		if newOffTimer:
			if self.supportsWarning and newTimerType != 'Final Minute':
				# Set flash or off timer, depending on special features
				newTimerType = newTimerType + ' 1 Minute Warning'
				newOffTimer = newOffTimer - 60

			# the timer functions only support one item in the queue per device, so you dont have to flush the queue
			scheduledOffTime = mmLib_Low.registerDelayedAction({'theFunction': self.offTimerCallback, 'timeDeltaSeconds': newOffTimer, 'theDevice': self.deviceName, 'timerMessage': "offTimerCallback:" + newTimerType, 'offTimerType': newTimerType})
			mmLib_Log.logVerbose(">>> " + self.deviceName + " requested/result timer: " + str(newOffTimer) + " / " + str(scheduledOffTime))

		else:
			mmLib_Low.cancelDelayedAction(self.offTimerCallback)
			scheduledOffTime = 0

		mmLib_Log.logVerbose(self.deviceName + " Timer set to " + newTimerType + " at " + str(mmLib_Low.minutesAndSecondsTillTime(scheduledOffTime)))

		return 0


	#
	# 	offTimerCallback - flash or beep before turning off if necessary
	#
	def offTimerCallback(self, parameters):
		theTimerType = parameters["offTimerType"]
		mmLib_Log.logReportLine("\'" + self.deviceName + "\' CallBack type " + theTimerType)

		if theTimerType in ['MaxOccupancy','NonMotion','Final Minute']:
			self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': 0, 'retry': 2})
			theTimerType = 'none'

		elif 'Warning' in theTimerType:
			if self.supportsWarning == 'flash':
				self.queueCommand({'theCommand': 'flash', 'theDevice': self.deviceName, 'theValue': 0, 'defeatTimerUpdate': 'flash','retry': 2})
			else:
				self.queueCommand({'theCommand': 'beep', 'theDevice': self.deviceName, 'theValue': 0, 'repeat': 1, 'retry': 2})

			theTimerType = 'Final Minute'

			# We normally would return the update timer value and automatically restart the timer, but we want to change the timer note, so we call update
			# return 60	#reschedule timer

			self.updateOffTimerCallback(theTimerType)
			return 0	# dont requeue (its handled above)

		else:
			mmLib_Log.logForce(self.deviceName + "Unknown callBack type " + theTimerType)
			theTimerType = 'none'

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
					mmLib_Log.logForce(" ### For Device " + self.deviceName + ", Check Controllers in csv file... No Such controller " + str(devName))
					continue

				if theController.getOnState() == True:
					theList.append(theController.deviceName)

		return theList

	#
	# setControllersOnOfflineState - for all of our controllers
	#	We actually put the controller offline because the load device (switch) is the UI for the controller(motion sensor)
	#	its the only wat to put the motion sensor to sleep for other devices (Water pump and HVAC for example)
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

		theMessage = '\n\n==== DeviceStatus for ' + self.deviceName + '====\n'

		if self.theIndigoDevice.onState == True:
			scheduledOffTime = mmLib_Low.delayedFunctionKeys[self.offTimerCallback]
			if scheduledOffTime:
				theTimeString = mmLib_Low.minutesAndSecondsTillTime(scheduledOffTime)
				theMessage = theMessage + str("\'" + self.deviceName + "\'" + " is scheduled to turn off in " + str(theTimeString) + ".\n")
				onGroup = self.listOnControllers(self.combinedControllers)
				if onGroup: theMessage = theMessage + str("  Related Controllers Reporting ON: " + str(onGroup) + "\n")
			else:
				theMessage = theMessage + str("WARNING " + "\'" + self.deviceName + "\'" + " is on but not scheduled to turn off.\n" )
		else:

			if self.bedtimeMode == mmLib_Low.BEDTIMEMODE_ON:
				bedtimeMessage = " Bedtime Mode Active."
			else:
				bedtimeMessage = ""

			theMessage = theMessage + str("\'" + self.deviceName + "\'" + " is not on." + bedtimeMessage + "\n")

		theMessage = theMessage + mmLib_Low.mmGetDelayedProcsList({'theDevice':self.deviceName})
		theMessage = theMessage + "\n==== DeviceStatus End ====\n"

		mmLib_Log.logReportLine(theMessage)

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
				mmLib_Log.logReportLine("Bedtime Mode OFF for device: " + self.deviceName)
				self.setControllersOnOfflineState('on')  # we are turning badtime mode off, so start commands from our controllers again
		else:
			#
			#  process day to night transition
			newBrightnessVal = self.nighttimeOnLevel


		# process day/night brightness transitions
		# If the device is on, set its brightness to the appropriate level, but only if there is nobody in the room
		if self.theIndigoDevice.onState == True and self.theIndigoDevice.__class__ == indigo.DimmerDevice and self.getAreaOccupiedState(self.combinedControllers) == False:
			mmLib_Log.logReportLine("Day/Night transition for device: " + self.deviceName)
			self.queueCommand({'theCommand': 'brighten', 'theDevice': self.deviceName, 'theValue': newBrightnessVal,'defeatTimerUpdate': 'dayNightTransition', 'retry': 2})

	#
	# periodicStatusUpdateRequest - status requests every now and then
	#
	def periodicStatusUpdateRequest(self, parameters):

		self.queueCommand({'theCommand': 'sendStatusRequest', 'theDevice': self.deviceName, 'theValue': 999, 'retry': 2})

		renewalStatusRequestTimeDelta = random.randint(3600, 3600 * 2)	# return timer reset value in seconds (between 1 and 2 hours)

		mmLib_Log.logVerbose("Sent Status Update Request for device: " + self.deviceName + ". Will send another in " + str(round(renewalStatusRequestTimeDelta/60.0, 2)) + " minutes.")

		return renewalStatusRequestTimeDelta

	#
	# deviceTime - do device housekeeping... this should happen once a minute
	#
	#def deviceTime(self):
	#	return 0

