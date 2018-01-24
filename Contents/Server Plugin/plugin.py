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

	mmLib_Log.logForce("Parsing config file: " + _MotionMapPlugin.MM_DEFAULT_CONFIG_FILE)
	savedInitValue = pluginInitialized
	pluginInitialized = 0
	timerQueue = deque()
	mmLib_CommandQ.qInit()
	mmLib_Config.init(_MotionMapPlugin.MM_DEFAULT_CONFIG_FILE)
	pluginInitialized = savedInitValue


############################################################################################
# mmTestCode
#
############################################################################################
def mmTestCode(theCommandParameters):


	if 0:
		theStartTime = time.clock()
		for theCount in range(1000):
			#mmLib_Low.setIndigoVariable("mmTestVariable", "TestValue")
			mmLib_Log.logForce("=== Testing SetIndigoVar")
		newTime = time.clock()

		mmLib_Log.logForce("### Plugin.py:mmTestCode Test Code Timing: " + str((newTime - theStartTime)) + " seconds.")

		theStartTime = time.clock()
		for theCount in range(1000):
			#mmLib_Low.mmNonVolatiles["mmTestVariable"] = "TestValue"
			mmLib_Log.logForce("=== Testing SetNVVar")
		newTime = time.clock()

		mmLib_Log.logForce("### Plugin.py:mmTestCode Test Code Timing 2: " + str((newTime - theStartTime)) + " seconds.")

		mmLib_Log.logForce("=== Testing Log function")

		indigo.server.log("Try logDebug")
		mmLib_Log.logDebug("=====logDebug Demo")

		indigo.server.log("Try logVerbose")
		mmLib_Log.logVerbose("=====logVerbose Demo")

		indigo.server.log("Try logTerse")
		mmLib_Log.logTerse("=====logTerse Demo")

		indigo.server.log("Try logWarning")
		mmLib_Log.logWarning("=====logWarning Demo")

		indigo.server.log("Try logError")
		mmLib_Log.logError("=====logError Demo")

		indigo.server.log("Try logForce")
		mmLib_Log.logForce("=====logForce Demo")

		indigo.server.log("Try logTimestamp")
		mmLib_Log.logTimestamp("=====logTimestamp Demo")

		indigo.server.log("Try logReportLine")
		mmLib_Log.logReportLine("=====logReportLine Demo")
	else:

		theStartTime = time.clock()
		for i in range(0,100):
			mmLib_Log.logForce("=====logForce Demo " + str(i))
		newTime = time.clock()
		mmLib_Log.logForce("### Plugin.py:mmTestCode Test Code Timing 1: " + str((newTime - theStartTime)) + " seconds.")

		theStartTime = time.clock()
		for i in range(0,100):
			mmLib_Log.logForceX("=====logForce Demo " + str(i))
		newTime = time.clock()
		mmLib_Log.logForce("### Plugin.py:mmTestCode Test Code Timing 2: " + str((newTime - theStartTime)) + " seconds.")

		theStartTime = time.clock()
		for i in range(0,100):
			mmLib_Log.logForce("=====logForce Demo " + str(i))
		newTime = time.clock()
		mmLib_Log.logForce("### Plugin.py:mmTestCode Test Code Timing 1B: " + str((newTime - theStartTime)) + " seconds.")

	return(1)


############################################################################################
#
# supportedControlCommandsDict - list of functions exposed to outside world through plugin.executeMMCommand
#	they all take a single parameter that is a dictionary list of command options
#
############################################################################################

