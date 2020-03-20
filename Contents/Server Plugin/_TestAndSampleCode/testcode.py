import time
from timeit import default_timer as timer

import DictionaryBasedQueueCode
import IndexBasedQueueCode
from collections import deque
import sys
import os.path
import socket
import platform
import random
import bisect
import os
import pickle
import inspect
import timeit
import traceback
import datetime
import ntpath
import ast
from timeit import default_timer as timer
from time import gmtime, strftime
import datetime
import subprocess

import random
import logging

#====================================
#============  Main  ================
#====================================

print "%I:%M:%S %p"
exit()

LOG_NOTSET = 0
LOG_CLASSIC_DEBUG = 10
LOG_DEBUG_NOTE = 12
LOG_TIMESTAMP = 13
LOG_VERBOSE_NOTE = 14
LOG_TERSE_NOTE = 16
LOG_REPORT = 19
LOG_FORCE_NOTE = 25
LOG_WARNING = 35
LOG_ERROR = 45


MM_LOG_NOTSET = "mmNotSet"
MM_LOG_CLASSIC_DEBUG = "mmClasD"
MM_LOG_DEBUG_NOTE = "mmDebug"
MM_LOG_TIMESTAMP = "mmTStmp"
MM_LOG_VERBOSE_NOTE = "mmVrbse"
MM_LOG_TERSE_NOTE = "mmTerse"
MM_LOG_REPORT = "MMReprt"
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



# print(message="Welcome to MotionMap", type="Warning", isError=0)


class myLogHandler(logging.Handler, object):

	def __init__(self, displayName, level=logging.NOTSET):
		super(myLogHandler, self).__init__(level)
		self.displayName = displayName

	def emit(self, record):
		theTrace = traceback.extract_stack()
		#NestingDepth = max(0, min(len(theTrace) - 3, 21))
		NestingDepth = max(0, min(len(theTrace) - 7, 21))	# for TestCode.c
		#NestingDepth = 1
		callingFile, callingLine, callingProc, sourceCode = theTrace[NestingDepth]  # unpack the trace record for the call to mmLib_Log

		record.filename = os.path.basename(callingFile)
		record.funcName = callingProc
		record.lineno = callingLine
		record.stackDepth = '[{0:<22}]'.format(str('|' * NestingDepth) + str('.' * int(22 - NestingDepth)))
		print("MotionMap3 " + self.format(record))

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
			self._log(LOG_TIMESTAMP, msg, args, **kwargs)

	def mmVrbse(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_VERBOSE_NOTE):
			self._log(LOG_TERSE_NOTE, msg, args, **kwargs)

	def mmTerse(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_TERSE_NOTE):
			self._log(LOG_TERSE_NOTE, msg, args, **kwargs)

	# You probably dont want to set levels beyond this line. We should always accept report, force, warnings and errors.

	def MMReprt(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_REPORT):
			self._log(LOG_REPORT, msg, args, **kwargs)

	def mmForce(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_FORCE_NOTE):
			self._log(LOG_FORCE_NOTE, msg, args, **kwargs)

	def mmWARNG(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_WARNING):
			self._log(LOG_WARNING, msg, args, **kwargs)

	def mmERROR(self, msg, *args, **kwargs):
		if self.isEnabledFor(LOG_ERROR):
			self._log(LOG_ERROR, msg, args, **kwargs)



mmLogger = myLogger("MotionMapLogger")
for level,levelName in logLevelNameDict.items():
	logging.addLevelName(level, levelName)
	#print('adding level %(levelS)s with levelName of %(levelName)s' % {"levelS":str(level),"levelName":levelName})

mmLogHandler = myLogHandler("MotionMap3")

#mmLogHandler.setFormatter(logging.Formatter('%(stackDepth)s %(asctime)s %(levelname)s: %(message)s (%(funcName)s,%(lineno)d)'))
mmLogHandler.setFormatter(logging.Formatter(fmt='%(stackDepth)s %(asctime)s [%(levelname)s] %(message)s (%(filename)s.%(funcName)s:%(lineno)d) ',datefmt="%I:%M:%S %p"))
mmLogger.addHandler(mmLogHandler)


# Test code

def testLevel(theLevel):
	mmLogger.setLevel(theLevel)

	print '\n===================='
	print '== New Level: '+ logLevelNameDict[theLevel] + ' =='
	print '====================\n'

	mmLogger.mmForce("Inside Testlevel.")

	for level,levelName in logLevelNameDict.items():
		s = 'mmLogger.%(levelName)s(\"This is an %(levelName)s note\")' % {"levelName": levelName}
		eval(s)

def OneDeep(theStr):
	mmLogger.mmForce(theStr)

def TwoDeep(theStr):
	OneDeep(theStr)

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

print '\n===================='
print '== Stack Crawl test =='
print '====================\n'

mmLogger.setLevel(LOG_NOTSET)
mmLogger.mmForce("Testing from Main.")
OneDeep("Testing from onedeep")
TwoDeep("Testing from TwoDeep")

exit()


	mmOurPlugin.logger.info("\n\nTesting Info method\n")

	if 0:
		try:
			logTerse = IndigoLogHandlerTerse(_MotionMapPlugin.MM_NAME)
			logTerse.setLevel(logging.LOG_TERSE_NOTE)
			logTerse.setFormatter('%(asctime)s %(levelname)s %(message)s')
			ourPlugin.logger.addHandler(logTerse)
			logging.addLevelName(LOG_TERSE_NOTE, MM_LOG_TERSE_NOTE)

			logVerbose = IndigoLogHandlerVerbose(_MotionMapPlugin.MM_NAME)
			logVerbose.setLevel(logging.LOG_VERBOSE_NOTE)
			logVerbose.setFormatter('%(asctime)s %(levelname)s %(message)s')
			ourPlugin.logger.addHandler(logVerbose)
			logging.addLevelName(LOG_VERBOSE_NOTE, MM_LOG_VERBOSE_NOTE)
		except:
			indigo.server.log("###Error getting indigo_log_handler")

		logTerse._log(LOG_TERSE_NOTE, "This is a terse note")
		logVerbose._log(LOG_VERBOSE_NOTE, "This is a verbose note")

