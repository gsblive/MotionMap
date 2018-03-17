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
#	Flush all PendingCommands entries whos device name matches theCommandParameters['theDevice'] and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
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
#	Flush all PendingCommands entries whos device name matches theCommandParameters['theDevice'] and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
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
#	Flush all PendingCommands entries whos device name matches theCommandParameters['theDevice'] and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
#
# ############################################################################################
def flushQ3(theDeviceName, theCommandParameters, matchingEntries):

	#All you need to do is move the timeTag (if one) to canceledTimeTags

	global pendingCommands
	global timeTagDict
	global canceledTimeTags

	# Look up the commandID
	CommandID = theCommandParameters['theDevice'] + "." + theCommandParameters["theCommand"]

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
		CommandID = theCommandParameters['theDevice'] + "." + theCommandParameters["theCommand"]

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

#=================================
#========== Event related code ============
#=================================

eventPublishers = {'Indigo': {'DevUpdate':deque([]),'DevRcvCmd':deque([]),'DevCmdComplete':deque([]),'DevCmdErr':deque([])}, 'MMSys': {'XCmd':deque([])}}
targettedEvents = {}
eventsDelivered = 0

def resetGlobals():
	global 	eventPublishers
	global 	targettedEvents

	eventPublishers = {'Indigo': {'DevUpdate':deque([]),'DevRcvCmd':deque([]),'DevCmdComplete':deque([]),'DevCmdErr':deque([])}, 'MMSys': {'XCmd':deque([])}}

	targettedEvents = {}

#
# subscribeToEvents - add theHandler to be called when any of the events listed in theEvents occur from thePublisher
#
#	Events:
#		a list of events to subscribe to
#
#	Publisher:
#		Text string identifying the publisher of the event. For example..
#
#		'Indigo'	Hardware Sourced Event, like a light switch was turned on
#		MMDevName	Any MM Device (this can create and use any custom event, for any purpose)
#		'MMSys'		an Indigo Action Script calls executeMMCommand is published as MMSys publisher
#
#	theHandler:
#		A proc pointer that handles the event. format must be
#		theHandler(eventID, eventParameters)
#
#  		where eventParameters is a dict containing: {theEvent, publisher, Time of Event (seconds), Plus "handlerDefinedData" Passed in at time of registration}
#
#		Example eventIDs supported (there are many others, MMDevices define their own):
#
#		EventID			Publisher					Description
#		'on'			MotionSensor (MMDevName)	The motion sensor is publishing on event
#		'off'			Indigo						An Off Event was detected form an indigo device
#		'occupied'		VirtualMotionSensor			A motion sensor generated an ON sigl\nal causing a group to be occupied
#		'stateChange'	Indigo						Indigo detected a statusUpdate from a device
#
def subscribeToEvents(theEvents, thePublisher, theHandler, handlerDefinedData, aSubscriber):

	global eventPublishers

	for theEvent in theEvents:
		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			print( "subscribeToEvents: Publisher " + str(thePublisher) + " is not publishing requested event " + theEvent + ".")
			continue

		theQueue.append([aSubscriber, theHandler, handlerDefinedData])  # insert into appropriate deque

	return (0)


def subscribeToEvents2(theEvents, thePublisher, theHandler, handlerDefinedData, aSubscriber):

	global eventPublishers

	for theEvent in theEvents:
		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			print( "subscribeToEvents: Publisher " + str(thePublisher) + " is not publishing requested event " + theEvent + ".")
			continue

		theQueue.append([aSubscriber, theHandler, handlerDefinedData])  # insert into appropriate deque
		targettedEvents[thePublisher + "." + theEvent + "." + aSubscriber] = [aSubscriber, theHandler, handlerDefinedData]

	return (0)

