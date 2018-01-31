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
import mmComm_Indigo
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections



kInsteonOn = 17
kInsteonOnFast = 18
kInsteonOff = 19
kInsteonOffFast = 20
kInsteonIncreaseBrightness = 21
kInsteonDecreaseBrightness = 22
kInsteonStartBrightDim = 23
kInsteonStopBrightDim = 24
kInsteonStatusRequest = 25
kInsteonBeep = 48
kInsteonHVACMode = 107
kInsteonHVACCoolSetpoint = 108
kInsteonHVACHeatSetpoint = 109


mapCmdFuncToInsteon = {	'cool setpoint changed': kInsteonHVACCoolSetpoint,
						'heat setpoint changed': kInsteonHVACHeatSetpoint}

mapCommandToInsteon = {	'setHVACMode': [kInsteonHVACMode],
						'setHVACFanMode': [kInsteonHVACMode],
						'setHVACHeatSetpoint': [kInsteonHVACHeatSetpoint],
						'setHVACCoolSetpoint': [kInsteonHVACCoolSetpoint],
						'brighten': [kInsteonOn,kInsteonOff],
						'onOffDevice': [kInsteonOn,kInsteonOff],
						'sceneOn': [kInsteonOn],
						'sceneOff': [kInsteonOff],
						'beep': [kInsteonBeep],
						'toggle': [kInsteonOff,kInsteonOn],
						'flash': [kInsteonOff,kInsteonOn],
						'check': [],
						'sendStatusRequest': [kInsteonStatusRequest] }

mapInsteonToCommand = {kInsteonOn:['brighten','toggle', 'flash', 'onOffDevice','sceneOn'],\
					   kInsteonOnFast:['brighten','toggle', 'flash', 'onOffDevice'],\
					   kInsteonOff:['brighten','toggle', 'flash', 'onOffDevice','sceneOff'],\
					   kInsteonOffFast:['brighten','toggle', 'flash', 'onOffDevice'],\
					   kInsteonIncreaseBrightness:['brighten','toggle', 'flash'],\
					   kInsteonDecreaseBrightness:['brighten','toggle', 'flash'],\
					   kInsteonStartBrightDim:['brighten','toggle', 'flash'],\
					   kInsteonStopBrightDim:['brighten','toggle', 'flash'],\
					   kInsteonStatusRequest:['sendStatusRequest'],\
					   kInsteonBeep:['beep'],\
					   kInsteonHVACMode:['setHVACFanMode', 'setHVACMode'],\
					   kInsteonHVACCoolSetpoint:['setHVACHeatSetpoint'],\
					   kInsteonHVACHeatSetpoint:['setHVACCoolSetpoint']}




