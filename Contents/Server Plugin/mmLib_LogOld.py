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
try:
	import indigo
except:
	pass
import mmLib_Low
import _MotionMapPlugin
import logging

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
MM_LOG_FORCE_NOTE = "mmForce"
MM_LOG_TIMESTAMP = "mmTStmp"
MM_LOG_REPORT = "MMReprt"

LOG_DEBUG_NOTE = 11
LOG_VERBOSE_NOTE = 12
LOG_TERSE_NOTE = 15
LOG_WARNING = 35
LOG_ERROR = 45
LOG_FORCE_NOTE = 47
LOG_TIMESTAMP = 48
LOG_REPORT = 49


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

ourLoggerFile = "undefined"
mmDefaultLogSensitivity = MM_SHOW_TERSE_NOTES
mmLogSensitivity = "undefined"	# Force actual setting in first call to SetSensitivity

def prRed(skk): return ("\033[91m {}\033[00m" .format(skk))
def prGreen(skk): return ("\033[92m {}\033[00m" .format(skk))
def prCyan(skk): return ("\033[96m {}\033[00m" .format(skk))

############################################################################################
############################################################################################
#
#  Logging JumpTable - These are used as the logging entry points for the routines below
#
#  	These are the functions to call to print a log entry
#
############################################################################################
############################################################################################
#
#	Internal Logging Support functions
#
############################################################################################
############################################################################################

############################################################################################
# Special indirect routines
############################################################################################

# mmLog - WildCard, overrides current log settings for 1 single call
# Not part of the jump table above

def mmLog(MODE, logMessage):
	displayMessage(MODE, logMessage, loggerDispatchTable[MODE])
	return

#	mmLogNone - Default Proc
#	Shunt when a logging function is turned off

def mmLogNone(logMessage):
	pass

############################################################################################
# Logging Jump table
# Its here because it needs to be below mmLogNone()
#
# We can gret rid of these jump tables (which take a fair amount of system overhead), by
# Requiring an additional parameter (MM_LOG_DEBUG_NOTE, MM_LOG_VERBOSE_NOTE, etc) that will look up
# parameters and settings in a dictionary indexed by the log type... Similar to how mmLog() works above.
#
# The problem with this is that wwe will have to always put in another parameter when calling the
# displayMessage procedure
#
# The following are the namer s used for logging functions throught the code. This level of
# indirection is to allow for logging functions to be turned off selectively by setLogSensitivity()
# below. When it is called, all Log functions that are irrelivant to sensitivity level get shunted
# by the mmLogNone function as per logSensitivityMap below.
#
############################################################################################

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
# The actual logging functions are here (referenced by the jump table above)
#
############################################################################################
############################################################################################


# mmDebugNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_EVERYTHING
#

def mmDebugNote(logMessage):
	displayMessage(MM_LOG_DEBUG_NOTE, logMessage, loggerDispatchTable[MM_LOG_DEBUG_NOTE])
	return


#	mmVerboseNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_VERBOSE_NOTES
#
def mmVerboseNote(logMessage):
	displayMessage(MM_LOG_VERBOSE_NOTE, logMessage, loggerDispatchTable[MM_LOG_VERBOSE_NOTE])
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
	displayMessage(MM_LOG_FORCE_NOTE, logMessage, loggerDispatchTable[MM_LOG_FORCE_NOTE])
	return

#	mmPrintReportLine - show the message provided in all cases
#
def mmPrintReportLine(logMessage):
	displayMessage(MM_LOG_REPORT, logMessage, loggerDispatchTable[MM_LOG_REPORT])
	return


#	mmTimestamp - show the message provided in all cases, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmTimestamp(logMessage):
	displayMessage(MM_LOG_TIMESTAMP, logMessage, loggerDispatchTable[MM_LOG_TIMESTAMP])
	writeToLogFile(MM_LOG_TIMESTAMP, logMessage, 1, 0)
	return






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
		f = open(ourLoggerFile, 'a')

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
		if os.path.getsize(ourLoggerFile) > MAX_LOG_SIZE: trimFile(ourLoggerFile, RESET_LOG_SIZE)
	except:
		indigo.server.log("Could not open Log file")

	return(logMessage)