def subscribeToEvents3(theEvents, thePublisher, theHandler, handlerDefinedData, aSubscriber):

	global eventPublishers

	for theEvent in theEvents:
		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			print( "subscribeToEvents: Publisher " + str(thePublisher) + " is not publishing requested event " + theEvent + ".")
			continue

		theQueue.append([aSubscriber, theHandler, handlerDefinedData])  # insert into appropriate deque
		# Now append to the targetted event list too
		try:
			theQueue = targettedEvents[thePublisher + "." + theEvent + "." + aSubscriber]
			#print( "subscribeToEvents: Warning - Publisher " + str(thePublisher) + " is already publishing requested event " + theEvent + " to subscriber " + str(aSubscriber))
		except:
			targettedEvents[thePublisher + "." + theEvent + "." + aSubscriber] = deque()
			theQueue = targettedEvents[thePublisher + "." + theEvent + "." + aSubscriber]

		theQueue.append([aSubscriber, theHandler, handlerDefinedData])  # insert into appropriate deque

	return (0)


#
#	unsubscribeFromEvents
#
def unsubscribeFromEvents(theEvents, thePublisher, requestedHandler, theSubscriber):

	global eventPublishers

	if not theEvents:
		try:
			theEvents = list(eventPublishers[thePublisher].keys())
		except:
			print("unsubscribeFromEvents: Warning - Invalid publisher " + thePublisher + ".")
			return(0)

	for theEvent in theEvents:

		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			continue

		theMax = len(theQueue)
		for index in range(theMax):
			aSubscriber, theHandler, handlerDefinedData = theQueue[0]
			if (theSubscriber == 0 or theSubscriber == aSubscriber) and (requestedHandler == 0 or requestedHandler == theHandler):
				theQueue.popleft()
			else:
				theQueue.rotate(-1)

	return (0)

#
#	unsubscribeFromEvents
#		if theEvents == 0, unsubscribe all events for given subscriber
#		if theSubscriber == 0, unsubscribe requested events for all subscribers
#		if theEvents and theSubscriber are both 0, unsubscribe all events for all subscribers for given publisher
#		if the Handler is 0, unsubscribe all handlers that meet the other criteria
#
def unsubscribeFromEvents3(theEvents, thePublisher, requestedHandler, theSubscriber):

	global eventPublishers

	if not theEvents and not theSubscriber:
		# short circuit a lot of processing for this rare occurance
		eventPublishers[thePublisher] = deque([])
		return(0)

	if not theEvents:
		try:
			theEvents = list(eventPublishers[thePublisher].keys())
		except:
			print("unsubscribeFromEvents: Warning - Invalid publisher " + thePublisher + ".")
			return(0)

	for theEvent in theEvents:

		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			continue

		theMax = len(theQueue)
		for index in range(theMax):
			aSubscriber, theHandler, handlerDefinedData = theQueue[0]
			if (theSubscriber == 0 or theSubscriber == aSubscriber) and (requestedHandler == 0 or requestedHandler == theHandler):
				theQueue.popleft()

				# find and delete the associated targettedEvent entry

				theTargettedQueue = targettedEvents.get(thePublisher + "." + theEvent + "." + aSubscriber, 0)
				if theTargettedQueue:
					theTargettedMax = len(theTargettedQueue)
					for targettedIndex in range(theTargettedMax):
						aTargettedSubscriber, theTargettedHandler, targettedHandlerDefinedData = theTargettedQueue[0]
						if (theSubscriber == 0 or theSubscriber == aTargettedSubscriber) and ( requestedHandler == 0 or requestedHandler == theTargettedHandler):
							theTargettedQueue.popleft()
						else:
							theTargettedQueue.rotate(-1)

			else:
				theQueue.rotate(-1)

	return (0)

