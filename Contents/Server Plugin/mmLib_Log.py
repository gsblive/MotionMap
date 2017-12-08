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
MM_LOG_FORCE = 5
MM_LOG_TIMESTAMP = 5

# Log Filtering - for mmLogSensitivity
MM_SHOW_EVERYTHING = 0
MM_SHOW_VERBOSE_NOTES = 1
MM_SHOW_TERSE_NOTES = 2
MM_SHOW_WARNINGS = 3
MM_SHOW_ERRORS = 4

# Log Mode Dictionary
logDict = {'debug': MM_SHOW_EVERYTHING, 'all': MM_SHOW_EVERYTHING,'verbose': MM_SHOW_VERBOSE_NOTES,'terse': MM_SHOW_TERSE_NOTES,'warnings': MM_SHOW_WARNINGS,'errors': MM_SHOW_ERRORS}

##################################
# Log Runtime Settings
##################################

mmLogFileName = "undefined"
mmDefaultLogSensitivity = MM_SHOW_TERSE_NOTES
mmLogSensitivity = 10		# unusual iunitial setting to make sure setLogSensitivity() initializes in the first pass

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


########################################
#  Message/Log routines
########################################


########################################
#
# mmDebugNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_EVERYTHING
#
def mmDebugNote(logMessage):
	return(write(MM_LOG_DEBUG_NOTE, logMessage))


########################################
#
#	mmVerboseNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_VERBOSE_NOTES
#
def mmVerboseNote(logMessage):
	return(write(MM_LOG_VERBOSE_NOTE, logMessage))


########################################
#
#	mmTerseNote - only show the message provided if mmLogSensitivity is set to MM_SHOW_TERSE_NOTES
#
def mmTerseNote(logMessage):
	return(write(MM_LOG_TERSE_NOTE, logMessage))


########################################
#
#	mmWarning - only show the message provided if mmLogSensitivity is set to MM_SHOW_WARNINGS, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmWarning(logMessage):
	return(write(MM_LOG_WARNING, logMessage))


########################################
#
#	mmError - only show the message provided if mmLogSensitivity is set to MM_SHOW_ERRORS, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmError(logMessage):
	return(write(MM_LOG_ERROR, logMessage))


########################################
#
#	mmForceNote - only show the message provided in all cases
#
def mmForceNote(logMessage):
	return(write(MM_LOG_FORCE, logMessage))


########################################
#
#	mmTimestamp - only show the message provided in all cases, also place a debugInfo/stackcrawl and timestamp into the log file
#
def mmTimestamp(logMessage):
	return(write(MM_LOG_TIMESTAMP, logMessage))

########################################
#
#	mmLogNone
#
def mmLogNone(logMessage):
	pass


########################################
########################################
#
#  Logging JumpTable - These are used as the logging entry points for the routines below
#
#  	use this as so:  if logDebug: logDebug
#
#  we do this so we dont have to dispatch to the Write() routine if nothing is going to
# be printed anyway (this makes the code more efficient)
#
# ########################################
# ########################################

logDebug = mmDebugNote
logVerbose = mmVerboseNote
logTerse = mmTerseNote
logWarning = mmWarning
logError = mmError
logForce = mmForceNote
logTimestamp = mmTimestamp

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
	return(mmLogSensitivity)

############################################################################################
#
# setLogSensitivity
#
#	accepts:
# 		MM_SHOW_EVERYTHING = 0
# 		MM_SHOW_VERBOSE_NOTES = 1
# 		MM_SHOW_TERSE_NOTES = 2
# 		MM_SHOW_WARNINGS = 3
# 		MM_SHOW_ERRORS = 4
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

	if mmLogSensitivity != newVal:
		mmLogSensitivity = newVal

		if MM_LOG_DEBUG_NOTE >= mmLogSensitivity: logDebug = mmDebugNote
		else:logDebug = mmLogNone
		if MM_LOG_VERBOSE_NOTE >= mmLogSensitivity: logVerbose = mmVerboseNote
		else:logVerbose = mmLogNone
		if MM_LOG_TERSE_NOTE >= mmLogSensitivity: logTerse = mmTerseNote
		else:logTerse = mmLogNone
		if MM_LOG_WARNING >= mmLogSensitivity: logWarning = mmWarning
		else:logWarning = mmLogNone
		if MM_LOG_ERROR >= mmLogSensitivity: logError = mmError
		else:logError = mmLogNone
		if MM_LOG_FORCE >= mmLogSensitivity: logForce = mmForceNote
		else:logForce = mmLogNone
		if MM_LOG_TIMESTAMP >= mmLogSensitivity: logTimestamp = mmTimestamp
		else:logTimestamp = mmLogNone
		indigo.server.log("  Log Sensitivity is now:" + str(mmLogSensitivity))
