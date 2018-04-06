__author__ = 'gbrewer'
# ! /usr/bin/env python
# -*- coding: utf-8 -*-



##################################################################################
############################ Runtime Directives ##################################
##################################################################################

import _MotionMapPlugin

##################################################################################
#
#	System Definitions
#
##################################################################################

try:
	import indigo
except:
	pass

import mmLib_Log
import mmLib_Low
import mmLib_Events

import mmLib_CommandQ
import mmLib_Config
from timeit import default_timer as timer
import time
from collections import deque

pluginInitialized = 0
startTime = 0


########################################
#
# Command processing support routines
#
########################################


############################################################################################
# mmParseConfig
#	theCommandParameters is a required parameter because of architecture, but it is unused here
############################################################################################
def mmParseConfig(theCommands):

	global pluginInitialized

	savedInitValue = pluginInitialized
	pluginInitialized = 0
	mmLib_CommandQ.qInit()
	mmLib_Config.init(_MotionMapPlugin.MM_DEFAULT_CONFIG_FILE)
	pluginInitialized = savedInitValue


############################################################################################
# mmTestCode
#
############################################################################################
def mmTestCode(theCommandParameters):

	theStartTime = time.clock()
	for theCount in range(100):
		mmLib_Log.logForce("===== New logForce   " + str(theCount))
	newTime = time.clock()
	mmLib_Log.logForce("### Plugin.py:mmTestCode Test Code Timing 0: " + str((newTime - theStartTime)) + " seconds.")

	return(1)


############################################################################################
#
# supportedControlCommandsDict - list of functions exposed to outside world through plugin.executeMMCommand
#	they all take a single parameter that is a dictionary list of command options
#
############################################################################################

supportedControlCommandsDict = {'resetOfflineStatistics':mmLib_Low.resetOfflineStatistics,
								'printCommandQueue':mmLib_CommandQ.printQ,
								'printDelayQueue':mmLib_Low.mmPrintDelayedProcs,
								'emptyCommandQ':mmLib_CommandQ.emptyQ,
								'popCommandQ':mmLib_CommandQ.popQ,
								'restartCommandQ':mmLib_CommandQ.restartQ,
								'reparseConfig':mmParseConfig,
								'testCode':mmTestCode,
								'SetLogSensitivity':mmLib_Log.setLogSensitivityMMCommand,
								'motionStatus': mmLib_Low.displayMotionStatus,
								'offlineReport': mmLib_Low.processOfflineReport,
								'verifyLogMode':mmLib_Log.verifyLogMode,
								'batteryReport':mmLib_Low.batteryReport}


############################################################################################
############################################################################################
#
#  Main Object. This is an indigo server plugin
#
############################################################################################
############################################################################################