######################################################
#
# mmInsteon - Insteon Device Class
#
#            Default Behaviors for all Insteon Devices
#
#
######################################################
class mmInsteon(mmComm_Indigo.mmIndigo):
	def __init__(self, theDeviceParameters):
		#
		# Set object variables
		#

		# Initialize Root Class
		super(mmInsteon, self).__init__(theDeviceParameters)
		if self.initResult == 0:
			mmLib_Log.logDebug("Continuing initialization of " + self.deviceName)

			self.updateTimeStamp = 0		#time.clock()		# fresh start... assume updated
			self.defeatTimerUpdate = 0

			# For Offline report

			self.errorCounter = 0
			self.timeoutCounter = 0
			self.sequentialErrors = 0
			self.unresponsive = 0
			self.highestSequentialErrors = 0

			try:
				self.maxSequentialErrors = int(theDeviceParameters["maxSequentialErrorsAllowed"])
			except:
				self.maxSequentialErrors = mmLib_Low.MAX_SEQUENTIAL_ERRORS_DEFAULT

			self.supportedCommandsDict.update({'sendRawInsteonCommand': self.sendRawInsteonCommand, 'brighten': self.brightenDevice, 'beep': self.beepDevice,  'toggle': self.toggleDevice, 'flash': self.flashDevice, 'sendStatusRequest':self.sendStatusRequest, 'devStatus':self.devStatus})



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
	#def deviceUpdated(self, origDev, newDev):
	#
	#	super(mmInsteon, self).deviceUpdated(origDev, newDev)	# Nothing special here, forward to the Base class



	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	def completeCommand(self, theInsteonCommand ):

		theCommandByte = self.parseInsteonCommandByte(theInsteonCommand )
		mmLib_Log.logVerbose(self.deviceName + " Command Complete." + str(theCommandByte))
		if theCommandByte:
			return(self.completeCommandByte(theCommandByte))
		else:
			return(0)

	#
	# receivedCommand - we received a command from our device. This will take priority over anything in our queue. Flush the queue
	#                   A light switch for example may pass us an on or off command. The user clicked it, so that should take priority over anything we are doing
	#
	def receivedCommand(self, theInsteonCommand ):

		if mmLib_CommandQ.pendingCommands:
			#mmLog.logWarning( "Issuing flushQ command for " + self.deviceName + ", because manual device change. The insteon command: " + str(theInsteonCommand.cmdBytes) + " " + str(theInsteonCommand.cmdFunc))

			try:
				theCommandByte = int(theInsteonCommand.cmdBytes[0])
			except:
				mmLib_Log.logForce("Command byte for " + self.deviceName + " not present.")
				try:
					mmLib_Log.logForce("  Attempting mapping via cmdFunc \'" + str(theInsteonCommand.cmdFunc) + "\' in " + str(mapCmdFuncToInsteon) + ".")
					theCommandByte = int(mapCmdFuncToInsteon[str(theInsteonCommand.cmdFunc)])
				except:
					theCommandByte = 0

			if theCommandByte:
				self.receivedCommandByte(theCommandByte )
			else:
				mmLib_Log.logForce("No Valid Command byte found for " + self.deviceName + " for command " + str(theCommandByte) + " in insteon command \n" + str(theInsteonCommand))

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	def errorCommand(self, theInsteonCommand ):
		#mmLog.logForce( str(theInsteonCommand.cmdBytes) + " " + str(theInsteonCommand.cmdFunc))

		if self.checkForOurInsteonCommand( theInsteonCommand ):
			theCommandParameters = mmLib_CommandQ.pendingCommands[0]
			self.errorCommandLow(theCommandParameters, 'Error' )
		else:
			# someone else sent a similar command while our commands were waiting, delete all of our commands (defer to other process)
			mmLib_Log.logForce("received an error on command to " + self.deviceName + ", but it wasnt our command. The insteon command was: " + str(theInsteonCommand.cmdBytes) + " " + str(theInsteonCommand.cmdFunc))
			self.errorCommandLow(0, 'Error' )	# call commandlow to count the error (for offline processing)

		return(0)


	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	# sendRawInsteonCommand
	#	ackWait = 1 if Indigo should wait for an Ack
	#	cmd1, cmd2 = [cmd1,cmd2] indigo command specific
	#
	def sendRawInsteonCommand(self, theCommandParameters):

		mmLib_Log.logDebug("Sending Raw command to " + self.deviceName + " command: " + str(theCommandParameters))

		try:
			extended = int(theCommandParameters["extended"])
			extended = True
		except:
			extended = False

		try:
			ackWait = int(theCommandParameters["ackWait"])
			ackWait = True
		except:
			ackWait = False

		if extended:
			try:
				theCommand = [0,0,0,0,0]
				theCommand[0] = int(theCommandParameters["cmd1"])
				theCommand[1] = int(theCommandParameters["cmd2"])
				theCommand[2] = int(theCommandParameters["cmd3"])
				theCommand[3] = int(theCommandParameters["cmd4"])
				theCommand[4] = int(theCommandParameters["cmd5"])
			except:
				mmLib_Log.logForce("While sending Extended Raw command to " + self.deviceName + "... Parameter Error (extended cmds not found). command: " + str(theCommandParameters))
				return(0)
		else:
			try:
				theCommand = [0,0]
				theCommand[0] = int(theCommandParameters["cmd1"])
				theCommand[1] = int(theCommandParameters["cmd2"])
			except:
				mmLib_Log.logForce("While sending Raw command to " + self.deviceName + "... Parameter Error. command: " + str(theCommandParameters))
				return(0)

		resultCode = self.sendRawInsteonCommandLow( theCommand, ackWait, extended)

		return(resultCode)



	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################

	#
	#  beepDevice - Beep the Device
	#
	def beepDevice(self, theCommandParameters):

		resultCode = 0

		if self.unresponsive:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return('unresponsive')

		if self.theIndigoDevice.version >= 0x38:
			resultCode = self.sendRawInsteonCommandLow([kInsteonBeep,0], False, False)
		else:
			mmLib_Log.logWarning("Beep Requested on Device that doesnt support it: " + self.deviceName)

		return(resultCode)

	#
	#  Sends a Status Request
	#		Does not honor the unresponsive variable
	#
	def sendStatusRequest(self, theCommandParameters):
		mmLib_Log.logVerbose("Requesting Status for " + self.deviceName)
		#indigo.iodevice.statusRequest(self.theIndigoDevice.id)
		indigo.insteon.sendStatusRequest(self.theIndigoDevice.address,waitUntilAck=False)

		return(0)


	############################################################################################
	#
	# sendRawInsteonCommandLow
	#
	############################################################################################

	def sendRawInsteonCommandLow(self, theCommand, ackWait, extendedCommand):

		resultCode = 0

		mmLib_Log.logDebug("Sending Raw command to " + self.theIndigoDevice.name + " command: " + str(theCommand))

		if extendedCommand:
			resultCode = indigo.insteon.sendRawExtended(self.theIndigoDevice.address, theCommand, waitUntilAck=ackWait)
		else:
			resultCode = indigo.insteon.sendRaw(self.theIndigoDevice.address, theCommand, waitUntilAck=ackWait)

		if resultCode:
			try:
				if resultCode.cmdSuccess == True: resultCode = 0
			except:
				mmLib_Log.logForce("Sending Raw command to " + self.theIndigoDevice.name + " Received Result: " + str(resultCode) + ", *** substituting -1")

		if ackWait == False:
			if not resultCode: resultCode = 'Dque'		# we are not waiting for result... move on to the next command

		return(resultCode)


	#
	# deviceTime - do device housekeeping... this should happen once a minute. Returns the amount of seconds since last update
	#
	def deviceTime(self):
		# Insteon devices get their time here
		mmLib_Log.logForce("DeviceTime in Insteon.py for " + self.deviceName + " should be overridden.")
		return(0)

	#
	# getBrightness
	#
	def getBrightness(self):

		if self.theIndigoDevice.__class__ == indigo.DimmerDevice:
			return(self.theIndigoDevice.brightness)
		else:
			if self.theIndigoDevice.onState == True:
				return(100)
			else:
				return(0)


	#
	# deviceMotionStatus - check the motion status of a device
	#
	def deviceMotionStatus(self):

		# Handle this in the overriding objects
		return(0)


	########################################################
	############## Command and queue processing ############
	########################################################

	#
	# checkForOurCommandByte - Return a 1 of the command notification we received (theCommand) matches what we expected on top of the queue
	#
	def checkForOurCommandByte(self, theCommand ):
	
		if mmLib_CommandQ.pendingCommands:
			qHead = mmLib_CommandQ.pendingCommands[0]

			if qHead['theIndigoDeviceID'] == self.devIndigoID:											# is our device on top of the queue?
				headCommand = qHead['theCommand']
				try:
					expectedCommandValList = mapCommandToInsteon[headCommand]
				except:
					mmLib_Log.logForce(str(theCommand) + " no insteon equivalent for " + headCommand)
					return(1)

				if theCommand not in expectedCommandValList:
					mmLib_Log.logForce(str(theCommand) + " is not the expected result for " + headCommand)
				else:
					return(1)			# yes it was our command
			else:
				mmLib_Log.logVerbose(self.deviceName + " received \"" + str(theCommand) + "\" command result but the command did not initiate from MotionMap.")
		else:
			mmLib_Log.logForce(self.deviceName + " received \"" + str(theCommand) + "\" command result but the command queue was empty.")

		return(0)


	#
	# receivedCommandByte - we received a command from our device. This will take priority over anything in our queue. Flush the queue
	#                   A light switch for example may pass us an on or off command. The user clicked it, so that should take priority over anything we are doing
	#
	def receivedCommandByte(self, theCommandByte ):

		try:
			potentialCommandList = mapInsteonToCommand[theCommandByte]
			for theCommand in potentialCommandList:
				if mmLib_CommandQ.flushQ(self, {'theIndigoDeviceID':self.devIndigoID, 'theCommand':theCommand}, ["theCommand"]):
					mmLib_Log.logForce("=== Waiting comands flushed due to user interaction with: " + self.deviceName)
		except:
			mmLib_Log.logWarning("Command Error. The insteon command: " + str(theCommandByte))

		# Now that we processed all the waiting commands, if we are the active queued command, the new incomming command received probably sabatoged
		# our efforts to send anything, so restart the queue
		if mmLib_CommandQ.pendingCommands[0]['theIndigoDeviceID'] == self.devIndigoID:											# is our device on top of the queue?
			mmLib_Log.logVerbose("Forcing command Completion and restarting the queue. The insteon command: " + str(theCommandByte))
			mmLib_CommandQ.dequeQ(1) 														# no matter what command it is... with pop


	#
	# parseInsteonCommandByte - Return an insteon command number, or 0 if no command exists
	#
	def parseInsteonCommandByte(self, theInsteonCommand ):

		if theInsteonCommand.cmdBytes:
			theCommand = int(theInsteonCommand.cmdBytes[0])
			if theCommand == kInsteonBeep:
				mmLib_Log.logVerbose(self.deviceName + " received a completion (or error) on beep command, they are always async so we\'re ignoring it.")
				return(0)
		else:
			#mmLog.logError( "checkForOurInsteonCommand called with no cmdBytes \n" + str(theInsteonCommand))
			if theInsteonCommand.cmdFunc == 'on':
				mmLib_Log.logForce(self.deviceName + " No cmdBytes found, Substituting ON command.")
				theCommand = kInsteonOn
			elif theInsteonCommand.cmdFunc == 'off':
				mmLib_Log.logForce(self.deviceName + " Substituting OFF command.")
				theCommand = kInsteonOff
			else:
				mmLib_Log.logForce(self.deviceName + " Unknown command, returning Zero")
				return(0)

		return(int(theCommand))

	#
	# checkForOurInsteonCommand - Return a 1 of the command notification we received (theInsteonCommand) matches what we expected on top of the queue
	#
	def checkForOurInsteonCommand(self, theInsteonCommand ):

		theCommandByte = self.parseInsteonCommandByte(theInsteonCommand )
		if theCommandByte:
			return(self.checkForOurCommandByte(theCommandByte))
		else:
			return(0)

