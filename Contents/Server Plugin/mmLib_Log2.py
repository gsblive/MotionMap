############################################################################################
#
# mmLib_Log.py
# Error Log processing for MotionMap2
#
############################################################################################

import sys
import os.path
import os
import traceback
import logging
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
import time
import mmLib_Log

##################################
# Constants
##################################


LOG_NOTSET = 0
LOG_CLASSIC_DEBUG = 10
LOG_DEBUG_NOTE = 12
LOG_VERBOSE_NOTE = 13
LOG_TERSE_NOTE = 15
LOG_REPORT = 17
LOG_TIMESTAMP = 19
LOG_FORCE_NOTE = 25
LOG_WARNING = 35
LOG_ERROR = 45


MM_LOG_NOTSET = "mmNotSet"
MM_LOG_CLASSIC_DEBUG = "mmClasD"
MM_LOG_DEBUG_NOTE = "mmDebug"
MM_LOG_TIMESTAMP = "mmTStmp"
MM_LOG_VERBOSE_NOTE = "mmVrbse"
MM_LOG_TERSE_NOTE = "mmTerse"
MM_LOG_REPORT = "mmReprt"
MM_LOG_FORCE_NOTE = "mmForce"
MM_LOG_WARNING = "mmWARNG"
MM_LOG_ERROR = "mmERROR"



logLevelNameDict = {
	LOG_NOTSET: MM_LOG_NOTSET,
	LOG_CLASSIC_DEBUG: MM_LOG_CLASSIC_DEBUG,
	LOG_DEBUG_NOTE: MM_LOG_DEBUG_NOTE,
	LOG_TIMESTAMP: MM_LOG_TIMESTAMP,
	LOG_VERBOSE_NOTE: MM_LOG_VERBOSE_NOTE,
	LOG_TERSE_NOTE: MM_LOG_TERSE_NOTE,
	LOG_REPORT: MM_LOG_REPORT,
	LOG_FORCE_NOTE: MM_LOG_FORCE_NOTE,
	LOG_WARNING: MM_LOG_WARNING,
	LOG_ERROR: MM_LOG_ERROR
}

logMsgFormatDict = {
	MM_LOG_NOTSET: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_CLASSIC_DEBUG: '%(callingTime)s [%(levelname)s] %(msg)s (%(filename)s.%(funcName)s:%(lineno)d)',
	MM_LOG_DEBUG_NOTE: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_TIMESTAMP: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_VERBOSE_NOTE: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_TERSE_NOTE: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_REPORT: '%(msg)s',
	MM_LOG_FORCE_NOTE: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_WARNING: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.',
	MM_LOG_ERROR: '%(callingTime)s [%(levelname)s] %(msg)s. %(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d.'
}