#
# registerPublisher - All event publishers must first register before they can receive event subscriptions
#
#	Events:
#		a list of events that are published
#
#	Publisher:
#		Text string identifying the publisher of the event. For example..
#
#		'Indigo'	Hardware Sourced Event, like a light switch was turned on (Initialized by the system)
#		MMDevName	Any MM Device (this can create and use any custom event, for any purpose)
#		'Action'	an Indigo Action Script (Initialized by the system)
#
#		Example events supported (there are many others, MMDevices define their own):
#
#		EventID			Publisher					Description
#		'on'			MotionSensor (MMDevName)	The motion sensor is publishing on event
#		'off'			Indigo						An Off Event was detected form an indigo device
#		'occupied'		VirtualMotionSensor			A motion sensor generated an ON sigl\nal causing a group to be occupied
#		'stateChange'	Indigo						Indigo detected a statusUpdate from a device
#		'execute'		'MMSys'						executeMMCommand (all MMDevices register for this event at a minimum)
#
def registerPublisher(theEvents, thePublisher):

	global eventPublishers

	# Get Publisher's event Dict
	try:
		PublishersEventsDict = eventPublishers[thePublisher]
	except:
		eventPublishers[thePublisher] = {}
		PublishersEventsDict = eventPublishers[thePublisher]

	for theEvent in theEvents:

		# Get the Event deque for each event requested

		try:
			theQueue = PublishersEventsDict[theEvent]
		except:
			PublishersEventsDict[theEvent] = deque()
			theQueue = PublishersEventsDict[theEvent]

	return (0)

def dispatchEvent(thePublisher, theEvent, publisherDefinedData, handlerInfo):

	aSubscriber, theHandler, handlerDefinedData = handlerInfo

	eventParameters = publisherDefinedData
	eventParameters.update(handlerDefinedData)
	eventParameters['theEvent'] = theEvent
	eventParameters['publisher'] = thePublisher
	eventParameters['timestamp'] = time.mktime(time.localtime())
	return(theHandler(theEvent, eventParameters))


#
# distributeEvent - Touch all devices in the deque given.
#	theQueue, theEvent: as defined in theHandler info at addToControllerEventDeque()
#
def distributeEvent2(thePublisher, theEvent, theSubscriber, publisherDefinedData):

	global eventPublishers
	global targettedEvents

	if theSubscriber:

		handlerInfo = targettedEvents.get(thePublisher + "." + theEvent + "." + theSubscriber, 0)

		if not handlerInfo:
			print("distributeEvent2: No targettedEvents entry exists for: \'" + thePublisher + "." + theEvent + "." + theSubscriber + "\'")
			return(0)

		return(dispatchEvent(thePublisher, theEvent, publisherDefinedData, handlerInfo))
	else:
		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			print("distributeEvent2: Publisher " + str(thePublisher) + " is not registered to publish " + theEvent + ".")
			return (0)

		if len(theQueue) == 0:
			print("distributeEvent2: Warning - No registrations for event " + theEvent + ".")

		for handlerInfo in theQueue:
			dispatchEvent(thePublisher, theEvent, publisherDefinedData, handlerInfo)

	return (0)

#
# distributeEvent - Touch all devices in the deque given.
#	theQueue, theEvent: as defined in theHandler info at addToControllerEventDeque()
#
def distributeEvent3(thePublisher, theEvent, theSubscriber, publisherDefinedData):

	global eventPublishers

	if theSubscriber:
		# load a deque with a single entry (no searching necessary) just go to deque the single handlerInfo entry
		theQueue = targettedEvents.get(thePublisher + "." + theEvent + "." + theSubscriber, 0)
	else:
		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			theQueue = 0

	if not theQueue or len(theQueue) == 0:
		print("distributeEvent: Warning - No registrations for event " + theEvent + ".")
		return (0)

	publisherDefinedData['theEvent'] = theEvent
	publisherDefinedData['publisher'] = thePublisher
	publisherDefinedData['timestamp'] = time.mktime(time.localtime())

	for aSubscriber, theHandler, handlerDefinedData in theQueue:
		if (theSubscriber == 0) or (theSubscriber == aSubscriber):
			# Add event, timestamp, and publisher
			eventParameters = publisherDefinedData
			eventParameters.update(handlerDefinedData)
			theHandler(theEvent, eventParameters)
	return (0)

