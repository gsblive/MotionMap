############################################################################################
#
# mmLib_Log.py
# Error Log processing for MotionMap2
#
############################################################################################

# import json
import sys
import os
import traceback
import datetime
import indigo
import mmLib_Low

##################################
# Constants
##################################

MAX_LOG_SIZE = 1024*1024
RESET_LOG_SIZE = 512*1024


# Log type constants. This is displayed in the left margin of the EventLog per each log entry

MM_LOG_DEBUG_NOTE = "mmDebug"
MM_LOG_VERBOSE_NOTE = "mmVrbse"
MM_LOG_TERSE_NOTE = "mmTerse"
MM_LOG_WARNING = "mmWARNG"
MM_LOG_ERROR = "mmERROR"
MM_LOG_FORCE_NOTE = "mmForce "
MM_LOG_TIMESTAMP = "mmTStmp"
MM_LOG_REPORT = " "

# Log Filtering - for mmLogSensitivity
MM_SHOW_EVERYTHING = 'all'
MM_SHOW_VERBOSE_NOTES = 'verbose'
MM_SHOW_TERSE_NOTES = 'terse'
MM_SHOW_WARNINGS = 'warnings'
MM_SHOW_ERRORS = 'errors'

loggerDispatchTable = {}	# Must be initialized at init time when we have a pointer to our plugin object
logSuoportedSensitivities = [ MM_SHOW_EVERYTHING, MM_SHOW_VERBOSE_NOTES, MM_SHOW_TERSE_NOTES, MM_SHOW_WARNINGS, MM_SHOW_ERRORS]

##################################
# Log Runtime Settings
##################################

mmLogFileName = "undefined"
mmDefaultLogSensitivity = MM_SHOW_TERSE_NOTES
mmLogSensitivity = "undefined"	# Force actual setting in first call to SetSensitivity


############################################################################################
############################################################################################
#
#  Logging JumpTable - These are used as the logging entry points for the routines below
#
#  	These are the functions to call to print a log entry
#
############################################################################################
############################################################################################

#	mmLogNone - Default Proc
#
def mmLogNone(logMessage):
	pass

logDebug = mmLogNone
logVerbose = mmLogNone
logTerse = mmLogNone
logWarning = mmLogNone
logError = mmLogNone
logForce = mmLogNone
logTimestamp = mmLogNone
logReportLine = mmLogNone


############################################################################################
############################################################################################
#
#	Internal Logging Support functions
#
############################################################################################
############################################################################################

#
# trimFile
#
# Used to trim the logfile
#
def trimFile(theFilename,resetSize):

	indigo.server.log("Trimming Log File to: " + str(resetSize))

	f = open(theFilename, "r")
	f.seek(-resetSize, 2)
	for totalReads in range(1,100):
		line = f.readline()
		if line[:1] == '\n':break
	fMem = f.read()
	f = open(theFilename, "w")
	f.write(fMem)
	f.close()


#
# Write the provided log information to a file
#
def writeToLogFile(logType, logMessage, writeTimeStamp, writeTraceLog):

	theDateTime = datetime.datetime.now().strftime("%I:%M:%S %p") + " "

	try:
		f = open(mmLogFileName, 'a')

		if writeTimeStamp:
			f.write("==============================================================" + '\n' + "=" + '\n')
			f.write("=      Timestamp " + theDateTime + '\n')
			f.write("=      Message: " + logMessage + '\n' + "=" + '\n')
			f.write("==============================================================" + '\n')

		if writeTraceLog:
			if logType == MM_LOG_WARNING:
				f.write(theDateTime + " WARNING: " + logMessage + '\n')
				traceback.print_stack(f=None, limit=None, file=f)
			elif logType == MM_LOG_ERROR:
				f.write(theDateTime + " ERROR: " + logMessage + '\n')
				traceback.print_exc(limit=None, file=f)

		f.write('\n\n\n')
		f.close()
		if os.path.getsize(mmLogFileName) > MAX_LOG_SIZE: trimFile(mmLogFileName, RESET_LOG_SIZE)
	except:
		indigo.server.log("Could not open Log file")

	return(logMessage)



