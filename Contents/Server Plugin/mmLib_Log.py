############################################################################################
#
# mmLib_Log.py (Version 2.0)
#		This version uses an object for the logger based loosely on python login functionality
#		This replaces all functionality for  mmLib_Log.py maintaining all command compability
#		This version is slightly more performance enhanced, however if you need to look at
#		earlier code, the original is called mmLib_LogOld.py
#
# Error Log processing for MotionMap3
#
############################################################################################

import os.path
import sys
import os
import ntpath
import traceback
import datetime
import logging
import time
import mmLib_Low
try:
	import indigo
except:
	pass

##################################
# Constants
##################################

MAX_LOG_SIZE = 1024*1024
RESET_LOG_SIZE = 512*1024

# Log Levels in numeric order

LOG_NOTSET = 0
LOG_DEBUG_NOTE = 12
LOG_VERBOSE_NOTE = 13
LOG_TERSE_NOTE = 15
LOG_REPORT = 17
LOG_TIMESTAMP = 19
LOG_FORCE_GRAY_NOTE = 24
LOG_FORCE_NOTE = 25
LOG_WARNING = 35
LOG_ERROR = 45

# Log Level names

MM_LOG_NOTSET = "mmNotSet"
MM_LOG_DEBUG_NOTE = "mmDebug"
MM_LOG_VERBOSE_NOTE = "mmVrbse"
MM_LOG_TERSE_NOTE = "mmTerse"
MM_LOG_REPORT = "mmReprt"
MM_LOG_TIMESTAMP = "mmTStmp"
MM_LOG_FORCE_GRAY_NOTE = "mmForcG"
MM_LOG_FORCE_NOTE = "mmForce"
MM_LOG_WARNING = "mmWARNG"
MM_LOG_ERROR = "mmERROR"

logLevelDict =	{
				MM_LOG_NOTSET: LOG_NOTSET,
				MM_LOG_DEBUG_NOTE: LOG_DEBUG_NOTE,
				MM_LOG_VERBOSE_NOTE: LOG_VERBOSE_NOTE,
				MM_LOG_TERSE_NOTE: LOG_TERSE_NOTE,
				MM_LOG_REPORT: LOG_REPORT,
				MM_LOG_TIMESTAMP: LOG_TIMESTAMP,
				MM_LOG_FORCE_GRAY_NOTE: LOG_FORCE_GRAY_NOTE,
				MM_LOG_FORCE_NOTE: LOG_FORCE_NOTE,
				MM_LOG_WARNING: LOG_WARNING,
				MM_LOG_ERROR: LOG_ERROR
				}
# Jump table with default mmNullMessage

def mmNullMessage(msg): return

setLogSensitivity = mmNullMessage


logNull = mmNullMessage			# will never do anything... it never changes
logNotSet = mmNullMessage		# will always display this message regardles of loglevel setting
logDebug = mmNullMessage
logVerbose = mmNullMessage
logTerse = mmNullMessage
logReportLine = mmNullMessage
logTimestamp = mmNullMessage
logForceGray = mmNullMessage
logForce = mmNullMessage
logWarning = mmNullMessage
logError = mmNullMessage


logMsgFormatDict = {
	MM_LOG_NOTSET: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_DEBUG_NOTE: ' ',		# everything is in Type so the messaage will present gray
	MM_LOG_VERBOSE_NOTE: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_TERSE_NOTE: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_REPORT: '%(msg)s',
	MM_LOG_TIMESTAMP: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_FORCE_GRAY_NOTE: ' ',
	MM_LOG_FORCE_NOTE: '%(callingTime)s [%(levelname)s] %(msg)s : %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_WARNING: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_ERROR: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.'
}

logTypeFormatDict = {
	MM_LOG_NOTSET: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_DEBUG_NOTE: '%(ourLoggerName)s %(stackGraph)s %(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_VERBOSE_NOTE: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_TERSE_NOTE: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_REPORT: ' ',
	MM_LOG_TIMESTAMP: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_FORCE_GRAY_NOTE: '%(ourLoggerName)s %(stackGraph)s %(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_FORCE_NOTE: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_WARNING: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_ERROR: '%(ourLoggerName)s %(stackGraph)s'
}