#
# Note this turned out to be slower than just a standare for loop like above...
# Deques only have an advantage on looping through where you are deleting items, otherwise it is pretty close parity with list traversal...
# we chose to use deque because of the delete atvantage (rare in this case) and the fundamental parity in performaance with list otherwise.
def distributeEvent4(thePublisher, theEvent, theSubscriber, publisherDefinedData):

	global eventPublishers

	if theSubscriber:
		# load a deque with a single entry (no searching necessary) just go to deque the single handlerInfo entry
		theQueue = targettedEvents.get(thePublisher + "." + theEvent + "." + theSubscriber, 0)
	else:
		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			theQueue = 0

	if not theQueue or len(theQueue) == 0:
		print("distributeEvent: Warning - No registrations for event " + theEvent + ".")
		return (0)

	publisherDefinedData['theEvent'] = theEvent
	publisherDefinedData['publisher'] = thePublisher
	publisherDefinedData['timestamp'] = time.mktime(time.localtime())

	theMax = len(theQueue)
	for index in range(theMax):
		aSubscriber, theHandler, handlerDefinedData = theQueue[0]
		if (theSubscriber == 0) or (theSubscriber == aSubscriber):
			# Add event, timestamp, and publisher
			eventParameters = publisherDefinedData
			eventParameters.update(handlerDefinedData)
			theHandler(theEvent, eventParameters)
			theQueue.rotate(-1)

	return (0)


#
# distributeEvent - Touch all devices in the deque given.
#	theQueue, theEvent: as defined in theHandler info at addToControllerEventDeque()
#
def distributeEvent(thePublisher, theEvent, theSubscriber, publisherDefinedData):

	global eventPublishers

	try:
		theQueue = eventPublishers[thePublisher][theEvent]
	except:
		print("distributeEvent: Publisher " + str(thePublisher) + " is not registered to publish " + theEvent + ".")
		return (0)

	if len(theQueue) == 0:
		print("distributeEvent: Warning - No registrations for event " + theEvent + ".")

	for aSubscriber, theHandler, handlerDefinedData in theQueue:
		if (theSubscriber == 0) or (theSubscriber == aSubscriber):
			# Add event, timestamp, and publisher
			eventParameters = publisherDefinedData
			eventParameters.update(handlerDefinedData)
			eventParameters['theEvent'] = theEvent
			eventParameters['publisher'] = thePublisher
			eventParameters['timestamp'] = time.mktime(time.localtime())
			theHandler(theEvent, eventParameters)
			if theSubscriber != 0: break
	return (0)

def	testCodeNoOp(eventID, eventParameters):

	global eventsDelivered

	#print ("testCodeNoOp: received event \'" + eventID + "\' event  with eventParameters of " + str(eventParameters))
	eventsDelivered = eventsDelivered + 1

	return

def	testCodeOnEvent(eventID, eventParameters):

	print ("testCodeOnEvent: received \'" + eventID + "\' event  with eventData of " + str(eventParameters))

def	testCodeUpdateEvent(eventID, eventParameters):

	print ("testCodeUpdateEvent: Received \'" + eventID + "\' event with eventData of " + str(eventParameters))

#=======================

def eventTimeTestLow( subscribeEvnts, unsubscribeEvnts, registerPub, distributeEvnts):

	global eventPublishers
	global eventsDelivered
	global targettedEvents

	resetGlobals()
	startTime = timer()

	# make 100 publishers of 4 events

	for index in range(100):
		registerPub(['on', 'off', 'update', 'fastOn'], 'testCode' + str(index))

	# make 100 subscribers each with 4 events

	for index in range(100):
		subscribeEvnts(['on', 'off', 'update', 'fastOn'], 'testCode1', testCodeNoOp,{"HandlerDefinedData":"gregsUpdateEvent spoecific data"},"subscriber"+str(index) )
		subscribeEvnts(['on', 'off', 'update', 'fastOn'], 'testCode' + str(index), testCodeNoOp,{"HandlerDefinedData":"gregsUpdateEvent spoecific data"},"subscriber"+str(index) )
		subscribeEvnts(['on', 'off', 'update', 'fastOn'], 'testCode' + str(index), testCodeNoOp,{"HandlerDefinedData":"gregsUpdateEvent spoecific data"},"subscriber"+str(int(index/10)) )
		#print("subscribed subscriber \'subscriber"+str(index) + "\' to publisher \'" + 'testCode' + str(index) + "\'")

	# distribute all events 1000 times

	for index in range(10000):
		distributeEvnts('testCode1', 'off', "subscriber55", {"PublisherData":"Is Here"})

		distributeEvnts('testCode25', 'on', 0, {"PublisherData":"Is Here"})
		distributeEvnts('testCode50', 'off', 0, {"PublisherData":"Is Here"})
		distributeEvnts('testCode75', 'update', 0, {"PublisherData":"Is Here"})
		distributeEvnts('testCode99', 'fastOn', 0, {"PublisherData":"Is Here"})

	endTime = timer()

	return endTime - startTime


