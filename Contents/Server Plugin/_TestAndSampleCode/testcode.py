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

# Main Code

theDict = {}
timeTagDict = {}
canceledTimeTags = {}
delayQueue = []
delayedFunctionKeys = {}
delayedParameters = {}
lastDelayProcRunTime = 0
FractionalGranularity = .000001
fractionalIndex = FractionalGranularity
pendingCommands = deque()

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

	startTime = timer()

	# Create the entries.. this also deletes as necessary
	for i in range(1000):
		registerDelayedAction({"theFunction":"randomFunction"+str(int(random.randint(100,999))), "timeDeltaSeconds": int(random.randint(100,999))})

	# Now acess the entries as if executing the proc

	for i in range(1000):
		bisectKey = delayQueue[0]
		theParameters = delayedParameters[bisectKey]
		theProc = theParameters["theFunction"]
		doSomeMath()	# normally you would do the proc here

	endTime = timer()

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

	startTime = timer()

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

	endTime = timer()

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

	startTime = timer()

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

	endTime = timer()

	return endTime - startTime

#=======================
#======================= Testing Command Queue actions
#=======================

############################################################################################
# qMatch - compare given entry to deque (deck) entry
############################################################################################
def qMatch(qEntry, theCommandParameters, findDirective):

	if not findDirective: return(1)	# yes it matches

	for directive in findDirective:
		try:
			passedDirectiveValue = theCommandParameters[directive]
			queuedDirectiveValue = qEntry[directive]
		except:
			return(0)	# if the directive isnt found in theCommandParameters, or qEntry, no match

		if queuedDirectiveValue != passedDirectiveValue:
			return(0)	# values were found, but they dont match

	return(1)	# aha it matches!


############################################################################################
# qDelete - delete n entry from queue deque (deck)
############################################################################################
def qDelete(theQ, n):
	theQ.rotate(-n)
	theQ.popleft()
	theQ.rotate(n)


############################################################################################
# findQ = does not look into first queue element, its already being processed
#
#	Search PendingCommands for entries whos device is theDevice(name) and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
#
#  ############################################################################################
def findQ(targetID, theCommandParameters, findDirective):

	n=0
	for qEntry in pendingCommands:                   # iterate over the deque's elements
		# theDevice is already implied
		if n and qEntry['theDevice'] == targetID:
			if findDirective != 0 and qMatch(qEntry,theCommandParameters, findDirective):
				return(n)
		n=n+1

	return(0)                                   # we dont care about elem 0, its already being processed


############################################################################################
#
# flushQ - note we only look for a single entry because we only support 1 queue entry per command type per device
#
#	Flush all PendingCommands entries whos device name matches theCommandParameters["theDevice"] and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
#
# ############################################################################################
def flushQ(theDeviceName, theCommandParameters, matchingEntries):

	n=findQ(theDeviceName, theCommandParameters, matchingEntries)
	if n:
		#print("flushQ - flushing queued command " + theDeviceName + ": " + theCommandParameters["theCommand"])
		qDelete(pendingCommands, n)

	return n

############################################################################################
#
# enqueQ
#
############################################################################################
def enqueQ(theTargetDevice, theCommandParameters, flushDirective ):

	# theCommandParameters is a dictionary

	startTheQueue = not pendingCommands

	if flushDirective: flushQ(theTargetDevice, theCommandParameters, flushDirective)    # Get rid of the old ones if asked
	qEntry = theCommandParameters
	qEntry['theDevice'] = theTargetDevice
	qEntry['theIndigoDeviceID'] = "SampleDevID"
	qEntry["enqueueTime"] = time.time()

	pendingCommands.append(qEntry)

def	runCommands():

	global pendingCommands

	numExecutedCommands = 0

	while pendingCommands:
		# Keep looping until you get a 0 result code (means in process), or you run out of pending commands
		pendingCommands.popleft()
		numExecutedCommands = numExecutedCommands + 1

	#print "Test4 Number of commands Executed: " + str(numExecutedCommands)

def	test4():

	global	pendingCommands

	pendingCommands = deque()

	startTime = timer()

	# Create the entries.. this also deletes as necessary
	for i in range(1000):
		enqueQ("randomDevice"+str(int(random.randint(100,999))), {"theCommand":"On"}, ['theCommand'])

	# Now acess the entries as if executing the proc
	for i in range(1000):
		enqueQ2("testDevice", {"theCommand": "On"}, ['theCommand'])

	runCommands()

	endTime = timer()

	return endTime - startTime