logTypeFormatDict = {
	MM_LOG_NOTSET: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_CLASSIC_DEBUG: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_DEBUG_NOTE: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_TIMESTAMP: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_VERBOSE_NOTE: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_TERSE_NOTE: '%(ourLoggerName)s %(stackGraph)s',
	MM_LOG_REPORT: ' ',
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

# print(message="Welcome to MotionMap", type="Warning", isError=0)


class myLogHandler(logging.Handler, object):

	global ourLoggerName

	def __init__(self, displayName, level=logging.NOTSET):
		super(myLogHandler, self).__init__(level)
		self.displayName = displayName

	def emit(self, record):

		newString = checkString(record.msg)
		if newString:
			record.msg = newString
			record.levelname = MM_LOG_ERROR

		theTrace = traceback.extract_stack()
		NestingDepth = max(0, min(len(theTrace) - 7, 21))
		callingFile, callingLine, callingProc, sourceCode = theTrace[NestingDepth]  # unpack the trace record to get calling routine etc.
		callingTime = str( datetime.datetime.now().strftime("%I:%M:%S %p"))

		valDict = { "ourLoggerName": ourLoggerName,
					"callingTime":callingTime,
					"levelname":record.levelname,
					"msg":record.msg,
					"filename":os.path.basename(callingFile),
					"funcName":callingProc,
					"lineno":callingLine,
					"stackGraph":'[{0:<22}]'.format(str('|' * NestingDepth) + str('.' * int(22 - NestingDepth)))
					}
		logMessage = logMsgFormatDict[record.levelname] % valDict
		logType = logTypeFormatDict[record.levelname] % valDict

		indigo.server.log(message=logMessage, type=logType, isError=record.levelname == MM_LOG_ERROR)

class myLogger(logging.Logger):

	def __init__(self, name, level=logging.NOTSET):
		super(myLogger, self).__init__(name)

	# log dispatch area

	def mmNotSet(self, msg, *args, **kwargs):
		# Show everything
		self._log(LOG_NOTSET, msg, args, **kwargs)

	def mmClasD(self, msg, *args, **kwargs):
		if self.isEnabledFor(MM_LOG_CLASSIC_DEBUG):
			self._log(LOG_CLASSIC_DEBUG, msg, args, **kwargs)

	def mmDebug(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_DEBUG_NOTE):
			self._log(LOG_DEBUG_NOTE, msg, args, **kwargs)

	def mmTStmp(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_TIMESTAMP):
			ct = time.time()
			lt = time.localtime(ct)
			t = time.strftime("%Y-%m-%d %H:%M:%S", lt)
			timestampTime = "%s.%03d" % (t, (ct - long(ct)) * 1000)
			msg = timestampTime + " " + msg
			self._log(LOG_TIMESTAMP, msg, args, **kwargs)

	def mmVrbse(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_VERBOSE_NOTE):
			self._log(LOG_TERSE_NOTE, msg, args, **kwargs)

	def mmTerse(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_TERSE_NOTE):
			self._log(LOG_TERSE_NOTE, msg, args, **kwargs)

	# You probably dont want to set levels beyond this line. We should always accept report, force, warnings and errors.

	def mmReprt(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_REPORT):
			self._log(LOG_REPORT, msg, args, **kwargs)

	def mmForce(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_FORCE_NOTE):
			#newString = self.checkString(msg)
			#if newString:
			#	msg = newString
			self._log(LOG_FORCE_NOTE, msg, args, **kwargs)

	def mmWARNG(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_WARNING):
			self._log(LOG_WARNING, msg, args, **kwargs)

	def mmERROR(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_ERROR):
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

			self._log(LOG_ERROR, msg, args, kwargs)

	def mmNullMessage(self, msg, *args, **kwargs):
		return


		return(0)


def checkString(msg):
	# Returns 0 if the string is OK, otherwise returns a replacement string
	try:
		stringCheck = isinstance(msg, str)
	except Exception as exception:
		# this new exception will take priority over any previous exception. Here, we were handed a bad string,
		# so our original message would have thrown another exception anyway
		# Though I dont think it ever gets here.
		return ('##### String Exception #####')

	if not stringCheck:
		return ('##### String Type Error #####')

	return(0)


############################################################################################
#
#
# Initialization
#
#
############################################################################################
def init(logFileName, ourPlugin):

	global ourLoggerName
	global ourLoggerFile
	global mmOurPlugin
	global mmLogger

	ourLoggerName = "MotionMap3"
	ourLoggerFile = "mm3Log.txt"
	mmOurPlugin = ourPlugin
	mmLogger = myLogger(ourLoggerName)

	for level, levelName in logLevelNameDict.items():
		logging.addLevelName(level, levelName)


	mmLogHandler = myLogHandler("mm3LogHandler")
	# Setup the default formatter. Note: fmt is usually overridden in emit()
	# mmLogHandler.setFormatter(logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(message)s (%(filename)s.%(funcName)s:%(lineno)d) ',datefmt="%I:%M:%S %p"))
	mmLogger.addHandler(mmLogHandler)

	#testSuite()

	mmLogger.setLevel(LOG_TERSE_NOTE)	# default to Terse

	############################################################################################
	# Test code
	############################################################################################

def testSuite():

	mmLogger.setLevel(LOG_NOTSET)
	mmLogger.mmForce("###### Sample Force Message ######")
	mmLogger.mmDebug("###### Sample debug Message ######")
	mmLogger.mmReprt("\n========= Sample Report =========\nBlah\nBlah\nBlah\n========= End of Report =========\n")
	mmLogger.mmERROR("###### Sample error Message ######")

	# Performance tests comparative to original mmLib_Log

	mmLogger.setLevel(LOG_TIMESTAMP)
	mmLogger.mmTStmp("###### Start Timer")
	for x in range(1,10000):
		mmLogger.mmTerse("Placeholder")
	mmLogger.mmTStmp("###### End Timer")

	mmLogger.mmTStmp("###### Start Timer 2")
	for x in range(1,10000):
		mmLib_Log.logVerbose("Placeholder")
	mmLogger.mmTStmp("###### End Timer 2")

	mmLogger.mmTStmp("###### Start Timer 3")
	for x in range(1,10000):
		mmLogger.mmNullMessage("Placeholder")
	mmLogger.mmTStmp("###### End Timer 3")

	try:
		x = 1/0
	except:
		mmLogger.mmERROR("###### EXCEPTION error Message ######")

	mmLogger.mmForce(getZero())
	#mmLogger.mmForce("###### This is a force direct string exception ######" + getZero())
	mmLogger.mmForce("###### This is force mesage")

	mmLogger.mmForce("###### This is force mesage 2")

	#End Test
	mmLogger.setLevel(LOG_TERSE_NOTE)	# default to Terse

	#doTest()

def getZero():
	return(0)

def testLevel(theLevel):
	mmLogger.setLevel(theLevel)

	indigo.server.log('====================')
	indigo.server.log('== New Level: '+ logLevelNameDict[theLevel] + ' ==')
	indigo.server.log('====================')

	for level,levelName in logLevelNameDict.items():
		s = 'mmLogger.%(levelName)s(\"This is an %(levelName)s note\")' % {"levelName": levelName}
		eval(s)

def	doTest():
	indigo.server.log( "### doTest A ###")
	testLevel(LOG_NOTSET)
	testLevel(LOG_CLASSIC_DEBUG)
	testLevel(LOG_DEBUG_NOTE)
	testLevel(LOG_TIMESTAMP)
	testLevel(LOG_VERBOSE_NOTE)
	testLevel(LOG_TERSE_NOTE)
	testLevel(LOG_REPORT)
	testLevel(LOG_FORCE_NOTE)
	testLevel(LOG_WARNING)
	testLevel(LOG_ERROR)