#	else:
#		indigo.server.log("  No change in Log Sensitivity:" + str(mmLogSensitivity))

	return(mmLogSensitivity)

############################################################################################
#
# trimFile
#
# Used to trim the logfile
#
#############################################################################################
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

	global mmLogSensitivity
	global logDebug
	global logVerbose
	global logTerse
	global logWarning
	global logError
	global logForce
	global logTimestamp

	try:
		currentLoggingModeString = indigo.variables['MMLoggingMode'].value
	except:
		indigo.server.log(">>> Indigo variable  \'MMLoggingMode\' does not exist... creating it and setting it to \'terse\' mode.")
		currentLoggingModeString = indigo.variable.create('MMLoggingMode', "terse")

	try:
		mmNewLogSensitivity = int(logDict[currentLoggingModeString])
	except:
		indigo.server.log(">>> Illegal log mode \'" + str(indigo.variables['MMLoggingMode'].value) + "\', using default of \'terse\'")
		indigo.server.log(">>>   Use \'debug\' \'all\' \'verbose\' \'terse\' \'warnings\' and \'errors\'")
		mmNewLogSensitivity = MM_SHOW_TERSE_NOTES
		indigo.variable.updateValue('MMLoggingMode', "terse")

	setLogSensitivity(mmNewLogSensitivity)


############################################################################################
#
# write
#
# Append mmMessage to the indigo log or MotionMap.err.txt file as directed by logType
#
# MotionMap system can be in the following modes as directed by global mmLogSensitivity:
#
#	logType					Priority	Behavior
#	MM_LOG_DEBUG_NOTE		    1		Append to log entry mmLogSensitivity >= MM_SHOW_EVERYTHING (you rarely want to see this)
#	MM_LOG_VERBOSE_NOTE		    1		Append to log entry mmLogSensitivity >= MM_SHOW_VERBOSE_NOTES
#	MM_LOG_TERSE_NOTE			2		Append to log entry mmLogSensitivity >= MM_SHOW_TERSE_NOTES
#	MM_LOG_WARNING				3		Append to log entry mmLogSensitivity >= MM_SHOW_WARNINGS
#	MM_LOG_ERROR				4		Append to log entry AND place stack trace in MotionMap.err.txt if mmLogSensitivity >= MM_SHOW_ERRORS
#	MM_LOG_FORCE				5		Append to log no matter what.
#
# logType = display the message if mmLogSensitivity Priority level is greater or equal to the logType provided
# logMessage = the message to display
#
############################################################################################
def write(logType, logMessage):

	global mmLogSensitivity

	prefix = ""

	if logType == MM_LOG_WARNING or logType == MM_LOG_ERROR or logType == MM_LOG_TIMESTAMP:
		f=open(mmLogFileName, 'a')
		theDateTime = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
		if logType == MM_LOG_WARNING:
			prefix = "WARNING (Check " + mmLogFileName + " for stack crawl): "
			f.write( theDateTime + " WARNING: " + logMessage  + '\n')
			traceback.print_stack(f=None, limit=None, file=f)
		elif logType == MM_LOG_ERROR:
			prefix = "ERROR (Check " + mmLogFileName + " for details): "
			f.write(theDateTime + " ERROR: " + logMessage  + '\n')
			traceback.print_exc(limit=None, file=f)
		else:
			f.write("==============================================================" + '\n' + "=" + '\n')
			f.write("=      Timestamp " + theDateTime + '\n')
			f.write("=      Message: " + logMessage  + '\n' + "=" + '\n')
			f.write("==============================================================" + '\n')
		f.write('\n\n\n')
		f.close()
		if os.path.getsize(mmLogFileName)  > MAX_LOG_SIZE:trimFile(mmLogFileName,RESET_LOG_SIZE)

	# Indent the message to keep track of recursion

	theTrace = traceback.extract_stack()
	NestingDepth = len(theTrace)-4
	if NestingDepth < 0:
		#indigo.server.log( "nestingdepth below 0. original length: " + str(len(theTrace)))
		NestingDepth=0
	elif NestingDepth >20:
		NestingDepth=21
	aLine = theTrace[len(theTrace)-3]

	fileName = os.path.basename(str(aLine[0]) + "." + str(aLine[2]) + ":" + str(aLine[1]))
	prefix = indentList[NestingDepth] + str(aLine[2]) + ":" + prefix
	indigo.server.log(str(prefix + logMessage + " " + "(" + fileName + ")"))
	return(0)




############################################################################################
#
#
# Initialization
#
#
############################################################################################
def init(logFileName):

	global mmLogFileName
 
	mmLogFileName = logFileName
	setLogSensitivity(mmDefaultLogSensitivity)
	logTimestamp( "--- Initializing mmLog")

def start():

	logTimestamp( "--- Starting mmLog")
	verifyLogMode({'theCommand':'verifyLogMode'})