##################################
# Module Global Variables
##################################


ourLoggerName = "LoggerName not Set"
ourLoggerFile = "LoggerFile not Set"
mmOurPlugin = 0
mmLogger = 0

currentNumericLogLevel = LOG_NOTSET
currentTextLogLevel = MM_LOG_NOTSET


# Eventually, we may log to the terminal, then we can support color

def prRed(skk): return ("\033[91m {}\033[00m" .format(skk))
def prGreen(skk): return ("\033[92m {}\033[00m" .format(skk))
def prCyan(skk): return ("\033[96m {}\033[00m" .format(skk))


class myLogger(logging.Logger):

	def __init__(self, name, level=MM_LOG_NOTSET):
		super(myLogger, self).__init__(name)
		self.setLevel(level)

	def setLevel(self,logLevelString):

		global logNotSet, logDebug, logVerbose, logTerse, logReportLine, logTimestamp, logForceGray, logForce, logWarning, logError, setLogSensitivity, logLevelDict, currentNumericLogLevel, currentTextLogLevel

		setLogSensitivity = self.setLevel

		numericVal = logLevelDict.get(logLevelString, 'Unknown')

		if numericVal == 'Unknown':
			self.emit(MM_LOG_NOTSET, "Error Setting Log Level to " + str(logLevelString) + ". Should be text based in set " + str(logLevelDict.keys()))
			return

		logNotSet = self.mmNotSet if LOG_NOTSET >= numericVal else mmNullMessage
		logDebug = self.mmDebug if LOG_DEBUG_NOTE >= numericVal else mmNullMessage
		logVerbose = self.mmVrbse if LOG_VERBOSE_NOTE >= numericVal else mmNullMessage
		logTerse = self.mmTerse if LOG_TERSE_NOTE >= numericVal else mmNullMessage
		logReportLine = self.mmReprt if LOG_REPORT >= numericVal else mmNullMessage
		logTimestamp = self.mmTStmp if LOG_TIMESTAMP >= numericVal else mmNullMessage
		logForceGray = self.mmForceGray if LOG_FORCE_GRAY_NOTE >= numericVal else mmNullMessage
		logForce = self.mmForce if LOG_FORCE_NOTE >= numericVal else mmNullMessage
		logWarning = self.mmWARNG if LOG_WARNING >= numericVal else mmNullMessage
		logError = self.mmERROR if LOG_ERROR >= numericVal else mmNullMessage

		currentNumericLogLevel = numericVal
		currentTextLogLevel = logLevelString
		#Call directly to emit so our stack frame represents the actual caller (not ourselves)
		self.emit(MM_LOG_NOTSET, "Log Level value now " + str(numericVal) + ", " + logLevelString)


	def emit(self, levelname, msg):

		newString = checkString(msg)
		if newString:
			msg = newString
			levelname = MM_LOG_ERROR

		theTrace = traceback.extract_stack()
		NestingDepth = max(0, min(len(theTrace) - 3, 21))
		callingFile, callingLine, callingProc, sourceCode = theTrace[NestingDepth]  # unpack the trace record to get calling routine etc.
		callingTime = str( datetime.datetime.now().strftime("%I:%M:%S %p"))

		valDict = {
						"ourLoggerName": ourLoggerName,
						"callingTime": callingTime,
						"levelname": levelname,
						"msg": msg,
						"filename": os.path.basename(callingFile),
						"funcName": callingProc,
						"lineno": callingLine,
						"stackGraph": '[{0:<22}]'.format(str('|' * NestingDepth) + str('.' * int(22 - NestingDepth)))
					}
		logMessage = logMsgFormatDict[levelname] % valDict
		logType = logTypeFormatDict[levelname] % valDict

		indigo.server.log(message=logMessage, type=logType, isError=levelname == MM_LOG_ERROR)

		return 0

	# log dispatch area

	def mmNotSet(self, msg):
		# Show everything
		self.emit(MM_LOG_NOTSET, msg)

	def mmDebug(self, msg):
		self.emit(MM_LOG_DEBUG_NOTE, msg)

	def mmVrbse(self, msg):
		self.emit(MM_LOG_VERBOSE_NOTE, msg)

	def mmTerse(self, msg):
		self.emit(MM_LOG_TERSE_NOTE, msg)

	# You probably dont want to set levels beyond this line. We should always accept report, force, warnings and errors.

	def mmReprt(self, msg):
		self.emit(MM_LOG_REPORT, msg)

	def mmTStmp(self, msg):
		ct = time.time()
		lt = time.localtime(ct)
		t = time.strftime("%Y-%m-%d %H:%M:%S", lt)
		timestampTime = "%s.%03d" % (t, (ct - long(ct)) * 1000)
		msg = timestampTime + " " + msg
		self.emit(MM_LOG_TIMESTAMP, msg)
		writeToLogFile(MM_LOG_TIMESTAMP, msg, 1, 0)

	def mmForceGray(self, msg):
		self.emit(MM_LOG_FORCE_GRAY_NOTE, msg)

	def mmForce(self, msg):
		self.emit(MM_LOG_FORCE_NOTE, msg)

	def mmWARNG(self, msg):
		self.emit(MM_LOG_WARNING, msg)
		writeToLogFile(MM_LOG_WARNING, msg, 1, 1)

	def mmERROR(self, msg):
		# Append Exception to msg if necessary
		excType, excValue, excTraceback = sys.exc_info()
		if excType == None:
			postScript = "No exception found"
		else:
			theTrace = traceback.extract_tb(excTraceback, 1)
			callingFile, callingLine, callingProc, sourceCode = theTrace[0]  # unpack the trace record
			postScript = str(str(excValue) + ". Exception @ " + str(os.path.basename(callingFile)) + "." + str(callingProc) + ":" + str(callingLine))

		# return and Indent postscript to align with Error Message
		msg = msg +"\n" + ' ' * 45 + postScript

		self.emit(MM_LOG_ERROR, msg)
		writeToLogFile(MM_LOG_ERROR, msg, 1, 1)

	def mmNullMessage(self, msg):
		return


