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


# Log types
MM_LOG_DEBUG_NOTE = 0
MM_LOG_VERBOSE_NOTE = 1
MM_LOG_TERSE_NOTE = 2
MM_LOG_WARNING = 3
MM_LOG_ERROR = 4
MM_LOG_FORCE_NOTE = 5
MM_LOG_TIMESTAMP = 6
MM_LOG_REPORT = 7

# Log Filtering - for mmLogSensitivity
MM_SHOW_EVERYTHING = 0
MM_SHOW_VERBOSE_NOTES = 1
MM_SHOW_TERSE_NOTES = 2
MM_SHOW_WARNINGS = 3
MM_SHOW_ERRORS = 4

# Log Mode Dictionary
logDict = {'debug': MM_SHOW_EVERYTHING, 'all': MM_SHOW_EVERYTHING,'verbose': MM_SHOW_VERBOSE_NOTES,'terse': MM_SHOW_TERSE_NOTES,'warnings': MM_SHOW_WARNINGS,'errors': MM_SHOW_ERRORS}
logDictReverse = ['all','verbose','terse','warnings','errors']

logTypeEnglish = ["mmDebug", "mmVNote", "mmTerse", "mmWARN ", "mmERROR", "mmNote ","mmTStmp", " "]

##################################
# Log Runtime Settings
##################################

mmLogFileName = "undefined"
mmDefaultLogSensitivity = MM_SHOW_TERSE_NOTES
mmLogSensitivity = 10	# Force actual setting in first call to SetSensitivity

indentList =   ['',\
				' ',\
				'  ',\
				'   ',\
				'    ',\
				'     ',\
				'      ',\
				'       ',\
				'        ',\
				'         ',\
				'          ',\
				'           ',\
				'            ',\
				'             ',\
				'              ',\
				'               ',\
				'                ',\
				'                 ',\
				'                  ',\
				'                   ',\
				'                    ',\
				'                    +']



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
# 		MM_SHOW_EVERYTHING = 0			Show Everything
# 		MM_SHOW_VERBOSE_NOTES = 1		Show Many things
# 		MM_SHOW_TERSE_NOTES = 2			Show some things
# 		MM_SHOW_WARNINGS = 3			Show Warnings and Errors
# 		MM_SHOW_ERRORS = 4				Show Only Warnings
#
#	Note MotionMap always shows logForce, logTimestamp, and logReportLine for Program Functionality
#
#############################################################################################

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
	global logSensitivityKeys

	if mmLogSensitivity != newVal:
		mmLogSensitivity = newVal


		newSettings = logSensitivityMap[logSensitivityKeys[newVal]]

		logDebug = newSettings[0]
		logVerbose = newSettings[1]
		logTerse = newSettings[2]
		logWarning = newSettings[3]
		logError = newSettings[4]
		logForce = newSettings[5]
		logTimestamp = newSettings[6]
		logReportLine = newSettings[7]

		indigo.server.log("  Log Sensitivity is now: " + logDictReverse[mmLogSensitivity])

		# Update The indigo Variable too

		mmLib_Low.setIndigoVariable('MMLoggingMode', logDictReverse[mmLogSensitivity])


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
		indigo.server.log("SetLogSensitivity cammand did not include \'TheValue\'")
		return(1)
	try:
		intValue = logDict[theNewValue]
	except:
		indigo.server.log("SetLogSensitivity invalid value for \'TheValue\'. Try one of these")
		indigo.server.log(str(logDict))
		return(1)

	setLogSensitivity(intValue)

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
	theCommandParameters = {'theCommand':'SetLogSensitivity', 'TheValue':varTextValue}
	setLogSensitivityMMCommand(theCommandParameters)




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
#
#	writeTimeStamp	Write a timestamp to the log file
#
def writeTimeStamp(logType, logMessage):
	return(writeToLogFile(logType, logMessage, 1, 0))


#
#	writeTracelog	Write a traceback to the log file
#
def writeTracelog(logType, logMessage):
	return(writeToLogFile(logType, logMessage, 1, 1))


#
#	showPrefix	preppend a prefix to the log message (displays in the event log only)
#
def showPrefix(logType, logMessage):
	if logType == MM_LOG_WARNING:
		prefix = "WARNING (Check " + mmLogFileName + " for stack crawl): "
	elif logType == MM_LOG_ERROR:
		prefix = "ERROR (Check " + mmLogFileName + " for details): "

	return (prefix + logMessage)


#
#	addContext	Preppend caller context information to the log entry
#
def addContext(logType, logMessage):
	theTrace = traceback.extract_stack()
	NestingDepth = len(theTrace) - 5

	if NestingDepth < 0:
		NestingDepth = 0
	elif NestingDepth > 20:
		NestingDepth = 21
	aLine = theTrace[len(theTrace) - 5]

	fileName = os.path.basename(str(aLine[0]) + "." + str(aLine[2]) + ":" + str(aLine[1]))
	prefix = indentList[NestingDepth] + str(aLine[2]) + ":"
	logMessage = str(prefix + logMessage + " " + "(" + fileName + ")")

	return (logMessage)


#
#	displayMessage	Show the supplied log message in the Event Log
#
def displayMessage(logType, logMessage):

	if logType != MM_LOG_REPORT:
		theDateTime = datetime.datetime.now().strftime("%I:%M:%S %p") + " "
		mmOurPlugin.dispatchLog(logMessage, logTypeEnglish[logType] + " " + theDateTime, logType)
	else:
		mmOurPlugin.dispatchLog(logMessage, " ", logType)

	return (logMessage)


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
	return(write(MM_LOG_DEBUG_NOTE, logMessage))


#	mmVerboseNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_VERBOSE_NOTES
#
def mmVerboseNote(logMessage):
	return(write(MM_LOG_VERBOSE_NOTE, logMessage))


