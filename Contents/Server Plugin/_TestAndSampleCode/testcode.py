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

# Main Code

theDict = {}
delayQueue = []
delayedFunctionKeys = {}
delayedParameters = {}
lastDelayProcRunTime = 0
FractionalGranularity = .000001
fractionalIndex = FractionalGranularity

def doSomeMath():
	return int(random.randint(100,999))

def showSomeInfo(theString):
	print "showSomeInfo: " + theString


#=======================
#======================= Test1
#=======================

def getDelayedAction1(theFunction):

	bisectKey = delayedFunctionKeys[theFunction]
	bisectIndex = bisect.bisect_left(delayQueue, bisectKey)
	theParameters = delayedParameters[bisectKey]
	#print "The Key: " + str(bisectKey) + ". The Index: " + str(bisectIndex) + ". Tuples: " + str(bisectTuple) + ". Paramaters: " + str(theParameters)
	#print str(delayQueue)
	theProc = theParameters["theFunction"]

	return theProc


def cancelDelayedAction(theFunction):

	global delayQueue
	global delayedFunctionKeys
	global delayedParameters

	try:
	 	bisectKey = delayedFunctionKeys[theFunction]
		if bisectKey :
			# There is a function waiting
			delayedFunctionKeys[theFunction] = 0	# Reset delayedFunctionKeys... to no function waiting
			try:
				del delayedParameters[bisectKey]
			except:
				pass
		else: return
	except: return	# no function waiting

	delayQueue.pop(bisect.bisect_left(delayQueue, bisectKey))

def registerDelayedAction(parameters):
	global delayQueue
	global lastDelayProcRunTime
	global delayedFunctionKeys
	global delayedParameters

	theFunction = parameters['theFunction']
	whenSeconds = parameters['timeDeltaSeconds'] + time.mktime(time.localtime())
	bisectKey = str(whenSeconds) + " " + str(theFunction)


	cancelDelayedAction(theFunction)  # we only support one entry for this function at a time

	if time.mktime(time.localtime()) >= whenSeconds:
		# Time already expired, do it now
		theFunction(parameters)
	else:
		bisect.insort(delayQueue, bisectKey)
		delayedFunctionKeys[theFunction] = bisectKey  # We now mark this function as waiting
		delayedParameters[bisectKey] = parameters

	if lastDelayProcRunTime:
		# Round the time up to the next timer run and return it for the convenience of the caller
		timeDelta = int((time.mktime(
			time.localtime()) - lastDelayProcRunTime) % 5)  # time since the last pass through timer
		if timeDelta: timeDelta = (5 - timeDelta)
		newSeconds = whenSeconds + timeDelta
	else:
		newSeconds = whenSeconds

	# Returns time when the function will be run
	return newSeconds




def	test1():
	global	theDict
	global	delayQueue
	global	delayedFunctionKeys
	global	delayedParameters
	global	lastDelayProcRunTime
	global	fractionalIndex

	theDict = {}
	delayQueue = []
	delayedFunctionKeys = {}
	delayedParameters = {}
	lastDelayProcRunTime = 0
	fractionalIndex = FractionalGranularity

	registerDelayedAction({"theFunction": showSomeInfo,
						   "timeDeltaSeconds": int(500)})

	startTime = time.clock()

	# Create the entries.. this also deletes as necessary
	for i in range(1000):
		registerDelayedAction({"theFunction":"randomFunction"+str(int(random.randint(100,999))), "timeDeltaSeconds": int(random.randint(100,999))})

	# Now acess the entries as if executing the proc

	for i in range(1000):
		bisectKey = delayQueue[0]
		theParameters = delayedParameters[bisectKey]
		theProc = theParameters["theFunction"]
		doSomeMath()	# normally you would do the proc here

	endTime = time.clock()

	return endTime - startTime


#=======================
#======================= Test2
#=======================