supportedControlCommandsDict = {'resetOfflineStatistics':mmLib_Low.resetOfflineStatistics, 'printCommandQueue':mmLib_CommandQ.printQ, 'printDelayQueue':mmLib_Low.mmPrintDelayedProcs, 'emptyCommandQ':mmLib_CommandQ.emptyQ, 'popCommandQ':mmLib_CommandQ.popQ, 'restartCommandQ':mmLib_CommandQ.restartQ, 'reparseConfig':mmParseConfig, 'testCode':mmTestCode, 'SetLogSensitivity':mmLib_Log.setLogSensitivityMMCommand, 'motionStatus': mmLib_Low.displayMotionStatus, 'offlineReport': mmLib_Low.processOfflineReport, 'verifyLogMode':mmLib_Log.verifyLogMode, 'batteryReport':mmLib_Low.batteryReport}


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
	#	deltaTime = time.time()

		mmLib_Log.logForce("---" + _MotionMapPlugin.MM_NAME + " plugin version " + _MotionMapPlugin.MM_VERSION + ". Startup called")

	#	deltaTime = time.time()
		mmLib_Log.start()
	#	mmLib_Log.logForce("  +TIMETRACK:" + str(round(time.time() - deltaTime, 2)) + "s. mmLib_Log.start() completed.")

	#	deltaTime = time.time()
		mmLib_Low.init()
	#	mmLib_Log.logForce("  +TIMETRACK:" + str(round(time.time() - deltaTime, 2)) + "s. mmLib_Log.start() completed.")

	#	deltaTime = time.time()
		mmLib_Low.mmSubscribeToEvent('initComplete', self.initComplete)
	#	mmLib_Log.logForce("  +TIMETRACK:" + str(round(time.time() - deltaTime, 2)) + "s. initcompleteSubscribe() completed.")

	#	deltaTime = time.time()
		result = mmParseConfig({'theCommand':'reparseConfig'})
	#	mmLib_Log.logForce("  +TIMETRACK:" + str(round(time.time() - deltaTime, 2)) + "s. mmParseConfig() completed.")

	#	deltaTime = time.time()
		mmLib_Low.restoreOfflineStatistics()
	#	mmLib_Log.logForce("  +TIMETRACK:" + str(round(time.time() - deltaTime, 2)) + "s. restoreOfflineStatistics() completed.")

	#	deltaTime = time.time()
		indigo.insteon.subscribeToIncoming()
		indigo.insteon.subscribeToOutgoing()
		indigo.devices.subscribeToChanges()
	#	mmLib_Log.logForce("  +TIMETRACK:" + str(round(time.time() - deltaTime, 2)) + "s. messageSubscriptions() completed.")

		# Run subscriptions for all objects in the init queue
	#	deltaTime = time.time()
		mmLib_Low.mmRunSubscriptions('initComplete')
	#	mmLib_Log.logForce("  +TIMETRACK:" + str(round(time.time() - deltaTime, 2)) + "s. initSubscribeRUN() completed.")


	########################################
	#
	#		testInitComplete	The plugin is being called to stop and shutdown
	#
	########################################
	def initComplete(self):

		global pluginInitialized

		pluginInitialized = 1


		# initialize daytime value for all devices that care. We do this before the following
		# subscribes because we dont want to see the morning reports every time we start up
		mmLib_Low.mmDaylightTransition(indigo.variables['MMDayTime'].value)

		mmLib_Low.mmSubscribeToEvent('isDayTime', mmLib_Low.mmIsDaytime)
		mmLib_Low.mmSubscribeToEvent('isNightTime', mmLib_Low.mmIsNighttime)

		mmLib_Log.logError("--- " + _MotionMapPlugin.MM_NAME + " plugin: startup completed in " + str(round(time.time() - startTime, 2)) + " seconds. ")

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
	#	initLogger	Setup logging jump table
	#
	########################################
	def initLogger(self):

		#
		#  Note logger colors:
		#
		#  		self.logger.debug(u"Debug log message")			# Gray
		#		self.logger.info(u"Info log message")			# Black
		#		self.logger.warn(u"Warning log message")		# Black
		#		self.logger.error(u"Error log message")			# Red
		#		self.logger.critical(u"Critical log message")	# Red
		#
		#
		#	MM_LOG_DEBUG_NOTE = 0
		#	MM_LOG_VERBOSE_NOTE = 1
		#	MM_LOG_TERSE_NOTE = 2
		#	MM_LOG_WARNING = 3
		#	MM_LOG_ERROR = 4
		#	MM_LOG_FORCE_NOTE = 5
		#	MM_LOG_TIMESTAMP = 6
		#	MM_LOG_REPORT = 7
		#

		self.loggerDispatchTable = [self.logger.debug, self.logger.info, indigo.server.log, self.logger.warn, self.logger.error, indigo.server.log, indigo.server.log, indigo.server.log]


	########################################
	#
	#	dispatchLog	The plugin is being called display a message on the indigo console
	#
	########################################
	def dispatchLog(self, theMessage, indigoLogType, mmLogType):

		theLogFunction = self.loggerDispatchTable[mmLogType]

		if theLogFunction == indigo.server.log:
			theLogFunction(theMessage, indigoLogType)
		else:
			theLogFunction(indigoLogType + theMessage)





	########################################
	#
	#	insteonCommandReceived
	#
	#  	The server received an insteon command
	#	This routine is called because it was registered for by indigo.insteon.subscribeToIncoming()
	#	in startup
	#
	########################################
	def insteonCommandReceived(self, cmd):
		if pluginInitialized == 0: return()

		#mmLog.logForce( "Command Received for ID: " + str(cmd.address) )

		try:
			mmDev = mmLib_Low.MotionMapDeviceDict[str(cmd.address)]
		except:
			# Not our device
			# mmLib_Log.logForce( "Received a command, but not our device ID: " + str(cmd.address))
			return 0

		mmLib_Log.logVerbose("Received Command from " + str(mmDev.deviceName))
		if mmDev.parseCommand(cmd):
			# done processing
			return 0

		mmDev.receivedCommand( cmd )


	########################################
	#
	#	insteonCommandSent
	#
	#  	The server sent an insteon command
	#	This routine is called because it was registered for by indigo.insteon.subscribeToOutgoing()
	#	in startup
	#
	#
	########################################
	def insteonCommandSent(self, cmd):
		if pluginInitialized == 0: return()
		#indigo.server.log(str(cmd))

		if cmd.cmdScene > 0:
			devAddress = mmLib_Low.makeSceneAddress(cmd.cmdScene)
			mmLib_Log.logVerbose("Scene " + str(cmd.cmdFunc) + " complete for: " + str(devAddress) + "\n" + str(cmd))
		else:
			devAddress = str(cmd.address)

		theDev = mmLib_CommandQ.getQTopDev()

		if not theDev or str(theDev.devIndigoAddress) != str(devAddress):
			# Not our device
			return 0

		if theDev.parseCompletion(cmd):
			# done processing
			return 0

		try:
			theCommandByte = cmd.cmdBytes[0]
		except:
			theCommandByte = 0


		if cmd.cmdSuccess == 1:
			mmLib_Log.logDebug("Successful command: " + str(theCommandByte) + " Sent to " + str(theDev.deviceName))
			theDev.completeCommand( cmd )
		else:
			mmLib_Log.logForce("Unsuccessful command: " + str(theCommandByte) + " for " + str(theDev.deviceName))
			theDev.errorCommand( cmd )

	########################################
	#
	#	deviceUpdated
	#
	#  	A device has had some sort of change, process the new state accordingly
	#	This routine is called because it was registered for by indigo.insteon.subscribeToChanges()
	#	in startup
	#
	########################################
	def deviceUpdated(self, origDev, newDev):
		if pluginInitialized == 0: return()


		try:
			mmSignature = mmLib_Low.makeMMSignature(newDev.id, newDev.address)
		except:
			mmLib_Log.logForce("Device Update. Cannot make signature for device: " + str(newDev))
			return 0


		try:
			mmDev = mmLib_Low.MotionMapDeviceDict[mmSignature]
		except:
			# Not our device
			return 0

		#mmLib_Log.logForce("Device Update. Signature: " + str(mmSignature) + " " + mmDev.deviceName)

		#if newDev.__class__ == indigo.DimmerDevice:mmLog.logForce( str(mmDev.deviceName) + " has been updated to " + str(newDev.brightness))

		# lets copy over the data points of interest
		mmDev.theIndigoDevice = newDev

		# Update the timestamp of the device, and move him to the end of the update queue
		mmDev.updateTimeStamp = time.time()

		if mmDev.parseUpdate(origDev, newDev):
			# done processing
			return 0

		mmDev.deviceUpdated(origDev, newDev)

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

		global timerQueue

		localIsDaylight = indigo.variables['MMDayTime'].value

		loopCounter = 0
		try:
			while True:
				if pluginInitialized == 0:
					mmLib_Log.logForce(">>> calling runConcurrentThread before initialization")
					self.sleep(5) # in seconds
				else:
					self.sleep(mmLib_Low.TIMER_QUEUE_GRANULARITY) # in seconds
					mmLib_Low.mmRunTimer()
					newDaylightValue = indigo.variables['MMDayTime'].value

					if localIsDaylight != newDaylightValue:
						localIsDaylight = newDaylightValue
						mmLib_Low.mmDaylightTransition(newDaylightValue)

		except self.StopThread:
			# do any cleanup here
			mmLib_Low.saveOfflineStatistics()


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

		if "theCommand" in pluginAction.props:
			doCommand = str(pluginAction.props.get("theCommand"))
		else:
			mmLib_Log.logWarning("No command given in executeMMCommand")
			return(0)

		# Dispatch the mm control command (not a device command)
		# All control commands are immediate

		try:
			theFunction = supportedControlCommandsDict[doCommand]
		except:
			theFunction = 0

		if theFunction != 0:
			return(theFunction(pluginAction.props))
		else:
			if "theDevice" in pluginAction.props:
				theDeviceName = str(pluginAction.props.get("theDevice"))

				try:
					theDevice = mmLib_Low.MotionMapDeviceDict[theDeviceName]
				except:
					mmLib_Log.logWarning("Couldnt find device named: " + theDeviceName)
					return(0)

				# check to see if it should be queued or executed
				theMode = "QUEUE"
				if "theMode" in pluginAction.props: theMode = pluginAction.props.get("theMode")

				if theMode == "IMMED":
					return(theDevice.dispatchCommand(pluginAction.props))	# do the command now
				else:
					return(theDevice.queueCommand(pluginAction.props))	# queue it for later


