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
kInsteonEnableDisableMotionLED = 32
kInsteonBeep = 48
kInsteonBrightenWithRamp = 46
kInsteonRequestBattLevel = 46	# WARNING SAME CODE USED by Indigo/Insteon. However, we cant confuse kInsteonBrightenWithRamp and kInsteonRequestBattLevel processing command response because we rely on the fact that Brighten only works on Dimmers and Battery is only issued to Motion Sensors
kInsteonBrightenWithRamp2 = 52
kInsteonHVACMode = 107
kInsteonHVACCoolSetpoint = 108
kInsteonHVACHeatSetpoint = 109


mapCmdFuncToInsteon = {	'cool setpoint changed': kInsteonHVACCoolSetpoint,
						'heat setpoint changed': kInsteonHVACHeatSetpoint}

mapCommandToInsteon = {	'setHVACMode': [kInsteonHVACMode],
						'setHVACFanMode': [kInsteonHVACMode],
						'setHVACHeatSetpoint': [kInsteonHVACHeatSetpoint],
						'setHVACCoolSetpoint': [kInsteonHVACCoolSetpoint],
						'brighten': [kInsteonOn,kInsteonOff,kInsteonBrightenWithRamp,kInsteonBrightenWithRamp2,kInsteonStartBrightDim,kInsteonStopBrightDim,kInsteonIncreaseBrightness,kInsteonDecreaseBrightness],
						'onOffDevice': [kInsteonOn,kInsteonOff],
						'sceneOn': [kInsteonOn],
						'sceneOff': [kInsteonOff],
						'beep': [kInsteonBeep],
						'toggle': [kInsteonOff,kInsteonOn],
						'flash': [kInsteonOff,kInsteonOn],
						'check': [],
						'sendRawInsteonCommand': [kInsteonEnableDisableMotionLED, kInsteonBrightenWithRamp,kInsteonBrightenWithRamp2,kInsteonStartBrightDim,kInsteonStopBrightDim,kInsteonIncreaseBrightness,kInsteonDecreaseBrightness],
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
					   kInsteonBeep:['beep'], \
					   kInsteonBrightenWithRamp:['brighten'],\
					   kInsteonBrightenWithRamp2:['brighten'],\
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

			self.supportedCommandsDict.update({'sendRawInsteonCommand': self.sendRawInsteonCommand, 'brighten': self.brightenDevice, 'beep': self.beepDevice,  'toggle': self.toggleDevice, 'flash': self.flashDevice, 'sendStatusRequest':self.sendStatusRequest, 'devStatus':self.devStatus})



	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################


	#
	# deviceUpdatedEvent -
	#
	#
	def deviceUpdatedEvent(self, eventID, eventParameters):
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " deviceUpdatedEvent.")
		super(mmInsteon, self).deviceUpdatedEvent(eventID, eventParameters)	# Do universal housekeeping

		return (0)

	#
	# completeCommandEvent - we received a commandSent completion message from the server for this device.
	#
	def completeCommandEvent(self, eventID, eventParameters):

		theInsteonCommand = eventParameters['cmd']
		theCommandByte = self.parseInsteonCommandByte(theInsteonCommand )
		if self.debugDevice:
			#mmLib_Log.logForce(self.deviceName + " Command Complete. Byte:" + str(theCommandByte) + " InsteonCommand:" + str(theInsteonCommand))
			mmLib_Log.logForce(self.deviceName + " Command Complete. Byte:" + str(theCommandByte))
		else:
			mmLib_Log.logVerbose(self.deviceName + " Command Complete. Byte:" + str(theCommandByte))

		if theCommandByte:
			return(self.completeCommandByte(theCommandByte))
		else:
			return(0)

	#
	# receivedCommandEvent - we received a command from our device. This will take priority over anything in our queue. Flush the queue
	#                   A light switch for example may pass us an on or off command. The user clicked it, so that should take priority over anything we are doing
	#
	def receivedCommandEvent(self, eventID, eventParameters):
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " receivedCommandEvent.")

		theInsteonCommand = eventParameters['cmd']

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
	# errorCommandEvent - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	def errorCommandEvent(self, eventID, eventParameters):

		theInsteonCommand = eventParameters['cmd']

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
	#	cmd = indigo command specific
	#
	def sendRawInsteonCommand(self, theCommandParameters):

		if self.debugDevice: mmLib_Log.logForce("sendRawInsteonCommand. Sending New Raw command to " + self.deviceName + " command: " + str(theCommandParameters))

		try:
			cmd = theCommandParameters['cmd']
		except:
			mmLib_Log.logForce("### Sending Raw command to " + self.deviceName + ".... no cmd parameter found. Aborting command: " + str(theCommandParameters))
			return(0)

		try:
			ackWait = int(theCommandParameters["ackWait"])
		except:
			ackWait = False

		if len(cmd) > 2:
			extended = True
			try:
				waitForExtendedReply = int(theCommandParameters["waitForExtendedReply"])
			except:
				waitForExtendedReply = False
		else:
			extended = False
			waitForExtendedReply = False

		resultCode = self.sendRawInsteonCommandLow( cmd, ackWait, extended, waitForExtendedReply)
		if resultCode and resultCode != 'Dque':
			mmLib_Log.logForce("### While sending Raw Command " + str(theCommandParameters) + " to " + self.deviceName + " received result of " + str(resultCode))

			if not ackWait: resultCode = 0 	# GB Fix Me and Verify Its probably still in process... Clear "in process" result so it doesnt get dequeued.

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

		if self.ourNonvolatileData["unresponsive"]:
			mmLib_Log.logForce(theCommandParameters['theCommand'] + " command has been skipped. The device is offline: " + self.deviceName)
			return('unresponsive')

		if self.theIndigoDevice.version >= 0x38:
			resultCode = self.sendRawInsteonCommandLow([kInsteonBeep,0], False, False, False)
		else:
			mmLib_Log.logWarning("Beep Requested on Device that doesnt support it: " + self.deviceName)

		return(resultCode)

	#
	#  Sends a Status Request
	#		Does not honor the unresponsive variable
	#
	def sendStatusRequest(self, theCommandParameters):

		if self.StatusType == 'Sync':
			mmLib_Log.logVerbose("Requesting Synchronous Status for " + self.deviceName)
			indigo.device.statusRequest(self.theIndigoDevice)
		elif self.StatusType == 'Async':
			mmLib_Log.logVerbose("Requesting Async Status for " + self.deviceName)
			indigo.insteon.sendStatusRequest(self.theIndigoDevice.address, waitUntilAck=False)
		else:
			# Status is OFF
			mmLib_Log.logVerbose("Status is not supported for " + self.deviceName)
		return('Dque')	# We are done, tell dispatch to deque


	############################################################################################
	#
	# sendRawInsteonCommandLow
	#
	############################################################################################

	def sendRawInsteonCommandLow(self, theCommand, ackWait, extendedCommand, ExtendedWaitReply):

		resultCode = 0

		#if self.debugDevice: mmLib_Log.logForce("sendRawInsteonCommandLow. Sending Raw command to " + self.deviceName + " command: " + str(theCommand))

		if extendedCommand:
			resultRecord = indigo.insteon.sendRawExtended(self.theIndigoDevice.address, theCommand, waitUntilAck=ackWait, waitForExtendedReply=ExtendedWaitReply)
		else:
			resultRecord = indigo.insteon.sendRaw(self.theIndigoDevice.address, theCommand, waitUntilAck=ackWait)


		if resultRecord:
			if self.debugDevice: mmLib_Log.logForce("### sendRawInsteonCommandLow. While sending Raw Command " + str(theCommand) + " to " + self.deviceName + " received result record of\n" + str(resultRecord))

			if ackWait == False:
				try:
					if resultRecord.cmdSuccess == True: resultCode = 0	# Its already finished. The completion proc was already called and the command dequeued
				except:
					mmLib_Log.logForce("sendRawInsteonCommandLow. Error reading Raw command result code from " + self.deviceName + ".")

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
		mmLib_Log.logWarning("deviceMotionStatus called for " + self.deviceName + ". Function not supported. It must be overridden.")

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
		except:
			mmLib_Log.logWarning("Command Error. The insteon command: " + str(theCommandByte) + " Does not have a potential command list.")
			potentialCommandList = []

		for theCommand in potentialCommandList:
			if mmLib_CommandQ.flushQ(self, {'theDevice':self.deviceName,'theIndigoDeviceID':self.devIndigoID, 'theCommand':theCommand}, ["theCommand"]):
				mmLib_Log.logForce("=== Waiting comands flushed due to user interaction with: " + self.deviceName)

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
		else:
			#mmLog.logError( "checkForOurInsteonCommand called with no cmdBytes \n" + str(theInsteonCommand))
			if theInsteonCommand.cmdFunc == 'on':
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " No cmdBytes found, Substituting ON command.")
				theCommand = kInsteonOn
			elif theInsteonCommand.cmdFunc == 'off':
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Substituting OFF command.")
				theCommand = kInsteonOff
			else:
				mmLib_Log.logForce(self.deviceName + " Unknown command, returning Zero. Command found was " + str(theInsteonCommand.cmdFunc))
				return(0)

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Processing command completion. Found command byte " + str(theCommand))

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