def checkString(msg):
	# Returns 0 if the string is OK, otherwise returns a replacement string
	try:
		stringCheck = isinstance(msg, str)
	except:
		# this new exception will take priority over any previous exception. Here, we were handed a bad string,
		# so our original message would have thrown another exception anyway
		# Though I dont think it ever gets here.
		return ('##### String Exception #####')

	if not stringCheck:
		return ('##### String Type Error #####')

	return (0)


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

	# By Default we are only sending Errors, Warnings and Timestamps to the file

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


############################################################################################
#
#	setLogSensitivityMMCommand	Same Command as above, but used by Indigo Scripts through the executeMMCommand
#
############################################################################################

def setLogSensitivityMMCommand(theParameters):

	try:
		theNewValue = theParameters["TheValue"]
	except:
		logWarning("SetLogSensitivity cammand did not include \'TheValue\'")
		return(1)

	setLogSensitivity(str(theNewValue))

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

	varTextValue = mmLib_Low.getIndigoVariable('MMLoggingMode', MM_LOG_TERSE_NOTE)
	setLogSensitivity(str(varTextValue))	# typecast here because all indigo stuff is unicode



############################################################################################
# Initialization
############################################################################################
def init(logFileName, ourPlugin):

	global ourLoggerName
	global ourLoggerFile
	global mmOurPlugin
	global mmLogger


	ourLoggerName = "MotionMap3"
	ourLoggerFile = str(mmLib_Low.mmLogFolder + logFileName)
	indigo.server.log( "--- Setting mmLog file to " + str(ourLoggerFile))
	mmOurPlugin = ourPlugin
	mmLogger = myLogger(ourLoggerName)	#initialize our logger object

	mmLogger.setLevel(MM_LOG_TERSE_NOTE)	# default to Terse
	logForce( "--- Setting mmLog file to " + str(ourLoggerFile))

def start():

	logForce( "--- Starting mmLog")
	verifyLogMode({'theCommand':'verifyLogMode'})