#=======================
#======================= Testing Command Queue actions Alternate 2
#=======================

############################################################################################
# qMatch - compare given entry to deque (deck) entry
############################################################################################
def qMatch2(qEntry, theCommandParameters, findDirective):
	targetName = theCommandParameters['theDevice']
	targetCommand = theCommandParameters['theCommand']


	matchingEntries = [entry for ind, entry in enumerate(pendingCommands) if entry['theDevice'] == targetName and entry['theCommand'] == targetCommand]

	if matchingEntries == []:
		return (0)
	else:
		return (1)  # aha it matches!


############################################################################################
# qDelete - delete n entry from queue deque (deck)
############################################################################################
def qDelete2(theQ, n):
	theQ.rotate(-n)
	theQ.popleft()
	theQ.rotate(n)


############################################################################################
# findQ = does not look into first queue element, its already being processed
#
#	Search PendingCommands for entries whos device is theDevice(name) and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
#
#  ############################################################################################
def findQ2(targetID, theCommandParameters, findDirective):
	n = 0
	for qEntry in pendingCommands:  # iterate over the deque's elements
		# theDevice is already implied
		if n and qEntry['theDevice'] == targetID:
			if findDirective != 0 and qMatch2(qEntry, theCommandParameters, findDirective):
				return (n)
		n = n + 1

	return (0)  # we dont care about elem 0, its already being processed


############################################################################################
#
# flushQ - note we only look for a single entry because we only support 1 queue entry per command type per device
#
#	Flush all PendingCommands entries whos device name matches theCommandParameters["theDevice"] and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
#
# ############################################################################################
def flushQ2(theDeviceName, theCommandParameters, matchingEntries):

	global pendingCommands

	targetCommand = theCommandParameters['theCommand']

	if pendingCommands != []:
		for ind, entry in enumerate(pendingCommands):
			if entry['theDevice'] == theDeviceName and entry['theCommand'] == targetCommand:
				del pendingCommands[ind]
				break;
	return 0


############################################################################################
#
# enqueQ
#
############################################################################################
def enqueQ2(theTargetDevice, theCommandParameters, flushDirective):


	global pendingCommands

	# theCommandParameters is a dictionary

	qEntry = theCommandParameters
	qEntry['theDevice'] = theTargetDevice
	qEntry['theIndigoDeviceID'] = "SampleDevID"
	qEntry["enqueueTime"] = time.time()
	if flushDirective:
		flushQ2(theTargetDevice, qEntry, flushDirective)  # Get rid of the old ones if asked
	else:
		print("No flush Directive")

	pendingCommands.append(qEntry)

def	runCommands2():

	global pendingCommands

	numExecutedCommands = 0

	while pendingCommands:
		# Keep looping until you get a 0 result code (means in process), or you run out of pending commands
		pendingCommands.popleft()
		numExecutedCommands = numExecutedCommands + 1

	#print "Test5 Number of commands Executed: " + str(numExecutedCommands)

def test5():
	global pendingCommands

	pendingCommands = deque()

	startTime = timer()

	# Create the entries.. this also deletes as necessary
	for i in range(1000):
		enqueQ2("randomDevice" + str(int(random.randint(100, 999))), {"theCommand": "On"}, ['theCommand'])

	# Now acess the entries as if executing the proc
	for i in range(1000):
		enqueQ2("testDevice", {"theCommand": "On"}, ['theCommand'])

	runCommands2()

	endTime = timer()

	return endTime - startTime

#=======================
#======================= Testing Command Queue actions Alternate 3
#=======================

############################################################################################
# qMatch - compare given entry to deque (deck) entry
############################################################################################
def qMatch3(qEntry, theCommandParameters, findDirective):
	targetName = theCommandParameters['theDevice']
	targetCommand = theCommandParameters['theCommand']


	matchingEntries = [entry for ind, entry in enumerate(pendingCommands) if entry['theDevice'] == targetName and entry['theCommand'] == targetCommand]

	if matchingEntries == []:
		return (0)
	else:
		return (1)  # aha it matches!


############################################################################################
# qDelete - delete n entry from queue deque (deck)
############################################################################################
def qDelete3(theQ, n):
	theQ.rotate(-n)
	theQ.popleft()
	theQ.rotate(n)