def getDelayedAction2(theFunction):

	bisectKey = delayedFunctionKeys[theFunction]
	bisectIndex = bisect.bisect_left(delayQueue, (bisectKey, ))
	bisectTuple = delayQueue[bisectIndex]
	theParameters = bisectTuple[1]
	#print "The Key: " + str(bisectKey) + ". The Index: " + str(bisectIndex) + ". Tuples: " + str(bisectTuple) + ". Paramaters: " + str(theParameters)
	#print str(delayQueue)
	theProc = theParameters["theFunction"]

	return theProc

def cancelDelayedAction2(theFunction):

	global delayQueue
	global delayedFunctionKeys
	global delayedParameters

	try:
	 	bisectKey = delayedFunctionKeys[theFunction]
		if bisectKey :
			# There is a function waiting
			delayedFunctionKeys[theFunction] = 0	# Reset delayedFunctionKeys... to no function waiting
		else: return
	except: return	# no function waiting

	delayQueue.pop(bisect.bisect_left(delayQueue, (bisectKey, )))

def registerDelayedAction2(parameters):
	global delayQueue
	global lastDelayProcRunTime
	global delayedFunctionKeys
	global delayedParameters

	theFunction = parameters['theFunction']
	whenSeconds = parameters['timeDeltaSeconds'] + time.mktime(time.localtime())
	bisectKey = str(whenSeconds) + " " + str(theFunction)


	cancelDelayedAction2(theFunction)  # we only support one entry for this function at a time

	if time.mktime(time.localtime()) >= whenSeconds:
		# Time already expired, do it now
		theFunction(parameters)
	else:
		bisect.insort(delayQueue, (bisectKey, parameters))
		delayedFunctionKeys[theFunction] = bisectKey  # We now mark this function as waiting

	if lastDelayProcRunTime:
		# Round the time up to the next timer run and return it for the convenience of the caller
		timeDelta = int((time.mktime(
			time.localtime()) - lastDelayProcRunTime) % 5)  # time since the last pass through timer
		if timeDelta: timeDelta = (5 - timeDelta)
		newSeconds = whenSeconds + timeDelta
	else:
		newSeconds = whenSeconds

	# Returns time when the function will be run
	return newSeconds




def	test2():

	global	theDict
	global	delayQueue
	global	delayedFunctionKeys
	global	delayedParameters
	global	lastDelayProcRunTime

	theDict = {}
	delayQueue = []
	delayedFunctionKeys = {}
	delayedParameters = {}
	lastDelayProcRunTime = 0

	registerDelayedAction2({"theFunction": showSomeInfo,
						   "timeDeltaSeconds": int(500)})

	startTime = time.clock()

	# Create the entries.. this also deletes as necessary
	for i in range(1000):
		registerDelayedAction3({"theFunction":"randomFunction"+str(int(random.randint(100,999))), "timeDeltaSeconds": int(random.randint(100,999))})

	# Now acess the entries as if executing the proc

	for i in range(1000):
		bisectTuple = delayQueue[0]
		bisectKey = bisectTuple[0]
		theParameters = bisectTuple[1]
		theProc = theParameters["theFunction"]
		doSomeMath()	# normally you would do the proc here

	endTime = time.clock()

	return endTime - startTime




#=======================
#======================= Test3
#=======================

def getDelayedAction3(theFunction):

	bisectKey = delayedFunctionKeys[theFunction]
	bisectIndex = bisect.bisect_left(delayQueue, (bisectKey, ))
	bisectTuple = delayQueue[bisectIndex]
	theParameters = bisectTuple[1]
	#print "The Key: " + str(bisectKey) + ". The Index: " + str(bisectIndex) + ". Tuples: " + str(bisectTuple) + ". Paramaters: " + str(theParameters)
	#print str(delayQueue)
	theProc = theParameters["theFunction"]

	return theProc

def cancelDelayedAction3(theFunction):

	global delayQueue
	global delayedFunctionKeys

	try:
	 	bisectKey = delayedFunctionKeys[theFunction]
		if bisectKey :
			# There is a function waiting
			delayedFunctionKeys[theFunction] = 0	# Reset delayedFunctionKeys... to no function waiting
		else: return
	except: return	# no function waiting

	delayQueue.pop(bisect.bisect_left(delayQueue, (bisectKey, )))

