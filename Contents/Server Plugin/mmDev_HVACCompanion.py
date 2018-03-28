

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
			mmLib_Events.subscribeToEvents(['occupied', 'unoccupied'], self.occupancySensors, self.processControllerEvent, {}, self.deviceName)

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
	#	processControllerEvent(theEvent, eventParameters) - when a controller, (usually a motion sensor) has an event, it sends the event to a loaddevice through this routine
	#
	#	theHandler format must be
	#		theHandler(theEvent, theControllerDev) where:
	#
	#		theEvent is the text representation of a single event type listed above: we handle ['occupied', 'unoccupied'] here only
	#		theControllerDev is the mmInsteon of the controller that detected the event
	#
	def processControllerEvent(self, theEvent, eventParameters):

		originalOnline = self.online
		theControllerDev = mmLib_Low.MotionMapDeviceDict[eventParameters['publisher']]

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
	def	deviceUpdatedEvent(self,eventID, eventParameters):

		super(mmHVACCompanion, self).deviceUpdatedEvent(eventID, eventParameters)  # the base class just keeps track of the time since last change

		newhvacMode = eventParameters.get('hvacMode', 'na')
		newfanMode = eventParameters.get('fanMode', 'na')
		newcoolSetpoint = eventParameters.get('coolSetpoint', 'na')
		newheatSetpoint = eventParameters.get('heatSetpoint', 'na')

		if self.masterThermostat:
			extraMessage = ""
			if newhvacMode != 'na':
				extraMessage = extraMessage + " HVAC Mode is now:" + str(newhvacMode) + "."

			if newfanMode != 'na':
				extraMessage = extraMessage + " Fan Mode is now:" + str(newfanMode) + "."

			if newcoolSetpoint != 'na':
				extraMessage = extraMessage + " Cool Setpoint is now:" + str(newcoolSetpoint) + "."

			if newheatSetpoint != 'na':
				extraMessage = extraMessage + " Heat Setpoint is now:" + str(newheatSetpoint) + "."

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