#=======================
#======================= Test Functions
#=======================
def eventTimeTest(subscribeEvnts, unsubscribeEvnts, registerPub, distributeEvnts):
	accumulatedTime = 0
	divisor = 0
	perNumber = 0
	global eventsDelivered

	eventsDelivered = 0

	startTime = timer()

	for index in range(10):
		elapsedTime = eventTimeTestLow(subscribeEvnts, unsubscribeEvnts, registerPub, distributeEvnts)
		accumulatedTime = accumulatedTime + elapsedTime
		divisor = divisor + 1
		if perNumber == 0: perNumber = eventsDelivered
	endTime = timer()

	print(str(eventsDelivered) + " events delivered in average time of " + str(
		elapsedTime / divisor) + " seconds per " + str(perNumber) + " for a total time of " + str(
		endTime - startTime) + " seconds.")



def functionalTest(subscribeEvnts, unsubscribeEvnts, registerPub, distributeEvnts):

	global eventPublishers
	global eventsDelivered
	global targettedEvents

	resetGlobals()
	#Functional Test

	registerPub(['on','off'], 'testCode')

	subscribeEvnts(['on','off'], 'testCode', testCodeOnEvent, {"HandlerDefinedData":"Goes Here"}, "testCode")

	subscribeEvnts(['DevUpdate'], 'Indigo', testCodeUpdateEvent, {"HandlerDefinedData":"gregsUpdateEvent spoecific data"}, "testCode")

	print( "BEFORE EventPublishers: " + str(eventPublishers))
	print( "BEFORE targettedEvents: " + str(targettedEvents))

	distributeEvnts('testCode', 'off', 0, {"PublisherData":"Is Here"})
	distributeEvnts('Indigo', 'DevUpdate', 0, {"PublisherData":"Is Here"})
	distributeEvnts('greg', 'on', 0, {"PublisherData":"Is Here"})
	distributeEvnts('Indigo', 'blah', 0, {"PublisherData":"Is Here"})

	unsubscribeEvnts(['DevUpdate'], 'Indigo', testCodeUpdateEvent, "testCode")
	distributeEvnts('Indigo', 'DevUpdate', 0, {"PublisherData": "Is Here"})
	distributeEvnts('testCode', 'off', 0, {"PublisherData":"Is Here"})
	unsubscribeEvnts(['on','off'], 'testCode', testCodeOnEvent, "testCode")
	distributeEvnts('testCode', 'off', 0, {"PublisherData":"Is Here"})
	print( "AFTER EventPublishers: " + str(eventPublishers))
	print( "AFTER targettedEvents: " + str(targettedEvents))

	# add 100 subscribers, then delete them
	registerPub("abcdefg", 'testPublisher')	# its a trick, each letter will act as a separate event type
	print( "Subscribe/Unsubscribe test - EventPublishers: " + str(eventPublishers))
	for index in range(100):
		for eventID in "abcdefg":
			subscribeEvnts([eventID], 'testPublisher', testCodeOnEvent, {"HandlerDefinedData": "Goes Here"}, "testCode" + str(index))
	print( "Subscribe/Unsubscribe test - EventPublishers LOADED: " + str(eventPublishers))
	for index in range(100):
		unsubscribeEvnts("acf", 'testPublisher', testCodeOnEvent, "testCode" + str(index))
		unsubscribeEvnts("b", 'testPublisher', testCodeOnEvent, "testCode" + str(index))
		unsubscribeEvnts(0, 'testPublisher', testCodeOnEvent, "testCode" + str(index))
	print( "Subscribe/Unsubscribe test - EventPublishers EMPTIED: " + str(eventPublishers))

	for index in range(100):
		for eventID in "abcdefg":
			subscribeEvnts([eventID], 'testPublisher', testCodeOnEvent, {"HandlerDefinedData": "Goes Here"}, "testCode" + str(index))
	print( "Subscribe/Unsubscribe test - EventPublishers LOADED2: " + str(eventPublishers))
	print( "Subscribe/Unsubscribe test - targettedEvents LOADED2: " + str(targettedEvents))
	unsubscribeEvnts(0, 'testPublisher', testCodeOnEvent, 0)
	print( "Subscribe/Unsubscribe test - EventPublishers EMPTIED2: " + str(eventPublishers))
	print( "Subscribe/Unsubscribe test - targettedEvents EMPTIED2: " + str(targettedEvents))

	return

