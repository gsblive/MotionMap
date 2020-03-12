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

#====================================
#============  Main  ================
#====================================

x = 0

class Object1():
	Value1 = 0
	Value2 = 0
	Value3 = 0

	def __init__(self, a, b, c):
		self.Value1 = a
		self.Value2 = b
		self.Value3 = c


	def	__repr__(self):
		resultString = str("Value1" + str(Object1.Value1))
		return resultString


	def __str__(self):
		resultString = ""
		myDict = vars(self)
		for keys, values in myDict.items():
			resultString = resultString + "Object1." + str(keys) + ':' + str(values) + "\n"
		return resultString

	def doSomething(self):
		print str(self.__class__.__name__)
		myDict = vars(self)
		for keys, values in myDict.items():
			print(str(keys) + ':' + str(values))

		return 0



#myObj = Object1(1,20,300)
#myObj.doSomething()

#print myObj

def doMath():
	global x
	x = x+1
	return(0)

def doMath2(var1, var2):
	global x
	x = x+1

def throughProc():
	doMath2(1,0)

def invalidLoggindDirective():
	print("Invalid Logging Directive")

def nullProc(): pass

#print datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# print(sys.version)

#
#
# test performance in acces to variables from dict
# For the purposes of experimenting with consolidated log dispatch in MM
#



indi = {"Error.0":doMath, "Debug.0":doMath, "Log.0":doMath, "Force.0":doMath, "Warn.0":doMath,"Error.1":nullProc, "Debug.1":0, "Log.1":0, "Force.1":0, "Warn.1":0}
theSelecedParameters = {"Error.0":1, "Debug.0":1, "Log.0":1, "Force.0":1, "Warn.0":1,"Error.1":1, "Debug.1":0, "Log.1":0, "Force.1":0, "Warn.1":0}
indi2 = {"Error.0":doMath, "Debug.0":doMath, "Log.0":doMath, "Force.0":doMath, "Warn.0":doMath,"Error.1":nullProc, "Debug.1":nullProc, "Log.1":nullProc, "Force.1":nullProc, "Warn.1":nullProc}


print "Test"

LogDirectiveNOP = "1"
LogDirective = "doMath()"



def theProc():
	return "in theProc"

ourLevel = 2

shortcut = lambda x : doMath() if x < 2 else 0

def displayMessage(logType, logMessage, displayProc):

	try:
		stringCheck = isinstance(logMessage, str)
	except:
		stringCheck = 0

	if not stringCheck: logMessage = "XXX displayMessage Error: Cannot display message... likely a formatting or type error"

	theTrace = traceback.extract_stack()
	NestingDepth = max(0, min(len(theTrace) - 3, 21))

	callingFile, callingLine, callingProc, sourceCode = theTrace[NestingDepth]	# unpack the trace record
	callingPackage = str("(" + os.path.basename(callingFile) + "." + str(callingProc) + ":" + str(callingLine) + ")")	# Construct a MM callingPackage (we skip the jump table)
	logMessage = '[{0:<22}] {1}'.format(str('|' * NestingDepth) + str('.' * int(22 - NestingDepth)), str( datetime.datetime.now().strftime("%I:%M:%S %p") + " " + ': ' + logMessage + " " + callingPackage))

	print(logMessage)
	return

displayMessage(1,"TestMessage",0)
displayMessage(1,1000,0)

exit()

print "\n"
print("==============================================")
print(" if Method")
print(" PRO: Fast, no indirection")
print(" CON:More complicated to call function")
print("==============================================")

ourLevel = 0
start = time.time()
for reps in range(1,1000000):
	if ourLevel: doMath()
end = time.time()
print("If METHOD... (MISS) Call in seconds:" + str(end - start))

ourLevel = 1
start = time.time()
for reps in range(1,1000000):
	if ourLevel: doMath()
end = time.time()
print("If METHOD... (HIT) Call in seconds:" + str(end - start))


print "\n"
print("==============================================")
print(" Lambda Method")
print(" PRO: No Selector Needed")
print(" CON:0 to 1 indirection")
print("==============================================")

start = time.time()
for reps in range(1,1000000):
	shortcut(2)