# displayMessage	Format and display the lof message
#
#	logType:			MM_LOG_DEBUG_NOTE 		Log the debugging note to SQL function logger.debug
#						MM_LOG_VERBOSE_NOTE 	Print the verbose message to the standard indigo.server.log
#						MM_LOG_TERSE_NOTE		Log the debugging note to SQL function logger.info
#						MM_LOG_WARNING 			Log the debugging note to SQL function logger.warn
#						MM_LOG_ERROR 			Log the debugging note to SQL function logger.error This will report the exception in addition to the message
#						MM_LOG_FORCE_NOTE 		Print the verbose message to the standard indigo.server.log
#						MM_LOG_TIMESTAMP		Log the debugging note to SQL function logger.info
#						MM_LOG_REPORT			Print the verbose message to the standard indigo.server.log
#
#	These logs mentioned are archived daily at midnight to timestamped files at /Library/Application Support/Perceptive Automation/Indigo 7/Logs/MotionMap3.listener/
#	All SQL Logs listed above also put test strings into PLugin.log file at the directory above. SQL versions will only be stored as directed by
#	accesing the configuation menu at Indigo 7.4->Plugins->	Plugins->SQL Logger:
#
def displayMessage(logType, logMessage, displayProc):

	exception = ""
	stringCheck = 0

	try:
		stringCheck = isinstance(logMessage, str)
	except Exception as exception:
		# this new exception will take priority over any previous exception. Here, we were handed a bad string,
		# so our original message would have thrown another exception anyway
		# Though I dont think it ever gets here.
		pass

	if not stringCheck:
			# The value passed in wasnt a string. Put up a custom message
			logMessage = "XXX displayMessage Error: Message was not a well-formed String."
			logType = MM_LOG_ERROR
			displayProc = loggerDispatchTable[logType]

	if logType == MM_LOG_REPORT:
		indigo.server.log(logMessage, " ")
	else:
		if logType == MM_LOG_ERROR:
			# Capture the exception if there is one
			excType, excValue, excTraceback = sys.exc_info()
			exception = str(excValue)
			theTrace = traceback.extract_tb(excTraceback, 1)
			NestingDepth = 0
			callingFile, callingLine, callingProc, sourceCode = theTrace[NestingDepth]	# unpack the trace record
		else:
			theTrace = traceback.extract_stack()
			NestingDepth = max(0, min(len(theTrace) - 3, 21))
			callingFile, callingLine, callingProc, sourceCode = theTrace[NestingDepth]	# unpack the trace record for the call to mmLib_Log

		callingPackage = str("(" + os.path.basename(callingFile) + "." + str(callingProc) + ":" + str(callingLine) + ")")	# Construct a MM callingPackage (we skip the jump table)
		if exception != "": exception = "[" + exception + "]"
		logMessage = '[{0:<22}] {1}'.format(str('|' * NestingDepth) + str('.' * int(22 - NestingDepth)), str( datetime.datetime.now().strftime("%I:%M:%S %p") + " [" + logType + "] " + logMessage + exception + callingPackage))

		displayProc(logMessage)

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

		mmForceNote("  Log Sensitivity is now: \'" + str(newVal) + "\'.")

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
#	Note .logger refers to an SQL logging system included in Indigo
#
def	initLoggerDispatchTable():
	global	loggerDispatchTable

	loggerDispatchTable = {
						MM_LOG_DEBUG_NOTE: mmOurPlugin.logger.debug,
						MM_LOG_VERBOSE_NOTE: mmOurPlugin.logger.info,
						MM_LOG_TERSE_NOTE: mmOurPlugin.logger.info,
						MM_LOG_WARNING: mmOurPlugin.logger.warn,
						MM_LOG_ERROR: mmOurPlugin.logger.error,
						MM_LOG_FORCE_NOTE: mmOurPlugin.logger.info,
						MM_LOG_TIMESTAMP: mmOurPlugin.logger.info,
						MM_LOG_REPORT: mmOurPlugin.logger.info
						}


############################################################################################
#
#
# Initialization
#
#
############################################################################################
def init(logFileName, ourPlugin):

	global ourLoggerFile
	global mmOurPlugin


	mmOurPlugin = ourPlugin
	ourLoggerFile = logFileName
	initLoggerDispatchTable()
	setLogSensitivity(mmDefaultLogSensitivity)
	logForce( "--- Initializing mmLog")



def start():

	logForce( "--- Starting mmLog")
	verifyLogMode({'theCommand':'verifyLogMode'})

