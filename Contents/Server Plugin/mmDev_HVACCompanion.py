

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
# HVACCompanion - Thermostat
#
######################################################
class mmHVACCompanion(mmLogic_HVAC.mmHVAC):


	def __init__(self, theDeviceParameters):

		super(mmHVACCompanion, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			self.supportedCommandsDict = {'sendRawInsteonCommand': self.sendRawInsteonCommand, 'updateThermostatSetings': self.updateThermostatSetings, 'setHVACMode':self.setHVACMode, 'setHVACFanMode':self.setHVACFanMode, 'setHVACCoolSetpoint':self.setHVACCoolSetpoint, 'setHVACHeatSetpoint':self.setHVACHeatSetpoint}
			#
			# Set object variables
			#
			self.masterName = theDeviceParameters["master"]
			self.coolInfluence = float(theDeviceParameters["coolInfluence"]) / 100.0
			self.heatInfluence = float(theDeviceParameters["heatInfluence"]) / 100.0

			self.masterThermostat = mmLib_Low.MotionMapDeviceDict[self.masterName]
			#mmLib_Log.logForce("##############" + self.deviceName + " is linking to Master " + self.masterThermostat.deviceName + ".")
			self.masterThermostat.registerCompanion(self)	# register with the master thermostat for climate collaboration


			self.occupancySensor = theDeviceParameters["occupancySensor"]
			self.online = 'unknown'
			self.occupancySensors = theDeviceParameters["occupancySensor"].split(';')
			mmLib_Low.subscribeToControllerEvents(self.occupancySensors, ['occupied', 'unoccupied'], self.processControllerEvent)

			self.resetSetpoints()


			# note there is no deviceTime settings (updateFrequency) because these wireless thermostats do not respond to update commands (
			#   they are just here as temperature sensors for the master thermostat)

			mmLib_Log.logVerbose("HVAC Companion Device " + self.deviceName + " is linking to Master " + self.masterName + ".")

			self.supportedCommandsDict.update({'updateThermostatSetings': self.updateThermostatSetings})

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	# updateThermostatSetings
	# Called from outside... theCommandParameters is required even if not used
	# no Action for now
	#
	def updateThermostatSetings(self, theCommandParameters):
		mmLib_Log.logForce("HVAC Companion Device " + self.deviceName + " does not process updateThermostatSetings commands.")



	######################################################################################
	#
	# Server Routines
	#
	######################################################################################


	#
	#	processControllerEvent(theEvent, theControllerDev) - when a controller, (usually a motion sensor) has an event, it sends the event to a loaddevice through this routine
	#
	#	theHandler format must be
	#		theHandler(theEvent, theControllerDev) where:
	#
	#		theEvent is the text representation of a single event type listed above: we handle ['occupied', 'unoccupied'] here only
	#		theControllerDev is the mmInsteon of the controller that detected the event
	#
	def processControllerEvent(self, theEvent, theControllerDev):

		originalOnline = self.online

		if theEvent == 'occupied':
			mmLib_Log.logVerbose("HVAC Companion Device " + self.deviceName + " is now online and will be considered in climate calculations.")
			self.online = 1
		else:
			mmLib_Log.logVerbose("HVAC Companion Device " + self.deviceName + " is now offline and will NOT be considered in climate calculations.")
			self.online = 0
			self.resetSetpoints()

		if self.masterThermostat and originalOnline != self.online:
			mmLib_Log.logVerbose("HVAC Companion Device " + self.deviceName + "\'s online state changed to " + str(self.online) + ". Calling updateThermostatSetingsLogic on master \"" + self.masterThermostat.deviceName + "\"")
			self.masterThermostat.updateThermostatSetingsLogic()


	#
	# deviceUpdated
	#
	def deviceUpdated(self, origDev, newDev):
		super(mmHVACCompanion, self).deviceUpdated(origDev, newDev)  # the base class just keeps track of the time since last change
		if self.masterThermostat:
			extraMessage = ""
			if origDev.hvacMode != newDev.hvacMode:
				extraMessage = extraMessage + " HVAC Mode is now:" + str(newDev.hvacMode) + "."

			if origDev.fanMode != newDev.fanMode:
				extraMessage = extraMessage + " Fan Mode is now:" + str(newDev.fanMode) + "."

			if origDev.coolSetpoint != newDev.coolSetpoint:
				extraMessage = extraMessage + " Cool Setpoint is now:" + str(newDev.coolSetpoint) + "."

			if origDev.heatSetpoint != newDev.heatSetpoint:
				extraMessage = extraMessage + " Heat Setpoint is now:" + str(newDev.heatSetpoint) + "."

			if extraMessage != "":
				mmLib_Log.logForce("HVAC Companion Device " + self.deviceName + ": " + extraMessage + ", calling Master " + self.masterName + " with new settings.")
				self.masterThermostat.updateThermostatSetingsLogic()
		return(0)

	#
	# deviceTime - do device housekeeping... Not currently called
	#
	def deviceTime(self):
		mmLib_Log.logForce("HVAC Companion Device " + self.deviceName + " getting time.")

		return(0)

	#
	# updateThermostatSetingsLogic
	#
	def updateThermostatSetingsLogic(self):
		super(mmHVACCompanion, self).updateThermostatSetingsLogic()  # the base class just keeps track of the time since last change


	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmHVACCompanion: " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmHVACCompanion: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmHVACCompanion: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

