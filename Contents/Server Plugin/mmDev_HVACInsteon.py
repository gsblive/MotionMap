
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
import mmLib_Events
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