end = time.time()
print("Lambda METHOD... Jump Table (MISS) Call in seconds:" + str(end - start))

start = time.time()
for reps in range(1,1000000):
	shortcut(1)
end = time.time()
print("Lambda METHOD... Jump Table (HIT) Call in seconds:" + str(end - start))


print "\n"
print("==============================================")
print(" Current Method")
print(" PRO: No Selector Needed")
print(" CON: 1 or 2 Layers of indirection")
print("==============================================")

aProc = nullProc
start = time.time()
for reps in range(1,1000000):
	aProc()
end = time.time()
print("CURRENT METHOD... Jump Table (MISS) Call in seconds:" + str(end - start))

aProc = throughProc

start = time.time()
for reps in range(1,1000000):
	aProc()
end = time.time()
print("CURRENT METHOD... Jumo Table (HIT) Call in seconds:" + str(end - start))

print "\n"
print("==============================================")
print(" Durect Call, selctor defines parameters")
print(" PRO: 0 to 1 layer indirection")
print(" CON: Needs Selector")
print("==============================================")

def testProc(theVersion):
	global x
	theVariables = indi.get("theVersion","NA")		#Use our selector to get the parameters
	if not theVariables:
		pass
	else:
		# do the work here, no jumping
		x = x+1

start = time.time()
for reps in range(1,1000000):
	testProc("Debug.1")
end = time.time()
print("Flatter (MISS) Call in seconds:" + str(end - start))

start = time.time()
for reps in range(1,1000000):
	testProc("Error.0")
end = time.time()
print("Direct Call (HIT) in seconds:" + str(end - start))


print "\n"
print("==============================================")
print(" Durect Call, numeric selctor defines parameters")
print(" PRO: 0 to 1 layer indirection. no lookup in miss case")
print(" CON: Needs Selector")
print("==============================================")

theLimit = 1

def testProc2(theVersion):
	global x
	if theVersion < theLimit: return		#Use our selector to determine if we should continue
	# do the work here, no jumping
	x = x+1

start = time.time()
for reps in range(1,1000000):
	testProc2(0)
end = time.time()
print("Flatter (MISS) Call in seconds:" + str(end - start))

start = time.time()
for reps in range(1,1000000):
	testProc2(1)
end = time.time()
print("Direct Call (HIT) in seconds:" + str(end - start))


print "\n"
print("==============================================")
print(" Durect Call, numeric selctor reviewed by caller")
print(" PRO: no junp in miss case")
print(" CON: Needs Selector. Needs IF at caller")
print("==============================================")

theLimit = 1
theVersion = 0

start = time.time()
for reps in range(1,1000000):
	if theVersion < theLimit: continue
end = time.time()
print("Flatter (MISS) Call in seconds:" + str(end - start))

theVersion = 2

start = time.time()
for reps in range(1,1000000):
	if theVersion > theLimit: doMath()

end = time.time()
print("Direct Call (HIT) in seconds:" + str(end - start))


print "\n"
print("==============================================")
print("==============================================")

start = time.time()
for reps in range(1,1000000):
	doMath()
end = time.time()
print("Direct Call in seconds:" + str(end - start))


start = time.time()
for reps in range(1,1000000):
	doMath()
end = time.time()
print("Direct Call in seconds:" + str(end - start))


start = time.time()
for reps in range(1,1000000):
	theProc = indi["Error.1"]
	if theProc:
		theProc()
	else:
		pass
end = time.time()
print("Indirect (Null) Call in seconds:" + str(end - start))



start = time.time()
for reps in range(1, 1000000):
	indi.get("Error.1", invalidLoggindDirective)()
end = time.time()
print("Indirect Two (Null) Call in seconds:" + str(end - start))



start = time.time()
for reps in range(1,1000000):
	theProc = indi["Error.0"]
	if theProc:
		theProc()
	else:
		pass
end = time.time()
print("Indirect Call in seconds:" + str(end - start))



start = time.time()
for reps in range(1,1000000):
	try:
		indi["Debug.1"]()
	except:
		pass
end = time.time()
print("FailMode in seconds:" + str(end - start))



indi.get("Error.2", invalidLoggindDirective)()
