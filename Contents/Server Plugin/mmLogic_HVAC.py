
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

import mmComm_HVACCommands
from collections import deque

######################################################
######################################################

######################################################
#
# mmHVAC - Logic to calculate HVAC settings
#
# 	In additional to traditional occupancy-based setbacks, this routine:
# 		Factors in Heat/Cool settings of the companion thermostats
# 		Factors in Temperature readings of the companion thermostats
# 		Factors in Outside Temperature by proactively adjusting setpoints while predicting outside temp influence on inside temperature
#		Will activate HVAC fan functions when there is a wide discrepancy in temperature between Main thermostat and the companions
#		All HVAC climate calculations skip input from companion thermostats that are in unoccupied areas of the house
# 		All HVAC commands are now handled in the queue
#		If the user manually sets any main thermostat, that change stays in effect until the house becomes unoccupied
#
#
#	for 2.0 version
#		Add zone temperature support from multisensors
#		Drop companion thermostats, but allow for up down temp control from zones with external commands (i.e. iOS devices)
#		Add secondary heat source control (fireplaces and space heaters)
#		Only consider confort conditions in occupied spaces
#		rework logic
#			A thermostat controls the comfort of an entire domain
#			A domain in a collection of zones (rooms)
#			A zones must have a multisensor
#			A Zone can have secondary heat
#				Fireplace and Electric Heat may have different profiles for safety
#			Cool Zones can reduce the temp of neighboring Warm zones by use of the HVAC fan
#			Warm zones can warm cold zones by use of the HVAC fan
#			All zones will warm and cool naturally (within reason) due to outside conditions
#				# this may influence the speed of which we will allow for heat and cold to be requested
#
#
#		Implementation
#			Define Zones and Domains in new object types
#			These objects will controlled by iOS
#			These Objects will Influence settings in the Thermostats
#
######################################################
class mmHVAC(mmComm_HVACCommands.mmHVACCommands):


	def __init__(self, theDeviceParameters):

		mmLib_Log.logVerbose( "mmHVAC Initialization. ")

		super(mmHVAC, self).__init__(theDeviceParameters)  # Initialize Base Class
		if self.initResult == 0:
			self.supportedCommandsDict.update({'updateThermostatSetings':self.updateThermostatSetings})


			mmLib_Events.subscribeToEvents(['initComplete'], ['MMSys'], self.initializationComplete, {}, self.deviceName)

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

		super(mmHVAC, self).deviceUpdated(origDev, newDev)  # the base class just keeps track of the time since last change

		#
		# do all the comparisons in integer values
		if self.initializationInProgress == 1: return(0)

		needUpdate = 0

		originalHeatSetpoint = int(origDev.heatSetpoint)
		newHeatSetpoint = int(newDev.heatSetpoint)
		originalCoolSetpoint = int(origDev.coolSetpoint)
		newCoolSetpoint = int(newDev.coolSetpoint)

		if originalHeatSetpoint != newHeatSetpoint:
			if newHeatSetpoint != self.calculatedHeatSetpoint:
				mmLib_Log.logForce("HeatSetpoint changed by Occupant for HVAC Device " + self.deviceName + ". was " + str(originalHeatSetpoint) + ", now is " + str(newHeatSetpoint) + ". Updating Custom HeatSetpoint to " + str(newHeatSetpoint))
				self.customHeatSetpoint = newHeatSetpoint
				needUpdate = 1
			else:
				mmLib_Log.logVerbose("HeatSetpoint changed by MotionMap for HVAC Device " + self.deviceName + ". was " + str(originalHeatSetpoint) + ", now is " + str(newHeatSetpoint))

		if originalCoolSetpoint != newCoolSetpoint:
			if newCoolSetpoint != self.calculatedCoolSetpoint:
				mmLib_Log.logForce("CoolSetpoint changed by Occupant for HVAC Device " + self.deviceName + ". was " + str(originalCoolSetpoint) + ", now is " + str(newCoolSetpoint) + ". Updating Custom CoolSetpoint to " + str(newCoolSetpoint))
				self.customCoolSetpoint = newCoolSetpoint
				needUpdate = 1
			else:
				mmLib_Log.logVerbose("CoolSetpoint changed by MotionMap for HVAC Device " + self.deviceName + ". was " + str(originalCoolSetpoint) + ", now is " + str(newCoolSetpoint))

		if needUpdate:
			self.updateThermostatSetingsLogic()

		if origDev.displayStateImageSel != newDev.displayStateImageSel:
			mmLib_Log.logVerbose("HeatCoolMode changed for HVAC Device " + self.deviceName + " to " + str(newDev.displayStateImageSel))

		if origDev.displayStateValRaw != newDev.displayStateValRaw:
			mmLib_Log.logVerbose("Temperature changed for HVAC Device " + self.deviceName + " to " + str(newDev.displayStateValRaw))



	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	#def completeCommand(self, theInsteonCommand ):
	#	super(mmHVAC, self).completeCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# receivedCommand - we received a command from our device.
	#
	#def receivedCommand(self, theInsteonCommand ):
	#	super(mmHVAC, self).receivedCommand(theInsteonCommand)	# Nothing special here, forward to the Base class

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	#def errorCommand(self, theInsteonCommand ):
	#	super(mmHVAC, self).errorCommand(theInsteonCommand)	# Nothing special here, forward to the Base class





	######################################################################################
	#
	# Externally Addressable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	# updateThermostatSetings
	# Called from outside... theCommandParameters is required even if not used
	#
	def updateThermostatSetings(self, theCommandParameters):
		mmLib_Log.logForce("updateThermostatSetings has been called. " + self.deviceName + " is calling updateThermostatSetingsLogic")
		return (self.updateThermostatSetingsLogic())


	######################################################################################
	#
	# HVAC Logic Routines
	#
	######################################################################################

	#
	# enumerate the companions and compare the delta between each thermostat... return the maximum temperature disparity
	# MOde:
	#	'fan' = get full delta even if areas are offline
	#	'heat' or 'cool' = consider online and offline state of the sensors
	#
	def getTemperatureDelta(self, mode):
		currentDelta = 0
		if self.companionDeque:
			for theCompanion in self.companionDeque:
				if mode == 'fan' or theCompanion.online:
					if float(theCompanion.theIndigoDevice.displayStateValRaw) != 0.0 and self.theIndigoDevice.displayStateValRaw != theCompanion.theIndigoDevice.displayStateValRaw:
						newDelta = int(abs(float(self.theIndigoDevice.displayStateValRaw) - float(theCompanion.theIndigoDevice.displayStateValRaw)))
						if newDelta > currentDelta: currentDelta = newDelta
		return(currentDelta)


	#
	# enumerate the companions and average them with this thermostat's temperature
	# returned in whole integer
	#
	def getAverageTemperature(self, outsideTempMode):

		thermostatTemp = float(self.theIndigoDevice.displayStateValRaw)
		accumulatedTemp = thermostatTemp		# Count this thermostat in the average
		showMath = "(" + str(accumulatedTemp) + "[" + self.deviceName + "]"
		factorCount = 1.0

		if self.companionDeque:
			for theCompanion in self.companionDeque:
				if theCompanion.online:
					theTemperature = float(theCompanion.theIndigoDevice.displayStateValRaw)
					if theTemperature != 0.0:
						accumulatedTemp = accumulatedTemp + theTemperature
						showMath = showMath + " + " + str(theTemperature) + "[" + theCompanion.deviceName + "]"
						factorCount = factorCount + 1.0

		if outsideTempMode:
			outsideTempInfluence = 0
			MaxInfluenceOutside = float(2*factorCount)
			outsideTemp = float(indigo.variables['Local_Outside_Temperature'].value)
			inOutTempDifference = abs(outsideTemp - thermostatTemp)
			if inOutTempDifference > MaxInfluenceOutside:
				inOutTempDifference = MaxInfluenceOutside
				if outsideTemp > thermostatTemp:
					outsideTempInfluence = thermostatTemp + inOutTempDifference
				else:
					outsideTempInfluence = thermostatTemp - inOutTempDifference

			if outsideTempInfluence:
				accumulatedTemp = accumulatedTemp + outsideTempInfluence
				showMath = showMath + " + " + str(outsideTempInfluence) + " [outside " + str(outsideTemp) + ", normalized to maximum influence of " + str(MaxInfluenceOutside) + " degrees of " + self.deviceName + "\'s actual temperature reading: " + str(thermostatTemp) + " degrees ]"
				factorCount = factorCount + 1.0
			else:
				showMath = showMath + "[outside " + str(outsideTemp) + ", out of range]"

		averageTemp = accumulatedTemp/factorCount
		showMath = showMath + ") / " + str(factorCount)

		self.statusMessage = self.statusMessage + "\n" + outsideTempMode + " mode. " + self.deviceName + "\'s average domain temperature is " + str(averageTemp) + " = " + str(showMath)

		return(int(averageTemp))

	#
	# Reset companion Setpoints
	#
	def resetCompanionSetpoints(self):
		if self.companionDeque:
			for theCompanion in self.companionDeque: theCompanion.resetSetpoint()
		return(0)

	#
	# enumerate the companions and return the average Setpoint delta between main thermostat and companions
	#
	#	heatOrCool = 'heat' or 'cool'
	#	currentSetpoint = float (the current Setpoint for self)

	def factorCompanionSetpoints(self, heatOrCool, currentSetpoint):
		numberOfCompanions = 0.0
		accumulatedSetpointInfluence = 0.0
		SetpointResult = 0
		totalAverageInfluence = 0.0
		factorMessage = ""
		if self.companionDeque:

			for theCompanion in self.companionDeque:
				if not numberOfCompanions:
					factorMessage = self.deviceName + "\'s original " + heatOrCool + "setpoint (s): " + str(currentSetpoint) + ". Calculating companion influence (i) with values: ( "
				else:
					factorMessage = factorMessage + ", "

				factorMessage = factorMessage + theCompanion.deviceName + " ["

				if theCompanion.online:
					#mmLib_Log.logVerbose( theCompanion.deviceName + " is online with value "+ str(theCompanion.online) + ", factoring settings.")
					numberOfCompanions = numberOfCompanions + 1.0
					if heatOrCool == 'heat':
						# accumulate heatSetpoint Delta
						factorMessage = factorMessage + "s=" + str(theCompanion.theIndigoDevice.heatSetpoint)
						newDelta = float(theCompanion.theIndigoDevice.heatSetpoint) - currentSetpoint
						influenceValue = newDelta * theCompanion.heatInfluence
					else:
						# accumulate coolSetpoint Delta
						factorMessage = factorMessage + "s=" + str(theCompanion.theIndigoDevice.coolSetpoint)
						newDelta = float(theCompanion.theIndigoDevice.coolSetpoint) - currentSetpoint
						influenceValue = newDelta * theCompanion.coolInfluence

					factorMessage = factorMessage + ";i=" + str(influenceValue)
					accumulatedSetpointInfluence = accumulatedSetpointInfluence + influenceValue
				else:
					factorMessage = factorMessage + "offline"

				factorMessage = factorMessage + "]"

			if int(numberOfCompanions) > 0:
				factorMessage = factorMessage + " )"
				self.statusMessage = self.statusMessage + "\n" + factorMessage
				totalAverageInfluence = accumulatedSetpointInfluence / numberOfCompanions
				tSetpointResult = int(float(currentSetpoint) + float(totalAverageInfluence))
				if currentSetpoint != tSetpointResult:
					SetpointResult = tSetpointResult
					self.statusMessage = self.statusMessage + "\n" + self.deviceName + "\'s " + heatOrCool + " Setpoint is being influenced by companions by " + str(totalAverageInfluence) + " degrees. To " + str(SetpointResult)

		return(SetpointResult)


	#
	# updateThermostatSetingsLogic
	#
	def updateThermostatSetingsLogic(self):

		if self.operationalMode == 'HvacMonitor' or self.initializationInProgress: return(0)		# we dont need to process monitors

		#
		# First set operational mode

		mmLib_Log.logVerbose("Update HVAC Settings " + self.deviceName + " Evaluating motion, companions and outside temp.")
		self.statusMessage = "\nHVAC Device " + self.deviceName + "\'s Last pass through updateThermostatSetingsLogic() resulted in:\n "

		#
		# Set the operational mode
		processingHeatMode = 0
		processingCoolMode = 0

		if self.operationalMode == 'HvacHeatMode' :
			newOperationMode = indigo.kHvacMode.Heat
			processingHeatMode = 1
		elif self.operationalMode == 'HvacCoolMode' :
			newOperationMode = indigo.kHvacMode.Cool
			processingCoolMode = 1
		else:
			newOperationMode = indigo.kHvacMode.HeatCool
			processingHeatMode = 1
			processingCoolMode = 1

		if newOperationMode !=  self.theIndigoDevice.hvacMode:
			self.statusMessage = self.statusMessage + "\nHVAC Device " + self.deviceName + " Initializing hvacMode to " + str(newOperationMode) + "."
			self.queueCommand({'theCommand':'setHVACMode', 'theDevice':self.deviceName, 'theValue':newOperationMode, 'retry':2})

		#
		#  check to see if the house is occupied

		# if house has been occupied, any motion can keep the hvac on
		# if it has been unoccupied, only certain motions can turn it back on

		if self.areaOccupied == 1:
			#mmLib_Log.logForce( "HVAC Device " + self.deviceName + " Checking Combined Controllers  " + str(self.combinedControllers))
			secondsSinceNoMotionInArea = int(self.getSecondsSinceNoMotionInArea(self.combinedControllers))	# checking for sustained (any controller can sustain)
			#mmLib_Log.logForce( "  HVAC Device " + self.deviceName + " Found NoMotion at  " + str(secondsSinceNoMotionInArea) + " seconds.")
		else:
			#mmLib_Log.logForce( "HVAC Device " + self.deviceName + " Checking On Controllers  " + str(self.onControllers))
			secondsSinceNoMotionInArea = int(self.getSecondsSinceNoMotionInArea(self.onControllers))		# checking for on
			#mmLib_Log.logForce( "  HVAC Device " + self.deviceName + " Found NoMotion at  " + str(secondsSinceNoMotionInArea) + " seconds.")

		if secondsSinceNoMotionInArea > mmLib_Low.HVAC_SETBACK_THRESHOLD_TIME_SECONDS:
			if self.areaOccupied != 0:
				self.statusMessage = self.statusMessage + "\nHVAC Device " + self.deviceName + "\'s area has become unoccupied, resetting Custom setpoints."
				self.areaOccupied = 0
				#
				# The house is now considered unoccupied, clear the desired Temps
				self.customCoolSetpoint = 0
				self.customHeatSetpoint = 0
				if self.companionDeque:
					for theCompanion in self.companionDeque: theCompanion.resetSetpoints()
		else:
			self.areaOccupied = 1


		#
		# Establish the base temperature settings

		if 0:
			# GB Fix me
			if self.customCoolSetpoint:
				newCoolSetpoint = self.customCoolSetpoint
				mmLib_Log.logForce("HVAC Device " + self.deviceName + " Custom CoolSetpoint in effect: " + str(self.customCoolSetpoint))
			else:
				newCoolSetpoint = self.coolSetpoint

			if self.customHeatSetpoint:
				newHeatSetpoint = self.customHeatSetpoint
				mmLib_Log.logForce("HVAC Device " + self.deviceName + " Custom HeatSetpoint in effect: " + str(self.customHeatSetpoint))
			else:
				newHeatSetpoint = self.heatSetpoint
		else:
			newHeatSetpoint = self.heatSetpoint
			newCoolSetpoint = self.coolSetpoint

		#
		# set the default fanmode

		newFanMode = indigo.kFanMode.Auto

		#
		# Evaluate motion first... if we are supposed to turn, do it (we will always be on, just adjust the temp)
		# reset current temp settings to default (considering influence from outside factors [companions and outside temp])

		if self.areaOccupied == 0:
			newCoolSetpoint = newCoolSetpoint + 10
			newHeatSetpoint = newHeatSetpoint - 10
			self.statusMessage = self.statusMessage + "\nHVAC Device " + self.deviceName + " Unoccupied setback in effect. Setting CoolSetpoint to " + str(newCoolSetpoint) + " and HeatSetpoint to " + str(newHeatSetpoint)
		else:
			#
			# people are in the house, calculate the ideal temperature

			# Process cool setpoint if in cool mode
			#
			if processingCoolMode and self.customCoolSetpoint == 0:
				#
				# Factor in Companions setpoints
				t_newCoolSetpoint = self.factorCompanionSetpoints('cool', float(newCoolSetpoint))
				if t_newCoolSetpoint:
					newCoolSetpoint = t_newCoolSetpoint

				#
				# Factor in domain average temperatures
				averageSensorTemp = self.getAverageTemperature('cool')
				proposedCoolSetpointDelta = int((newCoolSetpoint - averageSensorTemp)/2)	# split the difference between coolSetpoint and average temp... we work in signed whole numbers
				if proposedCoolSetpointDelta != 0:
					if proposedCoolSetpointDelta > 0:
						# average temps are cooler than newCoolSetpoint by a significant amount
						self.statusMessage = self.statusMessage + "\n" + self.deviceName + "\'s calculated coolSetpoint (" + str(newCoolSetpoint) + " degrees) is higher than the average inside temperature (" + str(averageSensorTemp) + ") by " + str(newCoolSetpoint - averageSensorTemp) + " degrees."
						self.statusMessage = self.statusMessage + "\n    As a result we are increasing the coolSetpoint by " + str(proposedCoolSetpointDelta) + " degrees to " + str(newCoolSetpoint + proposedCoolSetpointDelta) + " and letting the HVAC fan mix the air as needed."
					else:
						# average temps are warmer than newCoolSetpoint by a significant amount
						self.statusMessage = self.statusMessage + "\n" + self.deviceName + "\'s calculated coolSetpoint (" + str(newCoolSetpoint) + " degrees) is lower than the inside average temperature of its remote sensors (" + str(averageSensorTemp) + ") by " + str(abs(newCoolSetpoint - averageSensorTemp)) + " degrees."
						self.statusMessage = self.statusMessage + "\n   As a result we are reducing the coolSetpoint by " + str(abs(proposedCoolSetpointDelta)) + " degrees to " + str(newCoolSetpoint + proposedCoolSetpointDelta) + " to quickly cool the hot areas of the house and mix the household air to equalize the temperatures."

					newCoolSetpoint = newCoolSetpoint + proposedCoolSetpointDelta		# apply half the difference to newCoolSetpoint. The sign takes care of +/-

			#
			# Process heat setpoint if in heat mode
			#
			if processingHeatMode and self.customHeatSetpoint == 0:

				#
				# Factor in Companions setpoints
				t_newHeatSetpoint = self.factorCompanionSetpoints('heat', float(newHeatSetpoint))
				if t_newHeatSetpoint:
					newHeatSetpoint = t_newHeatSetpoint

				#
				# Factor in domain average temperatures
				averageSensorTemp = self.getAverageTemperature('heat')
				proposedHeatSetpointDelta = int((newHeatSetpoint - averageSensorTemp)/2)	# split the difference between heatSetpoint and average temp... we work in signed whole numbers
				if proposedHeatSetpointDelta != 0:
					if proposedHeatSetpointDelta < 0:
						# average temps are warmer than newHeatSetpoint by a significant amount
						self.statusMessage = self.statusMessage + "\n" + self.deviceName + "\'s calculated heatSetpoint (" + str(newHeatSetpoint) + " degrees) is lower than the inside average temperature of its remote sensors (" + str(averageSensorTemp) + ") by " + str(abs(newHeatSetpoint - averageSensorTemp)) + " degrees."
						self.statusMessage = self.statusMessage + "\n   As a result we are reducing the heatSetpoint by " + str(abs(proposedHeatSetpointDelta)) + " degrees to " + str(newHeatSetpoint + proposedHeatSetpointDelta) + " and letting the HVAC fan mix the air as needed."
					else:
						# average temps are cooler than newHeatSetpoint by a significant amount
						self.statusMessage = self.statusMessage + "\n" + self.deviceName + "\'s calculated heatSetpoint (" + str(newHeatSetpoint) + " degrees) is higher than the inside average temperature of its remote sensors (" + str(averageSensorTemp) + ") by " + str(newHeatSetpoint - averageSensorTemp) + " degrees."
						self.statusMessage = self.statusMessage + "\n   As a result we are increasing the heatSetpoint by " + str(proposedHeatSetpointDelta) + " degrees to " + str(newHeatSetpoint + proposedHeatSetpointDelta) + " to quickly warm the cold areas of the house and mix the household air to equalize the temperatures."

					newHeatSetpoint = newHeatSetpoint + proposedHeatSetpointDelta		# apply half the difference to newHeatSetpoint. The sign takes care of +/-

			#
			# set the fanmode to ON if there is a big disparity of temperatures between this thermostat and the companions
			#
			temperatureDelta = self.getTemperatureDelta('fan')
			if temperatureDelta > self.maxTempDelta:
				self.statusMessage = self.statusMessage + "\nMulti-Thermostat temperature Delta found of: " + str(temperatureDelta) + " degrees. Turning Fan on for HVAC " + self.deviceName + " to mix the air."
				newFanMode = indigo.kFanMode.AlwaysOn		# mix the air

		#
		# Impose outer bounds on the New Setpoints
		#
		if int(newCoolSetpoint) > 99:
			self.statusMessage = self.statusMessage + "\nHVAC " + self.deviceName + "\'s coolSetpoint was calculated to be " + str(newCoolSetpoint) + " degrees. Above upper bound, setting it to 99."
			newCoolSetpoint = 99

		if int(newCoolSetpoint) < 65:
			self.statusMessage = self.statusMessage + "\nHVAC " + self.deviceName + "\'s coolSetpoint was calculated to be " + str(newCoolSetpoint) + " degrees. Below lower bound, setting it to 65."
			newCoolSetpoint = 65

		if int(newHeatSetpoint) > 79:
			self.statusMessage = self.statusMessage + "\nHVAC " + self.deviceName + "\'s heatSetpoint was calculated to be " + str(newHeatSetpoint) + " degrees. Above upper bound, setting it to 79."
			newHeatSetpoint = 79

		if int(newHeatSetpoint) < 55:
			self.statusMessage = self.statusMessage + "\nHVAC " + self.deviceName + "\'s heatSetpoint was calculated to be " + str(newHeatSetpoint) + " degrees. Below lower bound, setting it to 55."
			newHeatSetpoint = 55

		#
		# Now, set the heat and cool Setpoints
		#
		if (self.operationalMode == 'HvacAutoMode' or self.operationalMode == 'HvacCoolMode') and int(self.theIndigoDevice.coolSetpoint) != int(newCoolSetpoint):
			self.queueCommand({'theCommand':'setHVACCoolSetpoint', 'theDevice':self.deviceName, 'theValue':str(newCoolSetpoint), 'retry':2})
			self.calculatedCoolSetpoint = newCoolSetpoint

		if (self.operationalMode == 'HvacAutoMode' or self.operationalMode == 'HvacHeatMode') and int(self.theIndigoDevice.heatSetpoint) != int(newHeatSetpoint):
			self.queueCommand({'theCommand':'setHVACHeatSetpoint', 'theDevice':self.deviceName, 'theValue':str(newHeatSetpoint), 'retry':2})
			self.calculatedHeatSetpoint = newHeatSetpoint

		#
		# finally, set the fanmode
		if newFanMode != self.theIndigoDevice.fanMode:
			self.statusMessage = self.statusMessage + "\nHVAC " + self.deviceName + " setting fanmode to " + str(newFanMode) + " current mode is " + str(self.theIndigoDevice.fanMode)
			self.queueCommand({'theCommand':'setHVACFanMode', 'theDevice':self.deviceName, 'theValue':newFanMode, 'retry':2})

		return(0)

	######################################################################################
	#
	# MM Entry Points
	#
	######################################################################################

	#
	# deviceTime - do device housekeeping... this should happen once every 15 minutes
	#
	def deviceTime(self):
		mmLib_Log.logForce("HVAC Device " + self.deviceName + " getting time.")

		self.updateThermostatSetingsLogic()

		return(0)
	#
	# reset the heatSetPoints to the normal values
	#
	def resetSetpoints(self):

		mmLib_Log.logVerbose("ResetSetpoints has been called for device " + self.deviceName + ". CoolSetpoint is now " + str(self.coolSetpoint) + " and HeatSetpoint is " + str(self.heatSetpoint))

		if int(self.theIndigoDevice.coolSetpoint) != int(self.coolSetpoint):
			self.queueCommand({'theCommand':'setHVACCoolSetpoint', 'theDevice':self.deviceName, 'theValue':str(self.coolSetpoint), 'retry':2})

		if int(self.theIndigoDevice.heatSetpoint) != int(self.heatSetpoint):
			self.queueCommand({'theCommand':'setHVACHeatSetpoint', 'theDevice':self.deviceName, 'theValue':str(self.heatSetpoint), 'retry':2})

		return 0

	#
	#	we gave the system some time to process the intial settings before allowing processing of temp changes
	#
	def initializationComplete(self,eventID, eventParameters):
		self.initializationInProgress = 0

		# The following is done here because we set a number of the thermostat's baseline settings at init
		# time that need to be updated before final temp calculations done in updateThermostatSettingsLow()
		mmLib_Log.logVerbose( "Finalizing Initialization. " + self.deviceName + " is calling updateThermostatSetingsLogic")
		self.resetSetpoints()
		self.updateThermostatSetingsLogic()

		return 0

