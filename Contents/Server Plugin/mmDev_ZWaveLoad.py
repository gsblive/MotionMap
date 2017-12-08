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

import indigo
import mmLib_Log
import mmLib_Low
import mmLogic_Load
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
import codecs

#
# In the process of changing this to use mmObj_Occupation for basic on off timing code

######################################################
#
# mmZLoad - Load Device, usually a Dimmer or Switch (Z-Wave version)
#
# The difference with ZWave and Insteon Load devices is that ZWave does not respond
# with commandComplete messages, so you have to watch for teh update message coming in to clear the command Queue
#
######################################################
class mmZLoad(mmLogic_Load.mmLoad):

	#deviceName, maxNonMotionTime, maxOnTime, daytimeOnLevel, nighttimeOnLevel, specialFeatures, onControllers, sustainControllers, maxSequentialErrorsAllowed
	#TestPowerStrip - Outlet,1, 5, 10, 100, 100,, , , 2

	def __init__(self, theDeviceParameters):

		super(mmZLoad, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			self.supportedCommandsDict.update({'sendStatusRequest':self.sendStatusRequest})



	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################

	#
	# Parse routines, this converts the Plug-In function parameters into MM parameters
	#

	def parseUpdate(self,origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'),unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for ZLoad: " + self.deviceName + " with Value of: " + str(diff))
		return 1
	def parseCommand(self,theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for ZLoad: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 1

	#
	# deviceUpdated - tell the companions what to do
	#
	def deviceUpdated(self, origDev, newDev):

		#mmLib_Log.logForce(self.deviceName + " # update.")

		theOnstateChanged = 0
		#
		# do the special processing
		# ========================
		#mmLib_Log.logForce("Received Update for ZDevice: " + self.deviceName)
		#mmLib_Log.logForce(str(newDev))
		if newDev.onState!=origDev.onState:
			mmLib_Log.logVerbose("New onState for ZDevice: " + self.deviceName + " with Value of " + str(newDev.onState))
			theOnstateChanged = 1

		if mmLib_CommandQ.pendingCommands:
			qHead = mmLib_CommandQ.pendingCommands[0]

			if qHead['theIndigoDeviceID'] == self.devIndigoID:											# is our device on top of the queue?
				headCommand = qHead['theCommand']
				if headCommand == "sendStatusRequest":
					mmLib_Log.logVerbose("Clearing Status Request for " + self.deviceName)
					mmLib_CommandQ.dequeQ(1) 															# all is well, pop our old command off and Restart the Queue
				elif theOnstateChanged and headCommand in ["brighten", "on", "off", "flash"]:
					mmLib_Log.logVerbose("Clearing brighten command for " + self.deviceName)
					if newDev.onState == True:
						self.completeCommandByte(17)
					else:
						self.completeCommandByte(19)

					if headCommand == "flash": return(0)
		#
		# We didnt handle the event, do the normal processing
		if theOnstateChanged:
			super(mmZLoad, self).deviceUpdated(origDev, newDev)  				# execute Base Class


		return(0)
	#
	# receivedCommand - we received a command from our device. The base object will do most of the work... we want to process special commands here, like bedtime mode
	#
	def receivedCommand(self, theInsteonCommand ):

		#
		# do the special processing
		# ========================
		mmLib_Log.logForce("Received Command for ZDevice: " + self.deviceName)


		#
		# do the normal processing
		# ========================
		super(mmZLoad, self).receivedCommand(theInsteonCommand)  			# execute Base Class

		return(0)


	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	# The difference with ZWave and Insteon Load devices is that ZWave does not respond
	# with commandComplete messages, so you have to watch for teh update message coming in to clear the command Queue
	#
	def completeCommand(self, theInsteonCommand ):

		#
		# do the special processing
		# ========================
		mmLib_Log.logForce("Complete Command for ZDevice: " + self.deviceName)

		#
		# do the normal processing
		# ========================
		super(mmZLoad, self).completeCommand(theInsteonCommand)  			# execute Base Class


	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	def errorCommand(self, theInsteonCommand ):

		#
		# do the special processing
		# ========================
		mmLib_Log.logVerbose("Error Command for ZDevice: " + self.deviceName)

		#
		# do the normal processing
		# ========================
		super(mmZLoad, self).errorCommand(theInsteonCommand)  			# execute Base Class

		return(0)




	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	#  Sends a Status Request
	#		Does not honor the unresponsive variable
	#
	def sendStatusRequest(self, theCommandParameters):
		mmLib_Log.logVerbose("Requesting Status for " + self.deviceName)
		#indigo.device.statusRequest(self.devIndigoID)
		#if self.theIndigoDevice.deviceTypeId == 'zwRelayType':
		indigo.iodevice.statusRequest(self.theIndigoDevice.id)

		return(0)

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmZLoad: " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmZLoad: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmZLoad: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process