#=======================
#======================= MAIN Entry
#=======================


# functionalTests
print(" ")
print(" subscribeToEvents ")
functionalTest(subscribeToEvents, unsubscribeFromEvents, registerPublisher, distributeEvent)
print(" ")
print(" subscribeToEvents2 ")
functionalTest(subscribeToEvents2, unsubscribeFromEvents, registerPublisher, distributeEvent2)
print(" ")
print(" subscribeToEvents3 ")
functionalTest(subscribeToEvents3, unsubscribeFromEvents3, registerPublisher, distributeEvent3)

# Time Tests

eventTimeTest(subscribeToEvents, unsubscribeFromEvents, registerPublisher, distributeEvent)
eventTimeTest(subscribeToEvents2, unsubscribeFromEvents, registerPublisher, distributeEvent2)
eventTimeTest(subscribeToEvents3, unsubscribeFromEvents3, registerPublisher, distributeEvent3)

quit()


testDeque = deque()

testDeque.append(['a','b','c'])
testDeque.append(['d','e','f'])
testDeque.append(['d','e','f'])
testDeque.append(['h','i','j'])
testDeque.append(['1','2','3'])
print(str(len(testDeque)))
# delete the unknown element
theMax = len(testDeque)
for index in range(theMax):
	if testDeque[0] == ['x','y','z']:
		testDeque.popleft()
	else:
		testDeque.rotate(-1)

# view the deque manual
theMax = len(testDeque)
for index in range(theMax):
	print(str(testDeque[0]))
	testDeque.rotate(-1)

# delete the middle element
theMax = len(testDeque)
for index in range(theMax):
	if testDeque[0] == ['d','e','f']:
		testDeque.popleft()
	else:
		#print(str(testDeque))
		testDeque.rotate(-1)
		#print(str(testDeque))
print(" ")
# view the deque
print(str(testDeque))

# delete the middle element
theMax = len(testDeque)
for index in range(theMax):
	if testDeque[0] == ['a','b','c']:
		testDeque.popleft()
	else:
		testDeque.rotate(-1)
print(" ")
# view the deque
print(str(testDeque))

# delete the middle element
theMax = len(testDeque)
for index in range(theMax):
	if testDeque[0] == ['h','i','j']:
		testDeque.popleft()
	else:
		testDeque.rotate(-1)
print(" ")
# view the deque
print(str(testDeque))

print(str(len(testDeque)))
quit()



theDict = {}

def addToDict(theNewDict):
	global theDict

	theDict[str(theNewDict['theName'] + "alt")] = theNewDict
	theDict['AdditionalData'] = 1234
	#print theDict


#for x in range(100):
x = 1
aDict = {'theName':str('EntryName'+str(x)), 'theVal':x}
print str(aDict)
addToDict(aDict)
print str(aDict)

quit()

random.seed()

potentialCommandList = ['one','two','three']
potentialCommandList = []

for aCommand in potentialCommandList:
	print aCommand

quit()

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

