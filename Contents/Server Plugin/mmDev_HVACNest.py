
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
	def deviceUpdated(self, origDev, newDev):

		extraMessage = ""

		if origDev.hvacMode != newDev.hvacMode:
			extraMessage = extraMessage + " HVAC Mode was " + str(origDev.hvacMode) + " is now:" + str(newDev.hvacMode) + "."

		if origDev.fanMode != newDev.fanMode:
			extraMessage = extraMessage + " Fan Mode was " + str(origDev.fanMode) + " is now:" + str(newDev.fanMode) + "."

		if origDev.coolSetpoint != newDev.coolSetpoint:
			extraMessage = extraMessage + " Cool Setpoint was " + str(origDev.coolSetpoint) + " is now:" + str(newDev.coolSetpoint) + "."

		if origDev.coolIsOn != newDev.coolIsOn:
			if newDev.coolIsOn == True:
				extraMessage = extraMessage + " Cooling has become on."
			else:
				extraMessage = extraMessage + " Cooling has become off."

		if origDev.heatSetpoint != newDev.heatSetpoint:
			extraMessage = extraMessage + " Heat Setpoint was " + str(origDev.heatSetpoint) + " is now:" + str(newDev.heatSetpoint) + "."

		if origDev.heatIsOn != newDev.heatIsOn:
			if newDev.heatIsOn == True:
				extraMessage = extraMessage + " Heating has become on."
			else:
				extraMessage = extraMessage + " Heating has become off."

		if extraMessage != "":
			mmLib_Log.logForce("HVAC Nest Device \"" + self.deviceName + "\" has been Updated:" + extraMessage)
			super(mmHVACNest, self).deviceUpdated(origDev, newDev)  # Report up the food chain

	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	#def completeCommand(self, theInsteonCommand ):
	#	super(mmHVACNest, self).completeCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# receivedCommand
	#
	def receivedCommand(self, theInsteonCommand ):

		mmLib_Log.logForce("Received command from HVAC Nest Device \"" + self.deviceName + "\".")
		super(mmHVACNest, self).receivedCommand(theInsteonCommand)  # Normal Base Class operation



	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	#def errorCommand(self, theInsteonCommand ):
	#	super(mmHVACNest, self).errorCommand(theInsteonCommand)	# Nothing special here, forward to the Base class




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


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			if len(str(diff)) > 1:
				mmLib_Log.logForce("Parsing Update for mmHVACNest: Length " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmHVACNest: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmHVACNest: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process




