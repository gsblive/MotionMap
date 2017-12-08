
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
import mmLogic_HVAC

######################################################
#
# mmHVACInsteon - Thermostat
#
#	HVAC Overrides For Insteon thermostats only
#
######################################################
class mmHVACInsteon(mmLogic_HVAC.mmHVAC):


	def __init__(self, theDeviceParameters):
		mmLib_Log.logVerbose( "mmHVACInsteon Initialization. ")

		super(mmHVACInsteon, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			self.onControllers = theDeviceParameters["onControllers"].split(';')  # Can be a list, split by semicolons... normalize it into a proper list
			self.sustainControllers = theDeviceParameters["sustainControllers"].split(';')  # Can be a list, split by semicolons... normalize it into a proper list
			self.combinedControllers = filter(None, theDeviceParameters["onControllers"].split(';') + theDeviceParameters["sustainControllers"].split(';'))
			self.updateFrequency = int(theDeviceParameters["updateFrequency"])
			self.maxTempDelta = int(theDeviceParameters["fanOnThreshold"])
			self.operationalMode = theDeviceParameters["operationalMode"]




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
	#	super(mmHVACInsteon, self).deviceUpdated(origDev, newDev)	# Nothing special here, forward to the Base class

	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	#def completeCommand(self, theInsteonCommand ):
	#	super(mmHVACInsteon, self).completeCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# receivedCommand - we received a command from our device.
	#
	#def receivedCommand(self, theInsteonCommand ):
	#	super(mmHVACInsteon, self).receivedCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	#def errorCommand(self, theInsteonCommand ):
	#	super(mmHVACInsteon, self).errorCommand(theInsteonCommand)	# Nothing special here, forward to the Base class



	######################################################################################
	#
	# MM Entry Points
	#
	######################################################################################


	#
	# updateThermostatSetingsLogic
	#
	def updateThermostatSetingsLogic(self):
		super(mmHVACInsteon, self).updateThermostatSetingsLogic()  # the base class just keeps track of the time since last change



	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'),unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmHVACInsteon: " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmHVACInsteon: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmHVACInsteon: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process