# indigo.server.log(message="Welcome to MotionMap", type="Warning", isError=0)

class IndigoLogHandler(logging.Handler, object):

	logLevelNameDict = {
		logging.DEBUG:MM_LOG_DEBUG_NOTE,
		LOG_DEBUG_NOTE:MM_LOG_DEBUG_NOTE,
		LOG_VERBOSE_NOTE:MM_LOG_VERBOSE_NOTE,
		LOG_TERSE_NOTE:MM_LOG_TERSE_NOTE,
		LOG_WARNING:MM_LOG_WARNING,
		LOG_ERROR:MM_LOG_ERROR,
		LOG_FORCE_NOTE:MM_LOG_FORCE_NOTE,
		LOG_TIMESTAMP:MM_LOG_TIMESTAMP,
		LOG_REPORT:MM_LOG_REPORT
	}

	def __init__(self, displayName, level=logging.NOTSET):
		super(IndigoLogHandler, self).__init__(level)
		self.displayName = displayName
		#indigo.server.log("   Init IndigoLogHandler with displayName of: " + str(displayName))
		#< LogRecord: MotionMap3, 20, plugin.py, 141, "Initializing python %s, version=%s" >\

		#for level,levelName in self.logLevelNameDict.items():
		#	logging.addLevelName(level, levelName)

		indigo.server.log("IndigoLogHandler Initialized")

	def emit(self, record):
		# First, determine if it needs to be an Indigo error
		is_error = True if record.levelno == LOG_ERROR else False

		# Capture the level name from our dict. If its not in our dict, just use its STR equivalent
		levelName = self.logLevelNameDict.get(record.levelno,str(record.levelno))

		# Setup Stack visualization

		theTrace = traceback.extract_stack()
		NestingDepth = max(0, min(len(theTrace) - 3, 21))
		callingFile, callingLine, callingProc, sourceCode = theTrace[NestingDepth]	# unpack the trace record for the call to mmLib_Log

		#callingPackage = str("(" + os.path.basename(callingFile) + "." + str(callingProc) + ":" + str(callingLine) + ")")	# Construct a MM callingPackage (we skip the jump table)
		#if exception != "": exception = "[" + exception + "]"
		#logMessage = '[{0:<22}] {1}'.format(str('|' * NestingDepth) + str('.' * int(22 - NestingDepth)), str( datetime.datetime.now().strftime("%I:%M:%S %p") + " [" + logType + "] " + logMessage + exception + callingPackage))

		logMessage = ""

		if levelName == MM_LOG_REPORT:
			stackLevel = ""
			logMessage += "\n"
		else:
			stackLevel = '[{0:<22}]'.format(str('|' * NestingDepth) + str('.' * int(22 - NestingDepth)))

		if levelName == MM_LOG_TIMESTAMP:
			timeStamp = " " + str(datetime.datetime.now().strftime("%I:%M:%S %p"))
		else:
			timeStamp = ""

		if levelName == MM_LOG_DEBUG_NOTE:
			type_string = self.displayName + " " + stackLevel + ' mmDebug'
			logMessage = ":  " + self.format(record)
		else:
			type_string = self.displayName + " " + stackLevel
			logMessage += levelName + " : " + timeStamp + " " + self.format(record)

		if levelName == MM_LOG_ERROR:
			type_string = self.displayName + " " + stackLevel + ' M'
			logMessage = ":  " + self.format(record)

		indigo.server.log(message=logMessage, type=type_string, isError=is_error)

	def set_debug(self, debugOn):
		if debugOn:
			mmOurPlugin.__logger.setLevel(logging.DEBUG)
		else:
			mmOurPlugin.__logger.setLevel(logging.INFO)
		mmOurPlugin.__logger.info("set_debug to '%s'", debugOn)



class IndigoLogHandlerTerse(logging.Handler, object):


	def __init__(self, displayName, level=logging.NOTSET):
		indigo.server.log("Entering IndigoLogHandlerTerse")
		super(IndigoLogHandlerTerse, self).__init__(displayName, level)
		indigo.server.log("IndigoLogHandlerTerse Initialized")

	def mmTerse(self, msg, *args, **kwargs):
		indigo.server.log(message="Terse Message", type="MotionMap3" + "mmTerse", isError=False)

	def emit(self, record):

		indigo.server.log(message="In Terse Handler: " + self.format(record), type="mmTerse", isError=False)


class IndigoLogHandlerVerbose(logging.Handler, object):

	def __init__(self, displayName, level=logging.NOTSET):
		indigo.server.log("Entering IndigoLogHandlerVerbose")
		super(IndigoLogHandlerVerbose, self).__init__(displayName, level)
		indigo.server.log("IndigoLogHandlerVerbose Initialized")

	def mmVrbse(self, msg, *args, **kwargs):
		indigo.server.log(message="Verbose Message", type="MotionMap3" + "mmVrbse", isError=False)

	def emit(self, record):

		indigo.server.log(message="In Verbose Handler: " + self.format(record), type="mmVerbose", isError=False)