# displayMessage	Format and display the lof message
#
def displayMessage(logType, logMessage, diplayProc):

	global indentList

	theTrace = traceback.extract_stack()
	NestingDepth = len(theTrace) - 3
	aLine = theTrace[NestingDepth]

	if NestingDepth < 0: NestingDepth = 0
	elif NestingDepth > 20: NestingDepth = 21

	callingFile = os.path.basename(str(aLine[0]))
	callingProc = str(aLine[2])
	callingLine = str(aLine[1])
	callingTime = datetime.datetime.now().strftime("%I:%M:%S %p")
	callingPackage = str("(" + callingFile + "." + callingProc + ":" + callingLine + ")" )

	if diplayProc == indigo.server.log:
		diplayProc('|' * NestingDepth + "< " + callingProc + ':' + logMessage + " " + callingPackage, callingTime + " " + logType)
	else:
		diplayProc(str('|' * NestingDepth  + "< " + callingTime + " " + logType + ", " + callingProc + ':' + logMessage + " " + callingPackage))

	return




############################################################################################
############################################################################################
#
# The actual logging functions are here (referenced by the jump table near the top)
#
############################################################################################
############################################################################################


# mmDebugNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_EVERYTHING
#
def mmDebugNote(logMessage):
	displayMessage(MM_LOG_DEBUG_NOTE, logMessage, loggerDispatchTable[MM_LOG_DEBUG_NOTE])
	writeToLogFile(MM_LOG_TERSE_NOTE, logMessage, 1, 1)
	return


#	mmVerboseNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_VERBOSE_NOTES
#
def mmVerboseNote(logMessage):
	displayMessage(MM_LOG_VERBOSE_NOTE, logMessage, indigo.server.log)
	return


#	mmTerseNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_TERSE_NOTES
#
def mmTerseNote(logMessage):
	displayMessage(MM_LOG_TERSE_NOTE, logMessage, loggerDispatchTable[MM_LOG_TERSE_NOTE])
	return



#	mmWarning - only show the message provided if mmLogSensitivity is set to MM_SHOW_WARNINGS, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmWarning(logMessage):
	displayMessage(MM_LOG_WARNING, logMessage, loggerDispatchTable[MM_LOG_WARNING])
	writeToLogFile(MM_LOG_WARNING, logMessage, 1, 1)
	return


#	mmError - only show the message provided if mmLogSensitivity is set to MM_SHOW_ERRORS, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmError(logMessage):
	displayMessage(MM_LOG_ERROR, logMessage, loggerDispatchTable[MM_LOG_ERROR])
	writeToLogFile(MM_LOG_ERROR, logMessage, 1, 1)
	return


#	mmForceNote - show the message provided in all cases
#
def mmForceNote(logMessage):
	displayMessage(MM_LOG_FORCE_NOTE, logMessage, indigo.server.log)
	return

#	mmPrintReportLine - show the message provided in all cases
#
def mmPrintReportLine(logMessage):
	return indigo.server.log(logMessage," ")


#	mmTimestamp - show the message provided in all cases, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmTimestamp(logMessage):
	displayMessage(MM_LOG_TIMESTAMP, logMessage, loggerDispatchTable[MM_LOG_TIMESTAMP])
	writeToLogFile(MM_LOG_TIMESTAMP, logMessage, 1, 0)
	return



############################################################################################
############################################################################################
#
#	Other User Callable Logging functions
#
############################################################################################
############################################################################################


############################################################################################
#
# getLogSensitivity
#
#	will return:
# 		MM_SHOW_EVERYTHING = 0
# 		MM_SHOW_VERBOSE_NOTES = 1
# 		MM_SHOW_TERSE_NOTES = 2
# 		MM_SHOW_WARNINGS = 3
# 		MM_SHOW_ERRORS = 4
#
#############################################################################################
def getLogSensitivity():
	global mmLogSensitivity
	#indigo.server.log("getLogSensitivity is returning " + str(mmLogSensitivity))
	return(mmLogSensitivity)



