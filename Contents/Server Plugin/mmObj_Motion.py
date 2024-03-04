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

kMotionDevTolerableMotionBounceTime = 2	#if off/on transition time is > 2 seconds, the device is not bouncing
kMotionDevMaxSequentialBounces = 50	# if there are more than 50 bounces in a row, there may be a problem (usually requires a battery replacement or reset of parameters)
OccupiedStateList = ['UnoccupiedAll', 'OccupiedAll', 'Unknown']

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
from datetime import datetime, timedelta

# How many ON transitions will resuklt in a bettery level test
BAT_LEVEL_ON_FACTOR = 100
BAT_LEVEL_CHECK_INTERVAL_SECONDS = 24*3600		# 1 Day

######################################################
#
# mmMotion - Motion Sensor Device
#
######################################################
class mmMotion(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):

		# We added initLow so it can get called from child classes thereby overriding subscribeToEvents (iOLink device specifically)

		self.initLow(theDeviceParameters)

		mmLib_Events.subscribeToEvents(['AttributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes': {'onState': 0}}, self.deviceName)


	def initLow(self, theDeviceParameters):

		random.seed()

		# set things that must be setup before Base Class
		self.lastOnTimeSeconds = 0
		self.lastOffTimeSeconds = 0
		self.blackOutTill = 0
		self.onlineState = mmLib_Low.AUTOMATIC_MODE_ACTIVE

		super(mmMotion, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.maxMovement = theDeviceParameters["maxMovement"]	# the amount of time (in minutes) that the motion sense can stay "ON" for sustained occupancy
			self.minMovement = theDeviceParameters["minMovement"]	# the amount of time (in minutes) that motion sense is "OFF" that constitutes no occupancy
			mmLib_Low.controllerDeque.append(self)		# insert into device-time deque

			self.occupiedState = 2
			self.supportedCommandsDict = {}
			self.controllerMissedCommandCount = 0
			self.previousMotionOff = 0

			mmLib_Events.registerPublisher(['on', 'off', 'OccupiedAll', 'UnoccupiedAll'], self.deviceName)

			self.supportedCommandsDict.update({})

			self.ourNonvolatileData = mmLib_Low.initializeNVDict(self.deviceName)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "rapidTransitionTimeList", [])
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "problemReportTime", 0)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "batteryQueryTimeSeconds", 0)
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "batteryQueryTimeSecondsStr", " Unknown ")
			mmLib_Low.initializeNVElement(self.ourNonvolatileData, "batteryLevel", 0)

			if self.debugDevice:
				mmLib_Log.logForce("###DEBUG:Forcing batteryQueryTimeSeconds to 0")
				self.ourNonvolatileData["batteryQueryTimeSeconds"] = 0

			s = str(self.deviceName + ".Occupation")
			self.occupationIndigoVar = s.replace(' ', '.')
			if self.debugDevice: mmLib_Log.logForce("Initializing " + str(self.occupationIndigoVar) + " for " + self.deviceName + " to occupiedState " + str(self.occupiedState) + ". (" + str(OccupiedStateList[self.occupiedState]) + ")")
			mmLib_Low.getIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState])

			self.supportedCommandsDict.update({'devStatus': self.devStatus})

			self.supportedCommandsDict.update({'sendRawInsteonCommand': self.sendRawInsteonCommand })

			# register for the indigo events we want

			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.initializationComplete, {}, self.deviceName)

			# The two procedures below are for Battery level process ing for Indigo Motion Sensors only
			self.isInsteonMotionDevice = False
			try:
				prot = self.theIndigoDevice.protocol
				image = self.theIndigoDevice.displayStateImageSel
				s1 = "Insteon MotionSensor"
				s2 = str(prot) + " " + str(image)
				if not s2.find(s1):
					self.isInsteonMotionDevice = True
					# the following is only valid for insteon motions
					if theDeviceParameters["autoEnableActivityLight"] == "true":
						self.autoEnableActivityLight = True
						mmLib_Log.logForce("###DEBUG:Forcing LEDDaytimeMode to Unknown")
						self.LEDDaytimeMode = "Unknown"		#GB FIX ME.. Make this a nonvolitile
					else:
						self.autoEnableActivityLight = False
				else:
					mmLib_Log.logForce("###DEBUG:Not insteon Motion Sensor type for " + self.deviceName + ". Found: " + str(prot) + " " + str(image))

			except:
				mmLib_Log.logForce("###DEBUG:Failed to get device type for " + self.deviceName)
				pass

			if self.debugDevice:mmLib_Log.logForce(" ### " + self.deviceName + ".isInsteonMotionDevice: " + str(self.isInsteonMotionDevice))

			if self.isInsteonMotionDevice:
				mmLib_Events.subscribeToEvents(['DevCmdComplete'], ['Indigo'], self.completeCommandEvent, {}, self.deviceName)
				mmLib_Events.subscribeToEvents(['DevCmdErr'], ['Indigo'], self.errorCommandEvent, {}, self.deviceName)

			# The following is now handled at init above so it can get overridden by child classas
			# 	mmLib_Events.subscribeToEvents(['AttributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes':{'onState':0}}, self.deviceName)

	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	def completeCommandEvent(self, eventID, eventParameters ):
		theCommandByte = 0
		if self.debugDevice: mmLib_Log.logForce( "completeCommandEvent. Success for " + self.deviceName + " during command completion. Completion Event Parameters: " + str(eventParameters))
		commandParameters = eventParameters['cmd']
		#if self.debugDevice: mmLib_Log.logForce("completeCommandEvent, Command Parameters: " + str(commandParameters))
		theCommandByte = commandParameters.cmdBytes[0]

		super(mmMotion, self).completeCommandEvent(eventID, eventParameters)	# Nothing special here, forward to the Base class

		if theCommandByte == mmComm_Insteon.kInsteonRequestBattLevel:
			#if self.debugDevice: mmLib_Log.logForce("completeCommandEvent. BatteryLevel completeCommandEvent for " + self.deviceName)
			self.ourNonvolatileData["batteryLevel"] = str(float(commandParameters.replyBytes[13] / 100.0))
			mmLib_Log.logForce( "Battery Level for " + self.deviceName + " is " + self.ourNonvolatileData["batteryLevel"])
			self.ourNonvolatileData["batteryQueryTimeSeconds"] = int(time.mktime(time.localtime()))
			self.ourNonvolatileData["batteryQueryTimeSecondsStr"] = str(datetime.now().strftime("%m/%d/%Y"))

			mmLib_Low.setIndigoVariable("MotionBatteryLevel_" + self.deviceName, self.ourNonvolatileData["batteryLevel"] + " (as of " + str(datetime.now().strftime("%m/%d/%Y")) + ")")

		elif theCommandByte == mmComm_Insteon.kInsteonEnableDisableMotionLED:
			#if self.debugDevice: mmLib_Log.logForce("EnableDisableMotionLED_" + self.deviceName + "ReplyBytes:" + str(commandParameters.replyBytes))
			if commandParameters.cmdSuccess == True:
				self.LEDDaytimeMode = indigo.variables['isDaylight'].value  # str("true") means enable LED, str("false") means disable
				if self.debugDevice: mmLib_Log.logForce("LEDDaytimeMode for " + self.deviceName + " Successfully set to:" + str(self.LEDDaytimeMode))
		else:
			mmLib_Log.logForce( "###Unknown complete event type " + str(theCommandByte) + " for " + self.deviceName + " during command completion.")

		#if self.debugDevice: mmLib_Log.logForce("CompleteCommandEvent for " + self.deviceName + " Finished.")

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	def errorCommandEvent(self, eventID, eventParameters  ):
		mmLib_Log.logForce( "### Error completing command to " + self.deviceName + ". We are dequeing the command from the commandqueue. Completion Event Parameters: " + str(eventParameters))
		# We dont do retries in motion sensors so just dequeue command
		mmLib_CommandQ.dequeQ(1)  # the 1 implies dequeue (us from top) and restart the queue (no retries on motion sensors - they will be asleep by the time a retry happens)

		return(0)

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
	# deviceMotionStatus - check the motion status of a device
	#
	def deviceMotionStatus(self):

		self.devStatus({})
		return(0)

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
	#	'ON'			The motion sensor is to be put online and activated (mmLib_Low.AUTOMATIC_MODE_ACTIVE)
	#	'SLEEP'			The motion sensor is sleeping till morning (mmLib_Low.AUTOMATIC_MODE_SLEEP)
	#	'OFF'			The motion sensor to be put offline (mmLib_Low.AUTOMATIC_MODE_OFFLINE)
	def setOnOffLine(self, requestedState):
		if self.debugDevice: mmLib_Log.logForce("Setting " + self.deviceName + "'s onOfflineState to \'" + requestedState + "\'. Current State is: " + self.onlineState)

		if self.onlineState != requestedState:
			if self.debugDevice: mmLib_Log.logForce("Setting " + self.deviceName + " onOfflineState to \'" + requestedState + "\'.")

			self.onlineState = requestedState

			if self.onlineState != mmLib_Low.AUTOMATIC_MODE_ACTIVE:
				self.occupiedState = False	# if the device is offline (or bedtime mode), assume it is also unoccupied.
				# if there are any delay procs, delete them, they are not valid anymore
				mmLib_Low.cancelDelayedAction(self.delayProcForNonOccupancy)
				mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)
				mmLib_Log.logForce( "Motion sensor " + self.deviceName + " is going offline because it\'s \'onlineState\' is " + str(self.onlineState))
				if self.onlineState == mmLib_Low.AUTOMATIC_MODE_SLEEP:
					mmLib_Low.setIndigoVariable(self.occupationIndigoVar, "# Sleeping #")
				else:
					# the only other option is offline
					mmLib_Low.setIndigoVariable(self.occupationIndigoVar, "# Offline #")
				mmLib_Events.distributeEvents(self.deviceName, ['UnoccupiedAll'], 0, {})  # dispatch to everyone who cares
			else:
				# going active
				mmLib_Low.setIndigoVariable(self.occupationIndigoVar, "# Awake, no motion yet. #")

		return(0)


	#
	# getSecondsSinceState - how many seconds since the device was in the given on/off state
	#
	def getSecondsSinceState(self, theState):
		if self.onlineState in [mmLib_Low.AUTOMATIC_MODE_ACTIVE, mmLib_Low.AUTOMATIC_MODE_SLEEP]: return(int(60*60*24))	# default to a high number if the device is offline

		if theState == 'on':
			theStateTime = self.lastOnTimeSeconds
		else:
			theStateTime = self.lastOffTimeSeconds

		return(int(time.mktime(time.localtime()) - theStateTime))


	def getOnState(self):

		if self.onlineState != mmLib_Low.AUTOMATIC_MODE_ACTIVE: return(False)
		return(self.theIndigoDevice.onState)


	def getOccupiedState(self):

		return(OccupiedStateList[self.occupiedState])

	#
	# setLastUpdateTimeSeconds - note the time when the device changed state. This is called by base class.
	#

	def setLastUpdateTimeSeconds(self):

		super(mmMotion, self).setLastUpdateTimeSeconds()  # Call Base Class

		if self.getOnState() == True:
			self.lastOnTimeSeconds = self.lastUpdateTimeSeconds
		else:
			self.lastOffTimeSeconds = self.lastUpdateTimeSeconds
		return()

	#
	# delayProcForOnStateTimeout - if the device went ON 24 hours ago and never went off... it must be offline
	#
	def delayProcForOnStateTimeout(self, theParameters):
		mmLib_Log.logWarning(self.deviceName + " received \'on\' command 24 hours ago and never received off... changing onOffline state to \'off\'.")
		self.setOnOffLine('off')
		return 0


	# delayProcForMaxOccupancy - the device has been marked as occupied for the max amount of time
	#
	def	delayProcForMaxOccupancy(self, theParameters):

		if self.debugDevice: mmLib_Log.logForce("Motion sensor " + self.deviceName + " has been occupied for the maximum amount of time.")
		mmLib_Low.cancelDelayedAction(self.delayProcForNonOccupancy)  # Its unoccupied, clear non occupied timer too
		self.occupiedState = False
		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState])
		skipDistribute = theParameters.get('defeatDistribution', 0)
		if not skipDistribute: mmLib_Events.distributeEvents(self.deviceName, ['UnoccupiedAll'], 0, {})  # dispatch to everyone who cares

		return 0		# Cancel timer



	# delayProcForNonOccupancy - the device seems to indicate area vacant
	#
	def delayProcForNonOccupancy(self, theParameters):

		if self.debugDevice: mmLib_Log.logForce("Motion sensor " + self.deviceName + " is indicating non-occupied.")
		mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)  # Its unoccupied, clear max occupation timer too
		self.occupiedState = False
		mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState])
		skipDistribute = theParameters.get('defeatDistribution', 0)
		if not skipDistribute: mmLib_Events.distributeEvents(self.deviceName, ['UnoccupiedAll'], 0, {})  # dispatch to everyone who cares

		return 0		# Cancel timer



	#
	# deviceTime - check to see if the area is occupied or not, dispatch events accordingly
	#
	def deviceTime(self):
		return(0)



	#
	# initializationComplete - Finalize initialization and start running
	#
	def initializationComplete(self,eventID, eventParameters):

		# lest start with a clean slate

		mmLib_Low.cancelDelayedAction(self.delayProcForNonOccupancy)
		mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)
		self.processOccupation(1)

		return(0)


	#
	# processOccupation		We are normally running and got an update event from the motion sensor,
	#						lets send or schedule the appropriate update
	#
	def processOccupation(self, startup):

		if self.debugDevice: mmLib_Log.logForce("ProcessOccuption for " + self.deviceName + ". onLineState = " + str(self.onlineState) + ". onState = " + str(self.getOnState()))

		currentOnState = self.getOnState()

		# Its possible, especially during startup, the time the motion sensor made its last change was some amount of timeback. We account for that
		# by correcting min and max timeouts by lastUpdateTimeSeconds below

		lastUpdateDeltaSeconds = time.mktime( time.localtime()) - self.lastUpdateTimeSeconds  # lastUpdateTimeSeconds should always be accurate


		if currentOnState == True:

			# device is indicating motion, so set the timeout to the Maximum

			timeDeltaSeconds = int(self.maxMovement) * 60	# do delayProcForMaxOccupancy later

			if self.occupiedState == 2:  # startup time?
				if lastUpdateDeltaSeconds < timeDeltaSeconds:
					timeDeltaSeconds = timeDeltaSeconds - lastUpdateDeltaSeconds
				else:
					if int(self.minMovement) == 0:
						timeDeltaSeconds = 0		# the minimum is irrelevalent if the motion sensor is really a contact switch (indicated by minmovement of 0
					else:
						timeDeltaSeconds = 30		# the minimum... timeout in 30 seconds. Chances are, the motion sensor will timeout before this and we will get to the code below anyway

			stringExtension = "Motion Limit at"

			mmLib_Low.cancelDelayedAction(self.delayProcForNonOccupancy)
			mmLib_Low.registerDelayedAction( {	'theFunction': self.delayProcForMaxOccupancy,
												'timeDeltaSeconds': timeDeltaSeconds,
												'theDevice': self.deviceName,
												'timerMessage': "Motion Sensor MaxOccupancy Timer"})
			self.distributeOccupation(True,timeDeltaSeconds,stringExtension)	# whenever we go into occupied mode, we dont need a timer to distribute

		else:

			# device is NOT indicating motion, so set timeout to the minimum. We will still claim occupied until the timer expires

			timeDeltaSeconds = int(self.minMovement) * 60	# do delayProcForNonOccupancy later
			if self.debugDevice: mmLib_Log.logForce( "Processing OnState False for " + self.deviceName + " with timeDeltaSeconds of " + str(timeDeltaSeconds))

			if self.occupiedState == 2:  # startup time?
				# since we are not calling distributeOccupation, we have to set occupiedState

				if lastUpdateDeltaSeconds < timeDeltaSeconds:
					timeDeltaSeconds = timeDeltaSeconds - lastUpdateDeltaSeconds
					self.occupiedState = True		# Technically Occupied (will set timer)
				else:
					self.occupiedState = False		# it would have already timed out... mark as unoccupied, no timer
					timeDeltaSeconds = 0  # no need to process further

			stringExtension = "Non-Motion Timeout at"

			if timeDeltaSeconds:
				mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)
				mmLib_Low.registerDelayedAction({'theFunction': self.delayProcForNonOccupancy,
												 'timeDeltaSeconds': timeDeltaSeconds,
												 'theDevice': self.deviceName,
												 'timerMessage': "Motion Sensor NonOccupancy Timer"})
			else:
				mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)
				if self.debugDevice: mmLib_Log.logForce( "Distribute nonOccupancy events for " + self.deviceName + ". Skipping timer because minMovement is 0")
				self.delayProcForNonOccupancy({})  # dispatch to everyone who cares

			# We dont distribute unoccupied events here, but we want to update the indigo variable in all cases
			self.resetIndigoOccupationVariable(timeDeltaSeconds, stringExtension)


		return 0

	#
	# insteonMotionPeriodicTasks - Occasionally check the battery level, every BAT_LEVEL_ON_FACTOR number of ON transitions
	#
	def insteonMotionPeriodicTasks(self):

		# Occasionally check the battery level, every BAT_LEVEL_ON_FACTOR number of ON transitions

		if self.ourNonvolatileData["batteryQueryTimeSeconds"] == 0:		# this will be filled in the first time a motion event has been received (for Insteon Motion devices only)
			secondsSinceBatteryStatusCheck = int(BAT_LEVEL_CHECK_INTERVAL_SECONDS) # force battery check (its never been done before
		else:
			secondsSinceBatteryStatusCheck = int(time.mktime(time.localtime())) - int(self.ourNonvolatileData["batteryQueryTimeSeconds"] )

		if secondsSinceBatteryStatusCheck >= BAT_LEVEL_CHECK_INTERVAL_SECONDS:

			mmLib_Log.logForce( "insteonMotionPeriodicTasks. Checking Battery Level for " + self.deviceName + " in 2 seconds.")

			mmLib_Low.registerDelayedAction({'theFunction': self.dispatchBatteryStatusCommand,
											 'timeDeltaSeconds': int(2),
											 'theDevice': self.deviceName,
											 'timerMessage': "Motion Sensor battery status request Timer"})
		else:
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + ": checking autoEnableActivityLight")
			# only check for LED enable/disable when not checking battery
			# and only if the config file says to manage LED activity
			if self.autoEnableActivityLight:
				newEnabledState = indigo.variables['isDaylight'].value	# str("true") means enable LED, str("false") means disable
				if self.LEDDaytimeMode != newEnabledState:
					mmLib_Low.registerDelayedAction({'theFunction': self.dispatchMotionSensorDisableEnableCommand,
													 'timeDeltaSeconds': int(2),
													 'theDevice': self.deviceName,
													 'timerMessage': "Motion Sensor enable Disable activity LED",
													 'newState': newEnabledState})

		return 0


	#
	# dispatchBatteryStatusCommand - happens approximately 2 seconds after receiving an on command
	#
	def dispatchBatteryStatusCommand(self, theParameters):

		if self.debugDevice: mmLib_Log.logForce("### Motion sensor " + self.deviceName + " is Queing BatteryStatus Command.")
		# Do it as a queued command so we can get the result without waiting. the result will
		# come in as DevCmdComplete (success) or DevCmdErr (error) events
		# waitForExtendedReply must be set to true or we wont get a result in the completion proc

		# OLD self.queueCommand({'theCommand': 'sendRawInsteonCommand', 'theDevice': self.deviceName, 'extended':True, 'ackWait': 0, 'cmd1': 0x2E, 'cmd2': 0x00, 'cmd3': 0x00, 'cmd4': 0x00, 'cmd5': 0x00, 'waitForExtendedReply':True, 'retry': 0})
		self.queueCommand({'theCommand': 'sendRawInsteonCommand', 'theDevice': self.deviceName, 'ackWait': 0, 'cmd': [0x2E, 0x00, 0x00, 0x00, 0x00], 'waitForExtendedReply':True, 'retry': 0})
		#self.queueCommand({'theCommand': 'sendRawInsteonCommand', 'theDevice': self.deviceName, 'ackWait': 1, 'cmd': [0x2E, 0x00, 0x00, 0x00, 0x00], 'waitForExtendedReply':True, 'retry': 0})

		return 0  # Cancel timer

	#
	# dispatchMotionSensorDisableEnableCommand - happens approximately 2 seconds after receiving an on command
	#
	def dispatchMotionSensorDisableEnableCommand(self, theParameters):

		# Do it as a queued command so we can get the result without waiting. the result will
		# come in as DevCmdComplete (success) or DevCmdErr (error) events
		# waitForExtendedReply must be set to true or we wont get a result in the completion proc

		# newState will be "true" to enable, "false" to disable

		itsDaytime = theParameters.get('newState', 0)
		if self.debugDevice: mmLib_Log.logForce("### Motion sensor " + self.deviceName + " is sending LED Enable/Disable command of " + str(itsDaytime) + ".")

		if itsDaytime == "true":
			# its daytime, Enable LED cmd2 = 0x03 and data14 0xDD
			self.queueCommand({'theCommand': 'sendRawInsteonCommand', 'theDevice': self.deviceName, 'ackWait': 0, 'cmd': [mmComm_Insteon.kInsteonEnableDisableMotionLED, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xDD], 'waitForExtendedReply':False, 'retry': 0})
		else:
			# its nighttime,disable LED cmd2 = 0x02 and data14 0xDE
			self.queueCommand({'theCommand': 'sendRawInsteonCommand', 'theDevice': self.deviceName, 'ackWait': 0, 'cmd': [mmComm_Insteon.kInsteonEnableDisableMotionLED, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xDE], 'waitForExtendedReply':False, 'retry': 0})

		# either way, assume success
		self.LEDDaytimeMode = itsDaytime

		return 0  # Cancel timer

	#
	# resetIndigoOccupationVariable - Distribute Occupation Events and set the indigo occupation variable.
	#
	def resetIndigoOccupationVariable(self, timeDeltaSeconds, stringExtension):

		if timeDeltaSeconds:
			ft = datetime.now() + timedelta(seconds=timeDeltaSeconds)
			varString = " ( " + stringExtension + " " + '{:%-I:%M %p}'.format(ft) + " )"
			mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState] + varString)
		else:
			mmLib_Low.setIndigoVariable(self.occupationIndigoVar, OccupiedStateList[self.occupiedState])

		return 0

	#
	# processSwitchOff - A switch was turned off in this domain. Treat it like an immediate unoccupation
	#
	def processSwitchOff(self):
		if self.debugDevice: mmLib_Log.logForce("### Motion sensor " + self.deviceName + " received an OFF event from a subscriber switch." )
		'UnoccupiedAll', 'OccupiedAll'
		return 0

	#
	# distributeOccupation - Distribute Occupation Events and set the indigo occupation variable.
	#
	def distributeOccupation(self,newOccupiedState,timeDeltaSeconds,stringExtension):

		# update self.occupiedState accordingly and distribute the event if occupiedState changed

		# GB Fix me 2/17/24
		#
		# All of this in invalid... processing works as-is. I'm leaving the comments in case I run accross the symptoms again and feel the urge to fix it again.
		# This is already covered by the fact that the load devices call forceTimeout() in this object.I beleive the fire drill of fixing this problem was caused
		# by a low battery in the motion sensor. I cannot reproduce the problem. The symptom is that in some cases we get the message below that states
		# "NOT DISTRIBUTED. Motion Sensor already in " + str(newOccupiedState) + " state."... So how can that happen?
		#
		# Either 	A) the forceTimeout event never got delivered, or
		#			B) there is a very specific timing overlap where forceTimeout did get called, but was immediately superceeded by a new motion event during blackout time that isn't peocessed.
		#				in this case, the light may no longer respond to motion at least until the Motion handler (this object) circulates through its internal timeout...
		#				In any case, sometimes it appears that the event processing gets disabled (or delayed) and the most reasonable reason is that because it receives an ON or Off event while
		#				already, or still, in the proper requested on/off state somehow causing a full timeout sequence to be necessary before the light will automatically go off again. I have not taken the time
		#				to investigate further and will refrain until the problem becomes more easily reproducible. Once I have a reproducible case, I will just TURN ON DEBUGGHING for this motion
		#				sensor and watch the log for sequencing information.
		#
		# Obsoleted diagnostic below for future diagnostic and informational purposes only...
		#
		# Eliminated the IF statement below. Occupancy events are now already delivered even if they are unnecessary.
		#
		# The problem this solves is when the user turnes off a light (typically when leaving a room) in which case, MM doesnt know the user's intent, so the light doesn't
		# go on again with motion events until the full occupation timeout occurred (which finally resets the occupancyState).
		#
		# Here is repair plan in process:
		# When the Load device is sent the occupation event will now receive a proc pointer ('NoticeOfUserTurningLoadDeviceOff':self.processSwitchOff) in "publisherDeficedData".
		# The Load device will note this proc and if it detects a user turning the load switch off (not a state change, literally turning the switch OFF), the new proc
		# pointer will be called which will record an occupiedState of 'UnoccupiedAll' (which will cause the if statement below to work properly).
		#
		# NOTE: GB Fix Me: TBD: The proc pointer described above may need to propagate through occupantionGroups. This is a much thornier problem because when someone turns off a switch
		# does that automatically mean the whole occupation group is unoccupied? Do ALL the lights controlled by the group need to go off now? I will think about and test this (I'm
		# not sure if there is even an occupationgroup scenario defined that has this issue currently)... and if so, have we realy ever seen this as a weakness in occupationgroups in the last decade?
		#
		# So then the next issue...
		# if the user turns off the light but stays in the room... eventually the light will turn on again (possibly an unwanted behavior).
		# The solution is adding a process for the user to choose to disable local motion detection. This will only be done if testing determines it's a necessary feature (face it,
		# the user will never know about this feature so wil likely enable it by accident then wonder why motion detection doesn't work.- MotionMap has been running without this feature for
		# a decade without this feature (and adding the feature will uncover new problems).
		# If we choose to do this feature... The plan for this is to enable a new command.. Double tap off to disable motion detection until morning. We would need to do the analogous feature of double-tap-on
		# re-enables motion sensing.

		# Obsoleted code here:
		#	if self.debugDevice: mmLib_Log.logForce("Occupied State for " + self.deviceName + " has changed to " + str(OccupiedStateList[newOccupiedState]))
		#	mmLib_Events.distributeEvents(self.deviceName, [OccupiedStateList[newOccupiedState]], 0,{})  # dispatch to everyone who cares
		#	self.occupiedState = newOccupiedState

		# Original (and reactivated) code here:

		if self.occupiedState != newOccupiedState:
			if self.debugDevice: mmLib_Log.logForce( "Occupied State for " + self.deviceName + " has changed to " + str(OccupiedStateList[newOccupiedState]))
			# If this is some kind of occupation event (partial or full), put a notification proc pointer into PublisherDefinedData, just in case someone turns
			# off a switch (implying unoccupation event). In that case the proc pointer will be called which will reset the occupationState to reflect current new state.
			mmLib_Events.distributeEvents(self.deviceName, [OccupiedStateList[newOccupiedState]], 0,{'NoticeOfUserTurningLoadDeviceOff': self.processSwitchOff})  # dispatch to everyone who cares
			self.occupiedState = newOccupiedState
		else:
			if self.debugDevice: mmLib_Log.logForce("Occupation state change for " + self.deviceName + " NOT DISTRIBUTED. Motion Sensor already in " + str(newOccupiedState) + " state.")

		self.resetIndigoOccupationVariable(timeDeltaSeconds, stringExtension)

		return 0

	#
	# dispatchOnOffEvents - we received a command from our motion Sensor, process it
	#
	def dispatchOnOffEvents(self, theCommandByte ):

		# process Motion here
		self.deviceTime()		# this will process occupancy events
		if theCommandByte == mmComm_Insteon.kInsteonOn:	#kInsteonOn = 17
			mmLib_Events.distributeEvents(self.deviceName, ['on'], 0, {})  # dispatch to everyone who cares
			#self.dispatchEventToDeque(self.onDeque, 'on')							# process on
		elif theCommandByte == mmComm_Insteon.kInsteonOff:		#kInsteonOff = 19
			mmLib_Events.distributeEvents(self.deviceName, ['off'], 0, {})  # dispatch to everyone who cares
			#self.dispatchEventToDeque(self.offDeque, 'off')							# process off
		else:
			mmLib_Log.logVerbose("Invalid insteon event received for " + self.deviceName + " of " + str(theCommandByte))

		return(0)


	#
	# countBounce
	#	Check to see if the device is rapidly cycling between on and off
	#
	def countBounce(self):

		deltaSeconds = self.getSecondsSinceState('off')
		if deltaSeconds > kMotionDevTolerableMotionBounceTime:
			# the multisensor isnt looping, reset counter and list.
			self.ourNonvolatileData["rapidTransitionTimeList"] = []
			self.ourNonvolatileData["problemReportTime"] = 0
		else:
			# count the sequential transaction
			self.ourNonvolatileData["rapidTransitionTimeList"].append(str(time.ctime(time.mktime(time.localtime()))) + " Reporting only " + str(deltaSeconds) + " seconds of off time.")
			if len(self.ourNonvolatileData["rapidTransitionTimeList"]) == kMotionDevMaxSequentialBounces:
				self.reportFullStatus(1)		# report the problem
				# we reported the problem, now reset
				self.ourNonvolatileData["rapidTransitionTimeList"] = []
				self.ourNonvolatileData["problemReportTime"] = 0

		return(0)
	#
	# deviceUpdated
	#
	def	deviceUpdatedEvent(self, eventID, eventParameters):

		newOnState = eventParameters.get('onState', 'na')
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " deviceUpdatedEvent EventParameters:" + str(eventParameters) + ". newOnState is " + str(newOnState))

		# If we are blacked out, dont process the event.

		if self.blackOutTill > int(time.mktime(time.localtime())):
			if self.debugDevice: mmLib_Log.logForce( self.deviceName + " is not processing event \'onState:" + str(newOnState) + "\' because it was receive during blackout time.")
			return 0

		if 0:
			if self.onlineState == mmLib_Low.AUTOMATIC_MODE_SLEEP and newOnState == True:
				if self.debugDevice: mmLib_Log.logForce("Bringing " + self.deviceName + " back online.")
				self.setOnOffLine(mmLib_Low.AUTOMATIC_MODE_ACTIVE)
		else:
			# Similarly, if we are offline or sleeping, dont process the event.
			if self.onlineState == mmLib_Low.AUTOMATIC_MODE_SLEEP or self.onlineState == mmLib_Low.AUTOMATIC_MODE_OFFLINE:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Motion Skipped because Offline state is: " + self.onlineState)
				return 0

		if self.onlineState == mmLib_Low.AUTOMATIC_MODE_ACTIVE:

			if newOnState != mmLib_Low.AUTOMATIC_MODE_NOT_POSSIBLE:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + ": Motion Onstate = " + str(newOnState))
				super(mmMotion, self).deviceUpdatedEvent(eventID, eventParameters)  # the base class just keeps track of the time since last change
				self.controllerMissedCommandCount = 0			# Reset this because it looks like are controller is alive (battery report uses this)
				if newOnState == True:
					mmLib_Low.registerDelayedAction({'theFunction': self.delayProcForOnStateTimeout,
													 'timeDeltaSeconds': int(60 * 60 * 24),
													 'theDevice': self.deviceName,
													 'timerMessage': "Motion Sensor OnStateTimeout Timer"})
					# we are detecting motion
					if self.debugDevice:
						mmLib_Log.logForce( "Motion Sensor " + self.deviceName + " received update event: ON")

					self.countBounce()	# Collect Metrics regarding on/off sequences to tell if the sensor is bouncing

					# And dispatch the ON event
					self.dispatchOnOffEvents( mmComm_Insteon.kInsteonOn )	#kInsteonOn = 17

					# Check do motion sensor periodic tasks in the wake of this ON event (Insteon ONLY)
					#if self.isInsteonMotionDevice: self.insteonMotionPeriodicTasks()

				else:
					# Dispatch the Off event
					self.dispatchOnOffEvents(mmComm_Insteon.kInsteonOff )	#kInsteonOff = 19

					# Check do motion sensor periodic tasks in the wake of this OFF event (Insteon ONLY)
					if self.isInsteonMotionDevice: self.insteonMotionPeriodicTasks()

					# if we are already marked as unoccupied, debounce this event

					if self.occupiedState == False:
						if self.debugDevice: mmLib_Log.logForce(self.deviceName + " received an \'" + str(newOnState) + "\' event, but was already in unoccupied state... Ignoring the event.")
						return 0

					mmLib_Low.cancelDelayedAction(self.delayProcForOnStateTimeout)
					# We are detecting non-motion
					if self.debugDevice: mmLib_Log.logForce("Motion Sensor " + self.deviceName + " received update event: OFF")

					self.previousMotionOff = time.mktime(time.localtime())

				# do occupation event processing
				self.processOccupation(0)

			else:
				mmLib_Log.logError(self.deviceName + ": Unknown Onstate = " + str(newOnState))

		return(0)

	#
	# devStatus
	#
	def devStatus(self, theCommandParameters):

		self.reportFullStatus(0)

		return (0)

	#
	# loadDeviceNotificationOfOn - called from Load Devices
	# A load device associated with this motion sensor was manually turned on, note it for Battery performance tests
	#
	def loadDeviceNotificationOfOn(self):
		self.controllerMissedCommandCount = self.controllerMissedCommandCount + 1

		return(0)

	#
	# reportFullStatus - report status including debounce Problem for this device, if any
	#
	def reportFullStatus(self, sendEmail):

		theBody = "Status Report for " + self.deviceName

		if sendEmail:
			# send an email indicating the problem
			theBody = theBody + str("\r####### ")
		else:
			# just reporting status
			theBody = theBody + str("\r")

		listLength = len(self.ourNonvolatileData["rapidTransitionTimeList"])

		# report Online State
		theBody = theBody + "\rOnline State is: " + self.onlineState + "\r"

		# report Occupied State
		theBody = theBody + "It's reporting " + str(mmLib_Low.getIndigoVariable(self.occupationIndigoVar, "unknown reason")) + "\r"

		# Report When Occupation will end (if any)
		if OccupiedStateList[self.occupiedState] == "Occupied":
			projectedUnoccupiedEventTime = "Unknown Time"
			UnoccupiedReason = "of undefined reasons"
			if self.getOnState() == True:
				# sensor is showing ON, so delayProcForMaxOccupancy occupiedState transition now
				executionTime = int(mmLib_Low.findDelayedAction(self.delayProcForMaxOccupancy))
				if executionTime != 0:
					UnoccupiedReason = "maximum allowable time for motion has been reached"
					projectedUnoccupiedEventTime = mmLib_Low.minutesAndSecondsTillTime(executionTime)
					#projectedUnoccupiedEventTime = str(time.ctime(executionTime))
				else:
					mmLib_Log.logForce("#### " + self.deviceName + " is reporting occupied (while ON), yet there is no delayProcForMaxOccupancy delayProc registered to turn it off.")
			else:
				# sensor is showing OFF, so delayProcForNonOccupancy controls occupiedState transition now
				executionTime = int(mmLib_Low.findDelayedAction(self.delayProcForNonOccupancy))
				if executionTime != 0:
					UnoccupiedReason = "motion has stopped"
					projectedUnoccupiedEventTime = mmLib_Low.minutesAndSecondsTillTime(executionTime)
					#projectedUnoccupiedEventTime = str(time.ctime(executionTime))
				else:
					mmLib_Log.logForce("#### " + self.deviceName + " is reporting occupied (while OFF), yet there is no delayProcForNonOccupancy delayProc registered to turn it off.")

			theBody = theBody + "Will become Unoccupied in " + projectedUnoccupiedEventTime + " because " + UnoccupiedReason + "\r"

		if listLength > 1:
			theBody = str(theBody + self.deviceName + "'s number of off/on cycle times less than " + str(kMotionDevTolerableMotionBounceTime) + " seconds: " + str(listLength))

			theBody = theBody + "\rLast " + str(listLength) + " sequential off/on transition times to ON: \r"
			for newTimeStr in self.ourNonvolatileData["rapidTransitionTimeList"]:
				theBody = theBody + "\r" + newTimeStr
		else:
			theBody = theBody + "No sequential off/on transition times less than " + str(kMotionDevTolerableMotionBounceTime) + " seconds."

		mmLib_Log.logReportLine(theBody)

		if sendEmail:
			# send an email indicating the problem
			# only allow sending emails every 24 hours for this device
			if not self.ourNonvolatileData["problemReportTime"] or int(time.mktime(time.localtime()) - int(self.ourNonvolatileData["problemReportTime"])) > 60*60*24:
				theBody = "\r" + theBody + "\r"
				theSubject = str("MotionMap2 " + str(indigo.variables["MMLocation"].value)+ " MotionSensor Failure Report: " + self.deviceName)
				theRecipient = "greg@GSBrewer.com"
				indigo.server.sendEmailTo(theRecipient, subject=theSubject, body=theBody)
				# update the problem report time
				self.ourNonvolatileData["problemReportTime"] = time.mktime(time.localtime())
				self.ourNonvolatileData["problemReportTimeHumanReadable"] = '{:%a %b %-d, %Y %-I:%M %p}'.format(datetime.now())
			else:
				mmLib_Log.logWarning( self.deviceName + " is reporting MotionSensorFailure, but email was supressed due to recent delivery at " + str(self.ourNonvolatileData["problemReportTimeHumanReadable"]))


	#
	# checkBattery - report the status of this device's battery
	# 	FORCE it to the log
	#	returns 0 if good battery, nonzero if bad
	#
	#	Parameter "ReportType" =
	#		'DEAD'	Report only Dead or unresponsive controller devices
	#		'LIVE'	Report All controller type devices that are responsive
	#		'ALL'	Report All Controllers. regardless of responsiveness (includes motion sensitive cameras)
	#
	def checkBattery(self, theCommandParameters):

		theReportType = theCommandParameters["ReportType"]
		itsDead = 0
		addString = ""

		if self.isInsteonMotionDevice:
			preamble = str(self.deviceName + "\'s battery Level is " + str(self.ourNonvolatileData["batteryLevel"]) + " (as of " + str(self.ourNonvolatileData["batteryQueryTimeSecondsStr"]) + "). ")
		else:
			preamble = self.deviceName + " does not support Battery Level Requests. "

		# Has it experienced too many missed commands
		if self.controllerMissedCommandCount > mmLib_Low.MOTION_MAX_MISSED_COMMANDS:
			addString = addString + "It has missed " + str(self.controllerMissedCommandCount) + " events. "
			itsDead = 1

		# if the device is ON, see if has been on too long
		if self.getOnState() == True:
			if self.getSecondsSinceUpdate() > mmLib_Low.MOTION_MAX_ON_TIME:
				addString = addString + "It has been on for " + str(round(int(self.getSecondsSinceUpdate()) / int(60 * 60), 2)) + " hours. Setting it to Off. "
				indigo.device.turnOff(self.devIndigoID)	# doesn't honor the unresponsive flag because this just sets state in indigo (no command is sent to the device)
		else:
			if self.getSecondsSinceUpdate() > mmLib_Low.MOTION_MAX_OFF_TIME:
				addString = addString + "It has been off for " + str(round(int(self.getSecondsSinceUpdate()) / int(24 * 60 * 60), 2)) + " days. "
				itsDead = 1

		if itsDead: addString = addString + "The device may need to be reset or the battery may be dead."
		addString = preamble + addString

		if theReportType != "ALL":
			if theReportType == "DEAD":
				# We are reporting only dead devices
				if itsDead == 0:
					addString = ""
			elif theReportType == "LIVE":
				# We are reporting only live devices
				if itsDead:
					addString = ""

		return(addString)

	#
	# forceTimeout - The device we are controlling was manually turned off, so cancel our offTimers if there are any
	# plus, blackout for a few seconds as specified
	#
	def forceTimeout(self,BlackOutTimeSecs):


		self.blackOutTill = int(time.mktime(time.localtime())) + BlackOutTimeSecs
		if self.debugDevice: mmLib_Log.logForce("Motion sensor " + self.deviceName + " received a forceTimeout.")
		mmLib_Low.cancelDelayedAction(self.delayProcForNonOccupancy)  # No Longer Valid
		mmLib_Low.cancelDelayedAction(self.delayProcForMaxOccupancy)  # No longer Valid
		self.delayProcForNonOccupancy({})

		return 0