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
#import os.path
import os
import logging

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
								'unregisteredReport': mmLib_Low.processUnregistertedReport,
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

	IndigoLogHandler = 0

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

		mmLib_Low.mmLogFolder = str(os.path.expanduser("~") + "/MotionMap3 Logs/")	# moved the log folder to the user space

		try:
			os.mkdir(mmLib_Low.mmLogFolder)
		except Exception as err:
			if err.args[0] != 17:
				print ("Creation of the directory %s failed" % mmLib_Low.mmLogFolder)


		self.debug = True

		mmLib_Log.init("MotionMap.log", self)


		mmLib_Log.logTimestamp(_MotionMapPlugin.MM_NAME + " Plugin version " + _MotionMapPlugin.MM_VERSION + ". Initialization complete. Waiting for Startup Command.")


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
		global mmFilePath

		startTime = time.time()

		mmLib_Log.logForceGray("### " + _MotionMapPlugin.MM_NAME + " plugin version " + _MotionMapPlugin.MM_VERSION + ". Startup called")

		mmLib_Log.start()
		mmLib_Low.init()
		result = mmParseConfig({'theCommand':'reparseConfig'})
		indigo.insteon.subscribeToIncoming()
		indigo.insteon.subscribeToOutgoing()
		indigo.devices.subscribeToChanges()



	########################################
	#
	#		InitComplete	The plugin is Up and runningn
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
			# subscribe to daily transitions to do system things (battery reporting offline reporting etc)
			mmLib_Events.subscribeToEvents(['isNightTime', 'isDayTime'], ['MMSys'], mmLib_Low.daytimeTransition, {}, 'MMSys')
		except:
			mmLib_Log.logForce("MMSys SubscribeToEvents \'isNightTime\' or \'isDayTime\' failed.")

		try:
			mmLib_Events.distributeEvents('MMSys', ['initComplete'], 0, {})
		except Exception as exception:
			mmLib_Log.logError( "MMSys Distributing \'initComplete\' failed. Exception: " + str(exception))

		mmLib_Log.logForceGray("### " + _MotionMapPlugin.MM_NAME + " plugin: startup completed in " + str(round(time.time() - startTime, 2)) + " seconds. ")
		mmLib_Log.logTimestamp( _MotionMapPlugin.MM_NAME + " Startup complete. " + _MotionMapPlugin.MM_NAME + " is now running.")

		return

	########################################
	#
	#	shutdown	The plugin is being called to stop and shutdown
	#
	########################################
	def shutdown(self):
		global pluginInitialized

		pluginInitialized = 0	# Stop all processing
		mmLib_Low.cacheNVDict()	# cache the nonvolatiles
		mmLib_Log.logTimestamp("### " + _MotionMapPlugin.MM_NAME + "Shutdown requested. MotionMap session complete.")


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
			# Note cmd does not have devID... we only have access to address...
			# Its a limitation in the insteon/indigo architecture with no easy work around.
			# The real difficulty is on devices that have several IDs for one Address... For example:
			# OutletLinc (that share addresses between top and bottom outlets) and Zwave multifunction devices.
			#
			# We resolve this by keeping a list (motionMapDict) that contains the device name which we use for all operations.
			# If processing got here, we captured a command from a device that is not listed in MM conmfig file. We want
			# to keep a list of these devices so we can emit a warning to the log (so we can add the device to the known device list).

			mmLib_Log.logWarning( "Unknown device. Please edit \'" + "mmConfig." + str(_MotionMapPlugin.MM_Location) + ".csv" + "\' to add " + str(cmd.address) + ": " + mmLib_Low.addressTranslate(str(cmd.address) + " "))
			return 0

		try:
			#if mmDev.debugDevice: mmLib_Log.logForce(mmDev.deviceName + " insteonCommandReceived at Plugin.py with CMD: " + str(cmd))
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

		#mmLib_Log.logForce( "###CommandComplete with address: "+ str(devAddress))

		theDev = mmLib_CommandQ.getQTopDev()

		if not theDev or str(theDev.devIndigoAddress) != str(devAddress):
			# Not our device, but it could be a status (we send those async and dont wait for response)
			#mmLib_Log.logForce("Got an Indigo Complete, but device is not ours getQDevTop = " + str(theDev) + " DevAddr = " + str(devAddress))
			return 0

		#if theDev.debugDevice: mmLib_Log.logForce( "CommandComplete at Plugin for " + theDev.deviceName + ".")

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
	#	It converts the notification to an mmEvent of type 'AttributeUpdate' and dispatches it through mmLib_Events.distributeEvents()
	#
	#	For an mmObject to receive these events the object must call the following function at initialization time:
	#  		def subscribeToEvents(['AttributeUpdate'], ['Indigo'], theHandler, { handlerDefinedData - whatever static data you want delivered at time of event }, mmDevName):
	#	The event will be delivered as:
	#		theHandler('DevRcvCmd', {'AttributeUpdate', 'Indigo', Time of Event (seconds), Plus "handlerDefinedData", cmd (from Indigo)  })
	#
	#########################################
	def deviceUpdated(self, origDev, newDev):
		global pluginInitialized

		if pluginInitialized == 0: return()

		try:
			mmDev = mmLib_Low.MotionMapDeviceDict[newDev.name]
		except:
			return 0

		#if mmDev.debugDevice: mmLib_Log.logForce( mmDev.deviceName + " deviceUpdated at Plugin.py with newDev: " + str(newDev))

		# Update the indigo device in case it changed out behind our back (this just copies the reference to the device)
		# If we want to test to see if this really ever happens, we can uncomment the following block

		# if mmDev.theIndigoDevice != newDev:
			# Just a test to see if this ever happens... I dont think it does
		#	mmLib_Log.logForce("theIndigoDevice has changed for " + str(mmDev.deviceName))

		# I dont think device pointers ever change behind our back, but since it is just a pointer update.
		# It doesnt hurt much to be sure...
		mmDev.theIndigoDevice = newDev

		mmLib_Events.deliverFilteredEvents(origDev, newDev, newDev.name)

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

		previousDaylightValue = "n/a"

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

					# process Daytime/Nighttime Trsansitions

					if previousDaylightValue != newDaylightValue:
						mmLib_Log.logDebug("Change in Daylight indigo.variables[\'MMDayTime\'] value. previousDaylightValue and newDaylightValue are " + str(previousDaylightValue) + " and " + str(newDaylightValue))
						previousDaylightValue = newDaylightValue
						if newDaylightValue == 'true':
							theEvent = 'isDayTime'
						else:
							theEvent = 'isNightTime'

						mmLib_Events.distributeEvents('MMSys', [theEvent], 0, {})

		#		except self.StopThread:
		except self.StopThread:
			# do any cleanup here
			#self.shutdown()
			pass

		except:
			mmLib_Log.mmDebugError("Exception in RunConcurrent Thread. Exiting MM")
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
		# indigo makes their dict, it cant convert an object... you get an error like this:
		#   Error: No registered converter was able to produce a C + + rvalue of type CCString from this Python object of type mmScene

		try:
			for key, value in pluginAction.props.iteritems():
				# GB Fix me We have to do a unicode test here because right now, we only support regular Str. When we go to Python 3 we will not need this code
				if isinstance(value, unicode):
					theCommandParameters[key] = str(value)
				else:
					theCommandParameters[key] = value
		except:
			mmLib_Log.logForce("executeMMCommand cannot copy commandParameters. Aborting.")
			return(0)

		doCommand = theCommandParameters.get('theCommand', 0)

		if not doCommand:
			mmLib_Log.logForce("No command given in executeMMCommand")
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

			theDeviceName = theCommandParameters.get('theDevice', None)
			if theDeviceName != None:
				theDevice = mmLib_Low.MotionMapDeviceDict.get(theDeviceName,None)
				if theDevice == None:
					mmLib_Log.logForce("Couldnt find device named: " + theDeviceName )
					#mmLib_Log.logWarning("Couldnt find device named: " + theDeviceName + " \r" + str(mmLib_Low.MotionMapDeviceDict) )
					return(0)

				# check to see if it should be queued or executed
				#theMode = "QUEUE"
				#if "theMode" in theCommandParameters: theMode = theCommandParameters['theMode']
				theMode = theCommandParameters.get('theMode', "QUEUE")

				if theMode == "IMMED":
					return(theDevice.dispatchCommand(theCommandParameters))	# do the command now
				else:
					return(theDevice.queueCommand(theCommandParameters))	# queue it for later
			else:
				mmLib_Log.logForce("executeMMCommand: No device Name given for " + str(doCommand))

	############################################################################################
	# mmCommandTrigger
	#
	############################################################################################
	def mmCommandTrigger(self, pluginAction):

		theCommandParameters = {}


		# for some reason, if you just do theCommandParameters = pluginAction.props, you cant set anything in the
		# dict to an object pointer, so we have to make a copy of the parameters one by one. It must be the way
		# indigo makes their dict, it cant convert an object... you get an error like this:
		#   Error: No registered converter was able to produce a C + + rvalue of type CCString from this Python object of type mmScene

		try:
			for key, value in pluginAction.props.iteritems():
				theCommandParameters[key] = value
		except:
			mmLib_Log.logForce("mmCommandTrigger cannot copy commandParameters. Aborting.")
			return(0)

		mmLib_Log.logForce("Entering mmCommandTrigger")
		cmdBytes = theCommandParameters.get('cmdBytes', None)
		if cmdBytes != None:
			theDeviceName = theCommandParameters.get('theDevice', None)
			if theDeviceName != None:
				theDevice = mmLib_Low.MotionMapDeviceDict.get(theDeviceName,None)
				if theDevice != None:
					cmd = mmLib_Low.anIndigoCmd(theDevice.devIndigoAddress, cmdBytes)
					self.insteonCommandReceived(cmd)
				else:
					mmLib_Log.logForce("Error: Device " + theDeviceName + " not registered in MM during mmCommandTrigger")
			else:
				mmLib_Log.logForce("Error: Unknown Device given for mmCommandTrigger")

		else:
			mmLib_Log.logForce( "Error: No cmd given for mmCommandTrigger")

		return (1)


	############################################################################################
	# mmUpdateTrigger
	#
	############################################################################################
	def mmUpdateTrigger(self, pluginAction):

		mmLib_Log.logForce("Entering mmUpdateTrigger")

		theCommandParameters = {}


		# for some reason, if you just do theCommandParameters = pluginAction.props, you cant set anything in the
		# dict to an object pointer, so we have to make a copy of the parameters one by one. It must be the way
		# indigo makes their dict, it cant convert an object... you get an error like this:
		#   Error: No registered converter was able to produce a C + + rvalue of type CCString from this Python object of type mmScene

		try:
			for key, value in pluginAction.props.iteritems():
				theCommandParameters[key] = value
		except:
			mmLib_Log.logForce("mmUpdateTrigger cannot copy commandParameters. Aborting.")
			return(0)

		origDevDict = theCommandParameters.get('origDev', None)
		newDevDict = theCommandParameters.get('newDev', None)
		origDev = mmLib_Low.anIndigoDev(0, 0)
		newDev = mmLib_Low.anIndigoDev(0, 0)

		# use setAttr to make Object for origDev and newDev

		if origDevDict == None:
			mmLib_Log.logForce("Warning: Calling mmUpdateTrigger with no origDev")
		else:
			for key, value in origDevDict.iteritems():
				setattr(origDev, key, value)

		if newDevDict == None:
			mmLib_Log.logForce("Warning: Calling mmUpdateTrigger with no newDev")
		else:
			for key, value in newDevDict.iteritems():
				setattr(newDev, key, value)

		if newDev.name != None:
			theDevice = mmLib_Low.MotionMapDeviceDict.get(newDev.name,None)
			if theDevice != None:
				mmLib_Log.logForce("Calling deliverFilteredEvents to " + newDev.name + " with value of " + str(newDev.onState))
				mmLib_Events.deliverFilteredEvents(origDev, newDev, newDev.name)
			else:
				mmLib_Log.logForce("Error: Device " + newDev.name + " not registered in MM during mmUpdateTrigger")
		else:
			mmLib_Log.logForce("Error: No \'name\' given in newDev for mmUpdateTrigger")


		return (1)



