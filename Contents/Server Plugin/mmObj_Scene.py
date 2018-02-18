

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
import mmComm_Insteon
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections

######################################################
#
# mmScene - Virtual Device used for Scene commands
#
######################################################
class mmScene(mmComm_Insteon.mmInsteon):


	def __init__(self, theDeviceParameters):
		super(mmScene, self).__init__(theDeviceParameters)

		if self.initResult == 0:

			#
			# Set object variables
			#

			self.sceneNumber = int(theDeviceParameters["sceneNumber"])
			self.devIndigoAddress = mmLib_Low.makeSceneAddress(self.sceneNumber)
			mmLib_Log.logVerbose("Initializing Scene " + str(self.sceneNumber) + ": " + self.deviceName + ", " + self.devIndigoAddress + ", " + self.devIndigoID)
			self.members = theDeviceParameters["members"].split(';')  # Can be a list, split by semicolons... normalize it into a proper list
			self.expectedOnState = False

			self.testDevAddress = self.devIndigoAddress

			self.supportedCommandsDict.update({'sceneOn': self.sendSceneOn, 'sceneOff': self.sendSceneOff, 'devStatus':self.devStatus})

			del self.supportedCommandsDict['sendStatusRequest']


	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	# 	All commands in this section must have a single parameter theCommandParameters - a list of parameters
	# 	And all commands must be registered in self.supportedCommandsDict variable
	#
	######################################################################################

	#
	# devStatus - Print Status information for this device to the log
	#
	def	devStatus(self,theCommandParameters):
		mmLib_Log.logForce("sceneDevice status." + self.deviceName + " has no status handler routine.")

	#
	#  Send a Scene Off Request
	#
	def sendSceneOff(self, theCommandParameters):

		# force scene commands to happen twice (they frequently dont complete on the first pass)
		try:
			nTimes = theCommandParameters['repeat']
		except:
			theCommandParameters['repeat'] = 1

		indigo.insteon.sendSceneOff(self.sceneNumber, sendCleanUps=False)	# does not honor unresponsive because this is not really a device
		self.expectedOnState = False

		return(0)

	#
	#  Send a Scene On Request
	#
	def sendSceneOn(self, theCommandParameters):

		mmLib_Log.logVerbose("Issuing SceneOn " + self.deviceName)
		# force scene commands to happen twice (they frequently dont complete on the first pass)
		try:
			nTimes = theCommandParameters['repeat']
		except:
			theCommandParameters['repeat'] = 1

		indigo.insteon.sendSceneOn(self.sceneNumber, sendCleanUps=False) # does not honor unresponsive because this isnt really a device
		self.expectedOnState = True

		return(0)

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################



	#
	#  Verify completion of a Scene Request
	#
	def verifyScene(self):

		verificationCommandsSent = 0

		for theMember in self.members:
			# if the expected ON state is not correct, enqueue a command to fix it
			try:
				mmMemberDev = mmLib_Low.MotionMapDeviceDict[theMember]
				if mmMemberDev.theIndigoDevice.onState != self.expectedOnState:
					mmLib_Log.logForce("While processing Scene " + self.deviceName + ", a Device didnt change: " + theMember)
					mmMemberDev.queueCommand({'theCommand':'onOffDevice', 'theDevice':theMember, 'theValue':self.expectedOnState, 'retry':2})
					verificationCommandsSent = verificationCommandsSent + 1
			except:
				mmLib_Log.logWarning("Scene " + self.deviceName + " references member that does not exist: " + theMember)

		if verificationCommandsSent == 0:
			mmLib_Log.logForce("No verifications were needed for Scene " + self.deviceName)

		return(0)

	def parseCompletion(self, theInsteonCommand):
		#self.verifyScene()	# we can reactivate this in completeCommand, but we should first fix verifyScene to not do on/off command for devices that dont handle it
		return 0	#0 means did not process completion message... default handler will take care of it