class Plugin(indigo.PluginBase):


	# Note the "indigo" module is automatically imported and made available inside
	# our global name space by the host process.


	##############################################################################
	#
	# Plugin Framework Routines... Called by the Indigo Server
	#
	##############################################################################


	########################################
	#
	# __init__		Initialize/Allocate the plugin
	#				The plugin is trying to be integrated into the system.
	#				Check to see if we can run etc, return true if things look good
	#
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):

		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

		self.debug = True

		mmLib_Log.init("MotionMap.log.txt", self)
		mmLib_Log.logForce(_MotionMapPlugin.MM_NAME + " Plugin version " + _MotionMapPlugin.MM_VERSION + ". Initialization complete. Waiting for Startup Command.")


	########################################
	#
	# __del__		Delete the plugin
	#				The plugin is being deleted from the system. Freem memory etc.
	#
	########################################
	def __del__(self):
		indigo.PluginBase.__del__(self)



	########################################
	#
	#	startup		The plugin is being called to initialize
	#
	########################################
	def startup(self):
		global startTime

		startTime = time.time()

		mmLib_Log.logForce("---" + _MotionMapPlugin.MM_NAME + " plugin version " + _MotionMapPlugin.MM_VERSION + ". Startup called")

		mmLib_Log.start()
		mmLib_Low.init()
		result = mmParseConfig({'theCommand':'reparseConfig'})
		indigo.insteon.subscribeToIncoming()
		indigo.insteon.subscribeToOutgoing()
		indigo.devices.subscribeToChanges()



	########################################
	#
	#		testInitComplete	The plugin is being called to stop and shutdown
	#
	########################################
	def initComplete(self):

		global pluginInitialized
		global startTime


		pluginInitialized = 10
		mmLib_Log.logForce("  System Initialization completed. Running Device INIT subscriptions")
		# Run subscriptions for all objects in the init queue
		mmLib_Low.refreshControllers()
		try:
			mmLib_Events.subscribeToEvents(['isNightTime', 'isDayTime'], ['MMSys'], mmLib_Low.daytimeTransition, {}, 'MMSys')
		except:
			mmLib_Log.logForce("MMSys SubscribeToEvents \'isNightTime\' or \'isDayTime\' failed.")

		try:
			mmLib_Events.distributeEvents('MMSys', ['initComplete'], 0, {})
		except Exception as exception:
			mmLib_Log.logError( "MMSys Distributing \'initComplete\' failed. Exception: " + str(exception))

		# initialize daytime value for all devices that care. We do this before the following
		# subscribes because we dont want to see the morning reports every time we start up
		mmLib_Low.mmDaylightTransition(indigo.variables['MMDayTime'].value)


		mmLib_Log.mmDebugNote("--- " + _MotionMapPlugin.MM_NAME + " plugin: startup completed in " + str(round(time.time() - startTime, 2)) + " seconds. ")

		return

	########################################
	#
	#	shutdown	The plugin is being called to stop and shutdown
	#
	########################################
	def shutdown(self):
		global pluginInitialized

		mmLib_Log.logDebug("### Shutdown called -- Shutting Down MotionMap")
		pluginInitialized = 0	# Stop all processing
		mmLib_Low.cacheNVDict()	# cache the nonvolatiles


	########################################
	#
	#	insteonCommandReceived
	#
	#  	The server received an insteon command
	#	This routine is called because it was registered for by indigo.insteon.subscribeToIncoming()
	#	in startup
	#
	#	This function handles all command notices from indigo (i.e. when a light switch is turned on, that notification comes here)
	#	It converts this notification to an mmEvent of type 'DevRcvCmd' and dispatches it through mmLib_Events.distributeEvents()
	#
	#	For an mmObject to receive these events the object must call the following function at initialization time:
	#  		def subscribeToEvents(['DevRcvCmd'], ['Indigo'], theHandler, { handlerDefinedData - whatever static data you want delivered at time of event }, mmDevName):
	#	The event will be delivered as:
	#		theHandler('DevRcvCmd', {'DevRcvCmd', 'Indigo', Time of Event (seconds), Plus "handlerDefinedData", cmd (from Indigo)  })
	#
	########################################
	def insteonCommandReceived(self, cmd):
		global pluginInitialized

		if pluginInitialized == 0: return()

		try:
			mmDev = mmLib_Low.MotionMapDeviceDict[str(cmd.address)]
		except:
			# Not our device
			# Note cmd does not have devID, so you have to use address
			# this is technically broken with no work around. It only effects OutletLinc that shares address between top and bottom outlets
			# the moral of the story is dont rely on cmd where you can avoid it... rely on deviceUpdated where possible.
			mmLib_Log.logWarning( "Received a command, but not our device ID: " + str(cmd.address))
			return 0

		try:
			mmLib_Events.distributeEvents('Indigo', ['DevRcvCmd'], mmDev.deviceName, {'cmd': cmd})		# for MM version 4
		except:
			mmLib_Log.logWarning( "Failed to deliver a \'DevRcvCmd\' event")




	########################################
	#
	#	insteonCommandSent
	#
	#  	The server sent an insteon command
	#	This routine is called because it was registered for by indigo.insteon.subscribeToOutgoing()
	#	in startup
	#
	#	This function handles all command Sent notices from indigo (i.e. when a command MM sends completes, that notification comes here)
	#	It converts the notification to an mmEvent of type 'DevCmdComplete' or 'DevCmdErr' depending on disposition and dispatches it
	# 	through mmLib_Events.distributeEvents()
	#
	#	For an mmObject to receive these events the object must call the following function at initialization time:
	#  		def subscribeToEvents(['DevCmdComplete'], ['Indigo'], theHandler, { handlerDefinedData - whatever static data you want delivered at time of event }, mmDevName):
	#	or
	#  		def subscribeToEvents(['DevCmdErr'], ['Indigo'], theHandler, { handlerDefinedData - whatever static data you want delivered at time of event }, mmDevName):
	#
	# 	The event will be delivered as:
	#		theHandler('DevCmdComplete', {'DevCmdComplete', Indigo, Time of Event (seconds), Plus "handlerDefinedData", cmd (from Indigo)  })
	#	or
	#		theHandler('DevCmdErr', {'DevCmdErr', 'Indigo', Time of Event (seconds), Plus "handlerDefinedData", cmd (from Indigo)  })
	#
	########################################
	def insteonCommandSent(self, cmd):

		global pluginInitialized
		if pluginInitialized == 0: return()
		#indigo.server.log(str(cmd))

		if cmd.cmdScene > 0:
			devAddress = mmLib_Low.makeSceneAddress(cmd.cmdScene)
			#mmLib_Log.logForce("Scene " + str(cmd.cmdFunc) + " complete for: " + str(devAddress) + "\n" + str(cmd))
		else:
			# Note cmd does not have devID, so you have to use address
			# however, since this is a command completion, the last command we sent out should be on the top of the queue
			devAddress = str(cmd.address)

		theDev = mmLib_CommandQ.getQTopDev()

		if not theDev or str(theDev.devIndigoAddress) != str(devAddress):
			# Not our device, but it could be a status (we send those async and dont wait for response)
			#mmLib_Log.logForce("Got an Indigo Complete, but device is not ours getQDevTop = " + str(theDev) + " DevAddr = " + str(devAddress))
			return 0

		try:
			theCommandByte = cmd.cmdBytes[0]
		except:
			theCommandByte = 0

		if cmd.cmdSuccess == 1:
			theEvent = 'DevCmdComplete'
			mmLib_Log.logDebug("Successful command: " + str(theCommandByte) + " Sent to " + str(theDev.deviceName))
		else:
			mmLib_Log.logForce("Unsuccessful command: " + str(theCommandByte) + " for " + str(theDev.deviceName))
			theEvent = 'DevCmdErr'

		try:
			mmLib_Events.distributeEvents('Indigo', [theEvent], theDev.deviceName, {'cmd': cmd})		# for MM version 4
		except:
			mmLib_Log.logWarning( "Failed to deliver a \'" + theEvent + "\' event.")

		#if cmd.cmdSuccess == 1:
		#	mmLib_Log.logDebug("Successful command: " + str(theCommandByte) + " Sent to " + str(theDev.deviceName))
		#	theDev.completeCommand( cmd )
		#else:
		#	mmLib_Log.logForce("Unsuccessful command: " + str(theCommandByte) + " for " + str(theDev.deviceName))
		#	theDev.errorCommand( cmd )




	########################################
	#
	#	deviceUpdated
	#
	#  	A device has had some sort of change, process the new state accordingly
	#	This routine is called because it was registered for by indigo.insteon.subscribeToChanges()
	#	in startup
	#
	#	This function handles all device change notices from indigo (i.e. when a motion sensor changes state, that notification comes here)
	#	It converts the notification to an mmEvent of type 'AtributeUpdate' and dispatches it through mmLib_Events.distributeEvents()
	#
	#	For an mmObject to receive these events the object must call the following function at initialization time:
	#  		def subscribeToEvents(['AtributeUpdate'], ['Indigo'], theHandler, { handlerDefinedData - whatever static data you want delivered at time of event }, mmDevName):
	#	The event will be delivered as:
	#		theHandler('DevRcvCmd', {'AtributeUpdate', 'Indigo', Time of Event (seconds), Plus "handlerDefinedData", cmd (from Indigo)  })
	#
	#########################################
	def deviceUpdated(self, origDev, newDev):
		global pluginInitialized

		if pluginInitialized == 0: return()


		try:
			mmDev = mmLib_Low.MotionMapDeviceDict[newDev.name]
		except:
			return 0

		# Update the indigo device in case it changed out behind our back (this just copies the reference to the device)
		#if mmDev.theIndigoDevice != newDev:
			# Just a test to see if this ever happens... I dont think it does
		#	mmLib_Log.logForce("theIndigoDevice has changed for " + str(mmDev.deviceName))
		mmDev.theIndigoDevice = newDev

		mmLib_Events.deliverUpdateEvents(origDev, newDev, newDev.name)

		# be sure and call parent function
		indigo.PluginBase.deviceUpdated(self, origDev, newDev)



	########################################
	#
	#	runConcurrentThread
	#
	#  	Periodic time to process motion events, queue maintenance, etc
	#
	########################################
	def runConcurrentThread(self):

		global pluginInitialized

		localIsDaylight = indigo.variables['MMDayTime'].value

		try:
			while True:
				if pluginInitialized == 0:
					try:
						self.initComplete()
					except:
						mmLib_Log.logForce("Failed to initialize in initComplete(). Trying again in 5 seconds.")
						pluginInitialized = 0
						self.sleep(5) # in seconds

				else:
					self.sleep(mmLib_Low.TIMER_QUEUE_GRANULARITY) # in seconds
					mmLib_Low.mmRunTimer()
					newDaylightValue = indigo.variables['MMDayTime'].value

					if localIsDaylight != newDaylightValue:
						mmLib_Log.logDebug("Running mmDaylightTransition(). localIsDaylight and newDaylightValue are " + str(localIsDaylight) + " and " + str(newDaylightValue))
						localIsDaylight = newDaylightValue
						mmLib_Low.mmDaylightTransition(newDaylightValue)

