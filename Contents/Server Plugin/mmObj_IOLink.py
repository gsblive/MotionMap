__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

# import json
#import os
#import traceback
from datetime import datetime

import mmLib_Log
import mmLib_Low
import mmLib_Events
import mmObj_Motion

############################################################################################
#
#	Note This MM Object is for Insteon I/O Link devices. Here, we use only the inout section , imitating motion sensors' GetOnState()
#	We simply override that function and substitute the IOLink's BinaryInput1 for now.. we may add additional functionality as needed later
#
############################################################################################


######################################################
#
# mmIOLink - SubModel of motionsensorDevice
#
######################################################
class mmIOLink(mmObj_Motion.mmMotion):

	#
	# __init__
	#
	def __init__(self, theDeviceParameters):

		# We call initLow in favor of calling super(mmIOLink, self).__init__()
		# so we can override subscribeToEvents, normally done in __init__()
		# this is all because we are monitoring different update events (self.theIndigoDevice.states["binaryInput1"] instead of self.theIndigoDevice.onState

		self.initLow(theDeviceParameters)
		if self.debugDevice: mmLib_Log.logForce( " =***= Initializing (Completed BaseClass mmMotion) " + self.deviceName)
		mmLib_Events.subscribeToEvents(['AttributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes': {'states': 0}}, self.deviceName)

	#
	# deviceUpdated
	# our indigo device was updated
	#
	def	deviceUpdatedEvent(self, eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce( " =***= deviceUpdatedEvent called for IOLink device " + self.deviceName + " with eventParameters of: " + str(eventParameters) )

		stateDict = eventParameters.get('states', 'na')
		if stateDict == 'na':
			mmLib_Log.logError("MM IOLink device " + self.deviceName + " did not retrieve dev.states record.")
			return

		newOnState = stateDict.get('binaryInput1', 'na')
		if newOnState == 'na':
			mmLib_Log.logError("MM IOLink device " + self.deviceName + " did not receive proper dev.states['newOnState'] entry.")
			return

		# Convert the States['binaryInput1'] to the appropriate onState value
		eventParameters.update({'onState':newOnState})
		super(mmIOLink, self).deviceUpdatedEvent(eventID, eventParameters)  # Call Base Class

	def getOnState(self):
		if self.onlineState != mmLib_Low.AUTOMATIC_MODE_ON: return(False)
		self.currentOnState = self.theIndigoDevice.states["binaryInput1"]
		if self.debugDevice: mmLib_Log.logForce( "  === OnState for " + self.deviceName + " is " + str(self.currentOnState))
		return(self.currentOnState)


	def receivedCommandEvent(self, eventID, eventParameters):
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " receivedCommandEvent for ioLink.")
		super(mmIOLink, self).receivedCommandEvent(eventID, eventParameters)  # Call Base Class