#	mmTerseNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_TERSE_NOTES
#
def mmTerseNote(logMessage):
	return(write(MM_LOG_TERSE_NOTE, logMessage))


#	mmWarning - only show the message provided if mmLogSensitivity is set to MM_SHOW_WARNINGS, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmWarning(logMessage):
	return(write(MM_LOG_WARNING, logMessage))


#	mmError - only show the message provided if mmLogSensitivity is set to MM_SHOW_ERRORS, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmError(logMessage):
	return(write(MM_LOG_ERROR, logMessage))


#	mmForceNote - show the message provided in all cases
#
def mmForceNote(logMessage):
	return(write(MM_LOG_FORCE_NOTE, logMessage))

#	mmPrintReportLine - show the message provided in all cases
#
def mmPrintReportLine(logMessage):
	return(write(MM_LOG_REPORT, logMessage))

#	mmTimestamp - show the message provided in all cases, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmTimestamp(logMessage):
	return(write(MM_LOG_TIMESTAMP, logMessage))

#												logDebug,		logVerbose,		logTerse,		logWarning,	logError,	logForce,		logTimestamp,	logReportLine
logSensitivityMap = {
					"MM_SHOW_EVERYTHING": 		[mmDebugNote,	mmVerboseNote,	mmTerseNote,	mmWarning,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine],
					"MM_SHOW_VERBOSE_NOTES":	[mmLogNone,		mmVerboseNote,	mmTerseNote,	mmWarning,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine],
					"MM_SHOW_TERSE_NOTES":		[mmLogNone,		mmLogNone,		mmTerseNote,	mmWarning,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine],
					"MM_SHOW_WARNINGS":			[mmLogNone,		mmLogNone,		mmLogNone,		mmWarning,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine],
					"MM_SHOW_ERRORS":			[mmLogNone,		mmLogNone,		mmLogNone,		mmLogNone,	mmError,	mmForceNote,	mmTimestamp,	mmPrintReportLine]}


logSensitivityKeys = ["MM_SHOW_EVERYTHING","MM_SHOW_VERBOSE_NOTES","MM_SHOW_TERSE_NOTES","MM_SHOW_WARNINGS","MM_SHOW_ERRORS"]


############################################################################################
#
#
#  logProcX	The Jump Table for all log types. You can adjust the functionality of all logging functions by manipulating this table
#
# MM_LOG_FORCE_NOTE			Use Sparingly... Its Never Masked. This note will always be shown
#	MM_LOG_TIMESTAMP			Use More Sparingly... Its Never Masked. This note will always be shown. Same as above, but writes a timestamp into the log file too
#	MM_LOG_REPORT				Used for user-requested reports. Its never masked. Excludes all prefix and context information (to show a cleaner display)
#	MM_LOG_DEBUG_NOTE			USE Discretion... Even though this note will only be shown in MM_SHOW_EVERYTHING Mode, its CPU Intensive, as it writes log, time, and stack info to the file
#	MM_LOG_VERBOSE_NOTE			Use somewhat sparingly... is only masked by MM_SHOW_TERSE_NOTES, MM_SHOW_WARNINGS, and MM_SHOW_ERRORS modes. Only writes messages to the Event Log
#	MM_LOG_TERSE_NOTE			Good choice for FYI while coding its only masked by MM_SHOW_WARNINGS, and MM_SHOW_ERRORS modes. Only writes messages to the Event Log
#	MM_LOG_WARNING				Should only be used when an unusual thing happens but we can still continue. Writes to Log file. Only Masked by MM_LOG_ERROR mode
#	MM_LOG_ERROR				Should only be used when a catastrophic problem occurs. Writes to Log file. Is NEVER masked
#
#############################################################################################
logProcX = {
	"MM_LOG_FORCE_NOTE": [addContext, displayMessage],
	"MM_LOG_TIMESTAMP": [writeTimeStamp, addContext, displayMessage],
	"MM_LOG_REPORT": [displayMessage],
	"MM_LOG_DEBUG_NOTE": [showPrefix, addContext, writeTracelog, displayMessage],
	"MM_LOG_VERBOSE_NOTE": [addContext, displayMessage],
	"MM_LOG_TERSE_NOTE": [addContext, displayMessage],
	"MM_LOG_WARNING": [showPrefix, addContext, writeTracelog, displayMessage],
	"MM_LOG_ERROR": [showPrefix, addContext, writeTracelog, displayMessage],
}

logSubFunctionKeys = ["MM_LOG_DEBUG_NOTE", "MM_LOG_VERBOSE_NOTE", "MM_LOG_TERSE_NOTE", "MM_LOG_WARNING", "MM_LOG_ERROR",
					  "MM_LOG_FORCE_NOTE", "MM_LOG_TIMESTAMP", "MM_LOG_REPORT"]


#
#	writeX	Do all the actions necessary for this log mode
#
def write(logType, logMessage):
	theProcList = logProcX[logSubFunctionKeys[logType]]
	#modifiedMessage = logMessage

	for i in range(0, len(theProcList) ):
		# Give each module above in logProcX a chance to manipulate the message... logProcX's final entry is always displayMessage (it actually displays the final logMessage)
		logMessage = theProcList[i](logType, logMessage)


def	logForceX(logMessage):
	logMessage = addContext(MM_LOG_FORCE_NOTE,logMessage)
	displayMessage(MM_LOG_FORCE_NOTE,logMessage)


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
	ourPlugin.initLogger()
	setLogSensitivity(mmDefaultLogSensitivity)
	logForce( "--- Initializing mmLog")

def start():

	logForce( "--- Starting mmLog")
	verifyLogMode({'theCommand':'verifyLogMode'})