#		except self.StopThread:
		except:
			# do any cleanup here
			pass

########################################
#
# High level access to devices
#
########################################


	########################################
	#
	#	executeMMCommand
	#
	#  	An array of test commands are supported here.
	# 	Access them from indigo through script:
	#
	#	mmId = "motionmap.listener"
	#	mmPlugin = indigo.server.getPlugin(mmId)
	#	if mmPlugin.isEnabled():
	#		mmPlugin.executeAction("executeMMCommand", deviceId=0, props={'theCommand':6})
	#	else:
	#		indigo.server.log(">>> MotionMap is NOT Enabled")
	#
	#	Where the commands are defined as follows:
	#
	#		Command selectors (theCommand) are found in pluginAction.props.get("theCommand")
	#		The associated parameters are found by name in pluginAction.props.get
	#
	# 	Command brighten		Sets the brightness of a light (dimmer), or the On/Off value for a switch
	#
	#	Parameters
	#			theDevice				the name of the device
	#			theValue				0=off or 1-100 = Brightness (or on in the case of a switch)
	#			theMode					Optional: IMMED means no queue, just do it
	#
	########################################
	def executeMMCommand(self, pluginAction):

		# Parse the command

		theCommandParameters = {}


		# for some reason, if you just do theCommandParameters = pluginAction.props, you cant set anything in the
		# dict to an object pointer, so we have to make a copy of the parameters one by one. It must be the way
		# indigo makes their dict, it cant convert an object... you grt an error like this:
		#   Error: No registered converter was able to produce a C + + rvalue of type CCString from this Python object of type mmScene

		for key, value in pluginAction.props.iteritems():
			theCommandParameters[key] = value

		#mmLib_Log.logForce("executeMMCommand: " + str(theCommandParameters))

		doCommand = theCommandParameters.get('theCommand', 0)

		if not doCommand:
			mmLib_Log.logWarning("No command given in executeMMCommand")
			return(0)

		# Dispatch the mm control command (not a device command)
		# All control commands are immediate

		try:
			# Is it a system command?
			theFunction = supportedControlCommandsDict[doCommand]
		except:
			theFunction = 0

		if theFunction != 0:
			# Yes System Command, just do it
			return(theFunction(theCommandParameters))
		else:
			# Not a system Command, load the object and dispatch the command

			theDeviceName = theCommandParameters.get('theDevice', 0)
			if theDeviceName:
				try:
					theDevice = mmLib_Low.MotionMapDeviceDict[theDeviceName]
				except:
					mmLib_Log.logForce("Couldnt find device named: " + theDeviceName )
					#mmLib_Log.logWarning("Couldnt find device named: " + theDeviceName + " \r" + str(mmLib_Low.MotionMapDeviceDict) )
					return(0)

				# check to see if it should be queued or executed
				theMode = "QUEUE"
				if "theMode" in theCommandParameters: theMode = theCommandParameters['theMode']

				if theMode == "IMMED":
					return(theDevice.dispatchCommand(theCommandParameters))	# do the command now
				else:
					return(theDevice.queueCommand(theCommandParameters))	# queue it for later
			else:
				mmLib_Log.logForce("executeMMCommand: No device Name given for " + str(doCommand))

