__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

import mmLib_Log
import mmLib_Low
import mmObj_Motion
import mmObj_Multisensor
import mmDev_InsteonLoad
import mmDev_ZWaveLoad
import mmObj_Companion
import mmDev_HVACInsteon
import mmDev_HVACNest
import mmDev_HVACCompanion
import mmObj_Scene
import mmObj_Occupation
import mmObj_CamMotion
import time

######################################################
#
# parseConfig - Open and read a configuration file that creates and initializes all mm Devices
#
######################################################
def parseConfig(theFilePath):
	pauseMode = 0
	currentHeader = []
	processHeader = 0
	currentmmDeviceType = ""
#	inObjectTime = 0

	initialLogSensitivity = mmLib_Log.getLogSensitivity()

	mmLib_Log.logTerse("Parsing file: " + theFilePath)


	f = open(theFilePath, 'r')

	objectJumpTable = {'MotionSensor':mmObj_Motion.mmMotion,'Multisensor':mmObj_Multisensor.mmMultisensor,'CamMotion':mmObj_CamMotion.mmCamMotion,'LoadDevice':mmDev_InsteonLoad.mmILoad, 'zLoadDevice':mmDev_ZWaveLoad.mmZLoad, 'Companion':mmObj_Companion.mmCompanion, 'HVAC_Insteon':mmDev_HVACInsteon.mmHVACInsteon, 'HVAC_Nest':mmDev_HVACNest.mmHVACNest, 'HVAC_Insteon_Companion':mmDev_HVACCompanion.mmHVACCompanion, 'Scene':mmObj_Scene.mmScene, 'OccupationAction':mmObj_Occupation.mmOccupation}

	for line in f:
		# Filter out blank lines
		lineList = line.strip()
		lineList = lineList.split(",")

		if lineList[0] == "" or line[0] == "#": continue  # Filter out comment and blank lines
		if pauseMode != 0 and line[1] != 'r': continue  # Bail if we are in pause mode

		if line[0] == '-':  # Is it a Directive?
			#
			# It was a directive, Process it
			mmLib_Log.logVerbose("Processing Directive " + lineList[0])

			if line[1] == 'e':  # Processing Directive -echo
				mmLib_Log.logVerbose("echo: " + lineList[1])

			elif line[1] == 'd':  # Processing Directive -debug
				mmLib_Log.setLogSensitivity(mmLib_Log.MM_SHOW_VERBOSE_NOTES)
				mmLib_Log.logForce("Debug mode on")

			elif line[1] == 's':  # Processing Directive -set
				mmLib_Log.logForce("Setting Indigo Variables " + lineList[1] + " to " + lineList[2])
				mmLib_Low.setIndigoVariable(str(lineList[1]), str(lineList[2]))

			elif line[1] == 'h':  # Processing Directive -header
				processHeader = 1
				currentmmDeviceType = lineList[1]

			elif line[1] == 'v':  # Processing Directive -verbose
				mmLib_Log.setLogSensitivity(mmLib_Log.MM_SHOW_VERBOSE_NOTES)
				mmLib_Log.logVerbose("Debug mode on VERBOSE")

			elif line[1] == 'p':  # Processing Directive -pause
				mmLib_Log.logVerbose("Parsing Paused")
				pauseMode = 1

			elif line[1] == 'r':  # Processing Directive -resume
				mmLib_Log.logVerbose("Parsing Resumed")
				pauseMode = 0

			elif line[1] == '.':  # Processing Directive -stop
				mmLib_Log.logVerbose("Parsing Stopped")
				break

		elif processHeader == 1:  # Not a directive, Is it a Header?
			#
			# It was a Header, process it
			processHeader = 0
			lineList.insert(0, "deviceType")
			currentHeader = lineList
			mmLib_Log.logVerbose(" >>>Obtained header for device type " + currentmmDeviceType + ": " + str(currentHeader))
		else:
			#
			# Not a Header, it must be a device description line, use the current header and currentmmDeviceType to parse it
			lineList.insert(0, currentmmDeviceType)
			mmLib_Log.logVerbose("Initializing " + str(lineList[1]) + " Object: " + str(lineList[0]))

			if len(currentHeader) != len(lineList):	mmLib_Log.logForce(" === WARNING ==== Missing parameter for device " + lineList[1] )

			initParameters = dict(zip(currentHeader, lineList))

			try:
				dispatchInit = objectJumpTable[currentmmDeviceType]
			except:
				mmLib_Log.logForce(" >>>Object for device type " + currentmmDeviceType + " doesn\'t exist. ")
				continue

			mmLib_Log.logVerbose(" >>>Initializing " + str(initParameters["deviceName"]) )

			# Create and initialize the object
#			dispatchTime = time.time()
			newObject = dispatchInit(initParameters)
#			inObjectTime = inObjectTime + round(time.time() - dispatchTime, 4)

			if newObject.initResult != 0:
				mmLib_Log.logTerse("######  " + newObject.deviceName + " failed to initialize due to " + str(newObject.initResult) + ". ######")
			else:
				mmLib_Log.logVerbose("######  " + newObject.deviceName + " successfully initialized. ######")




	#
	# End of Loop
	#
	f.close()
	mmLib_Log.setLogSensitivity(initialLogSensitivity)		# restore log sensitivity (in case it changed while parsing)
#	mmLib_Log.logForce("  +TIMETRACK:" + str(inObjectTime) + "s. Time in objects.")
	mmLib_Log.logTerse("Complete Parsing file: " + theFilePath)


######################################################
#
# init - Open and read a configuration file that creates and initializes all mm Devices
#
######################################################
def init(configFileName):
	parseConfig(configFileName)
	mmLib_Low.refreshControllers()
	