def registerDelayedAction3(parameters):
	global delayQueue
	global lastDelayProcRunTime
	global fractionalIndex
	global delayedFunctionKeys

	fractionalIndex = fractionalIndex+FractionalGranularity
	if fractionalIndex >= 1.0: fractionalIndex = FractionalGranularity

	theFunction = parameters['theFunction']
	whenSeconds = parameters['timeDeltaSeconds'] + time.mktime(time.localtime())
	#bisectKey = str(whenSeconds) + str(fractionalIndex)
	bisectKey = whenSeconds + fractionalIndex


	cancelDelayedAction3(theFunction)  # we only support one entry for this function at a time

	if time.mktime(time.localtime()) >= whenSeconds:
		# Time already expired, do it now
		theFunction(parameters)
	else:
		bisect.insort(delayQueue, (bisectKey, parameters))
		delayedFunctionKeys[theFunction] = bisectKey  # We now mark this function as waiting

	if lastDelayProcRunTime:
		# Round the time up to the next timer run and return it for the convenience of the caller
		timeDelta = int((time.mktime(
			time.localtime()) - lastDelayProcRunTime) % 5)  # time since the last pass through timer
		if timeDelta: timeDelta = (5 - timeDelta)
		newSeconds = whenSeconds + timeDelta
	else:
		newSeconds = whenSeconds

	# Returns time when the function will be run
	return newSeconds




def	test3():

	global	theDict
	global	delayQueue
	global	delayedFunctionKeys
	global	delayedParameters
	global	lastDelayProcRunTime
	global	fractionalIndex

	theDict = {}
	delayQueue = []
	delayedFunctionKeys = {}
	delayedParameters = {}
	lastDelayProcRunTime = 0
	fractionalIndex = FractionalGranularity

	registerDelayedAction3({"theFunction": showSomeInfo,
						   "timeDeltaSeconds": int(500)})

	startTime = time.clock()

	# Create the entries.. this also deletes as necessary
	for i in range(1000):
		registerDelayedAction3({"theFunction":"randomFunction"+str(int(random.randint(100,999))), "timeDeltaSeconds": int(random.randint(100,999))})

	# Now acess the entries as if executing the proc

	for i in range(1000):
		bisectTuple = delayQueue[0]
		bisectKey = bisectTuple[0]
		theParameters = bisectTuple[1]
		theProc = theParameters["theFunction"]
		doSomeMath()	# normally you would do the proc here

	endTime = time.clock()

	return endTime - startTime



#=======================
#======================= MAIN
#=======================


random.seed()

accumulator = 0
for i in range(0,100):
	accumulator = accumulator + test1()

aProc = getDelayedAction1(showSomeInfo)
aProc("Test1 average timing: " + str(accumulator/100) + " seconds.")




accumulator = 0
for i in range(0,100):
	accumulator = accumulator + test3()

aProc = getDelayedAction3(showSomeInfo)
aProc("Test3 average timing: " + str(accumulator/100) + " seconds.")





accumulator = 0
for i in range(0,100):
	accumulator = accumulator + test2()

aProc = getDelayedAction2(showSomeInfo)
aProc("Test2 average timing: " + str(accumulator/100) + " seconds.")





accumulator = 0
for i in range(0,100):
	accumulator = accumulator + test2()

aProc = getDelayedAction2(showSomeInfo)
aProc("Test2 average timing: " + str(accumulator/100) + " seconds.")




accumulator = 0
for i in range(0,100):
	accumulator = accumulator + test3()

aProc = getDelayedAction3(showSomeInfo)
aProc("Test3 average timing: " + str(accumulator/100) + " seconds.")




accumulator = 0
for i in range(0,100):
	accumulator = accumulator + test1()

aProc = getDelayedAction1(showSomeInfo)
aProc("Test1 average timing: " + str(accumulator/100) + " seconds.")

