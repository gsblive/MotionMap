
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
# mmHVACNest - Thermostat
#
#	HVAC Overrides For Nest thermostats only
#
######################################################
class mmHVACNest(mmLogic_HVAC.mmHVAC):


	def __init__(self, theDeviceParameters):

		super(mmHVACNest, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			self.supportedCommandsDict.update({'setHVACMode':self.setHVACMode, 'setHVACFanMode':self.setHVACFanMode, 'setHVACCoolSetpoint':self.setHVACCoolSetpoint, 'setHVACHeatSetpoint':self.setHVACHeatSetpoint, 'sendStatusRequest':self.sendStatusRequest})
			self.allowAsync = 0		# Nest device is always async... use standard commands
			mmLib_Log.logVerbose("HVAC Nest Device \"" + self.deviceName + "\" has been set up.")




	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################

	#
	# deviceUpdated
	#
	def deviceUpdatedEvent(self, eventID, eventParameters):

		extraMessage = ""

		if eventParameters.get('hvacMode', 'na') != 'na':
			extraMessage = extraMessage + " HVAC Mode is now:" + str(eventParameters['hvacMode']) + "."

		if eventParameters.get('fanMode', 'na') != 'na':
			extraMessage = extraMessage + " Fan Mode is now:" + str(eventParameters['fanMode']) + "."

		if eventParameters.get('coolSetpoint', 'na') != 'na':
			extraMessage = extraMessage + " Cool SetPoint is now:" + str(eventParameters['coolSetpoint']) + "."

		coolBoolean = eventParameters.get('coolIsOn', 'na')
		if coolBoolean != 'na':
			if coolBoolean:
				extraMessage = extraMessage + " Cooling has become on."
			else:
				extraMessage = extraMessage + " Cooling has become off."

		if eventParameters.get('heatSetpoint', 'na') != 'na':
			extraMessage = extraMessage + " Heat SetPoint is now:" + str(eventParameters['heatSetpoint']) + "."

		heatBoolean = eventParameters.get('heatIsOn', 'na')
		if heatBoolean != 'na':
			if heatBoolean:
				extraMessage = extraMessage + " Heating has become on."
			else:
				extraMessage = extraMessage + " Heating has become off."

		if extraMessage != "":
			mmLib_Log.logForce("HVAC Nest Device \"" + self.deviceName + "\" has been Updated:" + extraMessage)
			super(mmHVACNest, self).deviceUpdatedEvent(eventID, eventParameters)  # Report up the food chain

	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	#def completeCommand(self, theInsteonCommand ):
	#	super(mmHVACNest, self).completeCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# receivedCommand
	#
	def receivedCommandEvent(self, eventID, eventParameters ):

		mmLib_Log.logForce("Received command from HVAC Nest Device \"" + self.deviceName + "\".")
		super(mmHVACNest, self).receivedCommandEvent(eventID, eventParameters)  # Normal Base Class operation



	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################


	#
	# Set the HVAC mode as defined in theCommandParameters
	#
	def setHVACMode(self, theCommandParameters):

		resultCode = super(mmHVACNest, self).setHVACMode(theCommandParameters)  # call Base Class

		if not resultCode: resultCode = 'Dque'		# we are not waiting for result... For NEST, there will be no response (it all happens in the server)

		return(resultCode)

	#
	# Set the HVAC Fanmode as defined in theCommandParameters
	#
	def setHVACFanMode(self, theCommandParameters):
		resultCode = super(mmHVACNest, self).setHVACFanMode(theCommandParameters)  # call Base Class

		if not resultCode: resultCode = 'Dque'		# we are not waiting for result... For NEST, there will be no response (it all happens in the server)

		return(resultCode)


	#
	# Set the HVAC Cool Setpoint as defined in theCommandParameters
	#
	def setHVACCoolSetpoint(self, theCommandParameters):

		resultCode = super(mmHVACNest, self).setHVACCoolSetpoint(theCommandParameters)  # call Base Class

		if not resultCode: resultCode = 'Dque'		# we are not waiting for result... For NEST, there will be no response (it all happens in the server)

		return(resultCode)



	#
	# Set the HVAC Heat Setpoint as defined in theCommandParameters
	#
	#	Setpoint = the setpoint (must convert to int)
	def setHVACHeatSetpoint(self, theCommandParameters):
		resultCode = super(mmHVACNest, self).setHVACHeatSetpoint(theCommandParameters)  # call Base Class

		if not resultCode: resultCode = 'Dque'		# we are not waiting for result... For NEST, there will be no response (it all happens in the server)

		return(resultCode)

	#
	#  Sends a Status Request
	#		Does not honor the unresponsive variable
	#
	def sendStatusRequest(self, theCommandParameters):
		mmLib_Log.logForce(self.deviceName + " does not need StatusRequest Messages.")
		return(0)



	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################





