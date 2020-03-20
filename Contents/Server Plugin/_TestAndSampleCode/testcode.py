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
import time

#====================================
#============  Main  ================
#====================================

msg = "This is a timestamp."
ct = time.time()
lt = time.localtime(ct)
t = time.strftime("%Y-%m-%d %H:%M:%S", lt)
timestampTime = "%s.%03d" % (t, (ct - long(ct)) * 1000)
msg = timestampTime + " " + msg
print msg
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