############################################################################################
# findQ = does not look into first queue element, its already being processed
#
#	Search PendingCommands for entries whos device is theDevice(name) and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
#
#  ############################################################################################
def findQ3(targetID, theCommandParameters, findDirective):
	n = 0
	for qEntry in pendingCommands:  # iterate over the deque's elements
		# theDevice is already implied
		if n and qEntry['theDevice'] == targetID:
			if findDirective != 0 and qMatch3(qEntry, theCommandParameters, findDirective):
				return (n)
		n = n + 1

	return (0)  # we dont care about elem 0, its already being processed


############################################################################################
#
# flushQ - note we only look for a single entry because we only support 1 queue entry per command type per device
#
#	Flush all PendingCommands entries whos device name matches theCommandParameters["theDevice"] and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
#
# ############################################################################################
def flushQ3(theDeviceName, theCommandParameters, matchingEntries):

	#All you need to do is move the timeTag (if one) to canceledTimeTags

	global pendingCommands
	global timeTagDict
	global canceledTimeTags

	# Look up the commandID
	CommandID = theCommandParameters["theDevice"] + "." + theCommandParameters["theCommand"]

	try:
		timeTag = timeTagDict[CommandID]
	except:
		#Not found, No work to do
		return 0

	timeTagDict.pop(CommandID, None)			# take the entry out of the time tag queue so it wont be found again
	canceledTimeTags[timeTag] = 1				# and mark this found entry cancelled

	return 0


############################################################################################
#
# enqueQ
#
############################################################################################
def enqueQ3(theTargetDevice, theCommandParameters, flushDirective):


	global pendingCommands
	global timeTagDict
	global canceledTimeTags

	# theCommandParameters is a dictionary

	timeTag = time.time()
	CommandID = theTargetDevice + "." + theCommandParameters["theCommand"]

	qEntry = theCommandParameters
	qEntry['theDevice'] = theTargetDevice
	qEntry['theIndigoDeviceID'] = "SampleDevID"
	qEntry["enqueueTime"] = timeTag
	#canceledTimeTags[timeTag] = 0		# GB Fix me Temp

	if flushDirective:
		flushQ3(theTargetDevice, qEntry, flushDirective)  # Get rid of the old ones if asked
	else:
		print("No flush Directive")

	pendingCommands.append(qEntry)
	timeTagDict[CommandID] = timeTag	# this will be used to cancel this command by timeTag in the future if need be

def	runCommands3():

	global pendingCommands
	global timeTagDict
	global canceledTimeTags

	numExecutedCommands = 0

	while pendingCommands:
		# Keep looping until you get a 0 result code (means in process), or you run out of pending commands
		theCommandParameters = pendingCommands[0]
		timeTag = theCommandParameters["enqueueTime"]
		CommandID = theCommandParameters["theDevice"] + "." + theCommandParameters["theCommand"]

		if canceledTimeTags.pop(timeTag, None) == None:
			#run the proc
			numExecutedCommands = numExecutedCommands + 1

		timeTagDict.pop(CommandID, None)
		pendingCommands.popleft()

	#print "Test6 Number of commands Executed: " + str(numExecutedCommands)

def test6():
	global pendingCommands

	pendingCommands = deque()

	startTime = timer()

	# Create the entries.. this also deletes as necessary
	for i in range(1000):
		enqueQ3("randomDevice" + str(int(random.randint(100, 999))), {"theCommand": "On"}, ['theCommand'])

	# Now acess the entries as if executing the proc
	for i in range(1000):
		enqueQ3("testDevice", {"theCommand": "On"}, ['theCommand'])

	runCommands3()

	endTime = timer()

	return endTime - startTime



#=======================
#======================= MAIN
#=======================


random.seed()

#quit()

accumulator = 0
for i in range(0,10):
	accumulator = accumulator + test4()

print("Test4 average timing: " + str(accumulator/10) + " seconds.")


accumulator = 0
for i in range(0,10):
	accumulator = accumulator + test5()

print("Test5 average timing: " + str(accumulator/10) + " seconds.")

accumulator = 0
for i in range(0,10):
	accumulator = accumulator + test6()

print("Test6 average timing: " + str(accumulator/10) + " seconds.")

print(str(pendingCommands))
matchingEntries = [entry for ind, entry in enumerate(pendingCommands) if entry['theDevice'] == "testDevice" and entry['theCommand'] == 'On' and canceledTimeTags[entry["enqueueTime"]] == 0]
print "number of matches = " + str(len(matchingEntries)) + " Matches: " + str(matchingEntries)
print str(canceledTimeTags)
print str(timeTagDict)

if 0:
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