############################################################################################
#
# setLogSensitivity	This short-circuits any log processing that is beyond the scope of what would be displayed
#						Adjust the logSensitivityMap below to influence what types of messages are shown for each of the sensitivity levels
#
#	Note this function needs to be called before any logging can happen... logging is defeated bu default
#
#	accepts:
# 		MM_SHOW_EVERYTHING ('all')			Show Everything
# 		MM_SHOW_VERBOSE_NOTES ('verbose')	Show Many things
# 		MM_SHOW_TERSE_NOTES ('terse')		Show some things
# 		MM_SHOW_WARNINGS ('warnings')		Show Warnings and Errors
# 		MM_SHOW_ERRORS ('errors')			Show Only Errors
#
# 	The following logSensitivityMap is a map (from the code below) of how the Sensitivity levels mask the different logging types. Entries containing mmLogNone are masked
#	Look accross the top row to find your loging type of interest, then look down its column to see which sensitivity levels masks it
#
#	Note MotionMap always shows logForce, logTimestamp, and logReportLine for Program Functionality
#
#############################################################################################
#	logSensitivityMap - Controls the masking of each Log type
#											logDebug,		logVerbose,		logTerse,		logWarning,	logError,	logForce,		logTimestamp,	logReportLine
logSensitivityMap = {
					MM_SHOW_EVERYTHING: 	[mmDebugNote,	mmVerboseNote,	mmTerseNote,	mmWarning,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine],
					MM_SHOW_VERBOSE_NOTES:	[mmLogNone,		mmVerboseNote,	mmTerseNote,	mmWarning,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine],
					MM_SHOW_TERSE_NOTES:	[mmLogNone,		mmLogNone,		mmTerseNote,	mmWarning,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine],
					MM_SHOW_WARNINGS:		[mmLogNone,		mmLogNone,		mmLogNone,		mmWarning,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine],
					MM_SHOW_ERRORS:			[mmLogNone,		mmLogNone,		mmLogNone,		mmLogNone,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine]}

def setLogSensitivity(newVal):

	global mmLogSensitivity
	global logDebug
	global logVerbose
	global logTerse
	global logWarning
	global logError
	global logForce
	global logTimestamp
	global logReportLine
	global logSensitivityMap

	if mmLogSensitivity != newVal:

		try:
			newSettings = logSensitivityMap[newVal]
		except:
			mmWarning("  Log Sensitivity mode \'" + str(newVal) + "\' is not supported. Try one of these: " )
			mmWarning( str( logSuoportedSensitivities ))
			return(mmLogSensitivity)

		logDebug = newSettings[0]
		logVerbose = newSettings[1]
		logTerse = newSettings[2]
		logWarning = newSettings[3]
		logError = newSettings[4]
		logForce = newSettings[5]
		logTimestamp = newSettings[6]
		logReportLine = newSettings[7]
		mmLogSensitivity = newVal

		mmForceNote("  Log Sensitivity is now: \'" + newVal + "\'.")

		# Update The indigo Variable too

		mmLib_Low.setIndigoVariable('MMLoggingMode', newVal)


	return(newVal)



############################################################################################
#
#	setLogSensitivityMMCommand	Same Command as above, but used by Indigo Scripts through the executeMMCommand
#
############################################################################################

def setLogSensitivityMMCommand(theParameters):

	try:
		theNewValue = theParameters["TheValue"]
	except:
		mmWarning("SetLogSensitivity cammand did not include \'TheValue\'")
		return(1)

	setLogSensitivity(theNewValue)

	return (1)



############################################################################################
#
#	verifyLogMode
#
#		When the user sets the Indigo Variable 'MMLoggingMode', verify its accuracy and set
#			mmLogSensitivity accordingly
#
# theCommandParameters is unused
#
############################################################################################
def verifyLogMode(theCommandParameters):

	varTextValue = mmLib_Low.getIndigoVariable('MMLoggingMode', 'terse')
	setLogSensitivity(varTextValue)

#
#	initLoggerDispatchTable	Must be called from init before any log calls
#
def	initLoggerDispatchTable():
	global	loggerDispatchTable

	loggerDispatchTable = {
						MM_LOG_DEBUG_NOTE: mmOurPlugin.logger.debug,
						MM_LOG_VERBOSE_NOTE: indigo.server.log,
						MM_LOG_TERSE_NOTE: mmOurPlugin.logger.info,
						MM_LOG_WARNING: mmOurPlugin.logger.warn,
						MM_LOG_ERROR: mmOurPlugin.logger.error,
						MM_LOG_FORCE_NOTE: indigo.server.log,
						MM_LOG_TIMESTAMP: mmOurPlugin.logger.info,
						MM_LOG_REPORT: indigo.server.log
						}

############################################################################################
#
#
# Initialization
#
#
############################################################################################
def init(logFileName, ourPlugin):

	global mmLogFileName
	global mmOurPlugin


	mmOurPlugin = ourPlugin
	mmLogFileName = logFileName
	initLoggerDispatchTable()
	setLogSensitivity(mmDefaultLogSensitivity)
	logForce( "--- Initializing mmLog")

def start():

	logForce( "--- Starting mmLog")
	verifyLogMode({'theCommand':'verifyLogMode'})

