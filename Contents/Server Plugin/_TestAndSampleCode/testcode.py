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

eventPublishers = {'Indigo': {'AtributeUpdate':deque([]),'DevRcvCmd':deque([]),'DevCmdComplete':deque([]),'DevCmdErr':deque([])}, 'MMSys': {'XCmd':deque([])}}
targettedEvents = {}
eventsDelivered = 0

def resetGlobals():
	global 	eventPublishers
	global 	targettedEvents

	eventPublishers = {'Indigo': {'AtributeUpdate':deque([]),'DevRcvCmd':deque([]),'DevCmdComplete':deque([]),'DevCmdErr':deque([])}, 'MMSys': {'XCmd':deque([])}}

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

	subscribeEvnts(['AtributeUpdate'], 'Indigo', testCodeUpdateEvent, {"HandlerDefinedData":"gregsUpdateEvent spoecific data"}, "testCode")

	print( "BEFORE EventPublishers: " + str(eventPublishers))
	print( "BEFORE targettedEvents: " + str(targettedEvents))

	distributeEvnts('testCode', 'off', 0, {"PublisherData":"Is Here"})
	distributeEvnts('Indigo', 'AtributeUpdate', 0, {"PublisherData":"Is Here"})
	distributeEvnts('greg', 'on', 0, {"PublisherData":"Is Here"})
	distributeEvnts('Indigo', 'blah', 0, {"PublisherData":"Is Here"})

	unsubscribeEvnts(['AtributeUpdate'], 'Indigo', testCodeUpdateEvent, "testCode")
	distributeEvnts('Indigo', 'AtributeUpdate', 0, {"PublisherData": "Is Here"})
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
#======================= Event Tests Entry
#=======================

if 0:
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



#=======================
#======================= MAIN Entry
#=======================

python --version
quit()

class aTestObject:

	def __init__(self, value1, value2, value3, value4, value5, value6, value7, value8, value9):
		self.val0 = 0
		self.val1 = value1
		self.val2 = value2
		self.val3 = value3
		self.val4 = value4
		self.val5 = value5
		self.val6 = value6
		self.val7 = value7
		self.val8 = value8
		self.val9 = value9

		self.val10 = 10
		self.val11 = 11
		self.val12 = 12
		self.val13 = 13
		self.val14 = 14
		self.val15 = 15
		self.val16 = 16
		self.val17 = 17
		self.val18 = 18
		self.val19 = 19

		self.val20 = 20
		self.val21 = 21
		self.val22 = 22
		self.val23 = 23
		self.val24 = 24
		self.val25 = 25
		self.val26 = 26
		self.val27 = 27
		self.val28 = 28
		self.val29 = 29

		self.val30 = 30
		self.val31 = 31
		self.val32 = 32
		self.val33 = 33
		self.val34 = 34
		self.val35 = 35
		self.val36 = 36
		self.val37 = 37
		self.val38 = 38
		self.val39 = 39

		self.val40 = 40
		self.val41 = 41
		self.val42 = 42
		self.val43 = 43
		self.val44 = 44
		self.val45 = 45
		self.val46 = 46
		self.val47 = 47
		self.val48 = 48
		self.val49 = 49

		self.val50 = 50
		self.val51 = 51
		self.val52 = 52
		self.val53 = 53
		self.val54 = 54
		self.val55 = 55
		self.val56 = 56
		self.val57 = 57
		self.val58 = 58
		self.val59 = 59

		self.val60 = 60
		self.val61 = 61
		self.val62 = 62
		self.val63 = 63
		self.val64 = 64
		self.val65 = 65
		self.val66 = 66
		self.val67 = 67
		self.val68 = 68
		self.val69 = 69

		self.val70 = 70
		self.val71 = 71
		self.val72 = 72
		self.val73 = 73
		self.val74 = 74
		self.val75 = 75
		self.val76 = 76
		self.val77 = 77
		self.val78 = 78
		self.val79 = 79

		self.val80 = 80
		self.val81 = 81
		self.val82 = 82
		self.val83 = 83
		self.val84 = 84
		self.val85 = 85
		self.val86 = 86
		self.val87 = 87
		self.val88 = 88
		self.val89 = 89

		self.val90 = 90
		self.val91 = 91
		self.val92 = 92
		self.val93 = 93
		self.val94 = 94
		self.val95 = 95
		self.val96 = 96
		self.val97 = 97
		self.val98 = 98
		self.val99 = 99


# === version 7

def checkV1(o1, o2): return o1.val1 != o2.val1 and o2.val1 or 'same'
def checkV2(o1, o2): return o1.val2 != o2.val2 and o2.val2 or 'same'
def checkV3(o1, o2): return o1.val3 != o2.val3 and o2.val3 or 'same'
def checkV4(o1, o2): return o1.val4 != o2.val4 and o2.val4 or 'same'
def checkV5(o1, o2): return o1.val5 != o2.val5 and o2.val5 or 'same'
def checkV6(o1, o2): return o1.val6 != o2.val6 and o2.val6 or 'same'
def checkV7(o1, o2): return o1.val7 != o2.val7 and o2.val7 or 'same'
def checkV8(o1, o2): return o1.val8 != o2.val8 and o2.val8 or 'same'
def checkV9(o1, o2): return o1.val9 != o2.val9 and o2.val9 or 'same'

jumpDict7 = {'val1':checkV1, 'val2':checkV2,'val3':checkV3, 'val4':checkV4,'val5':checkV5, 'val6':checkV6,'val7':checkV7, 'val8':checkV8,'val9':checkV9}


def getDiff7(o1, o2, requestedParms):

	resultDict = {}

	for whichVal in requestedParms:
		try:
			result = jumpDict7[whichVal](o1,o2)
			if result != 'same':
				resultDict[whichVal] = result
				if requestedParms[whichVal]: requestedParms[whichVal](whichVal,resultDict )
		except: pass

	return resultDict


# === Version 6

theConverters = {}
theConverters['val1'] = lambda o1,o2: o1.val1 != o2.val1 and o2.val1 or 'same'
theConverters['val2'] = lambda o1,o2: o1.val2 != o2.val2 and o2.val2 or 'same'
theConverters['val3'] = lambda o1,o2: o1.val3 != o2.val3 and o2.val3 or 'same'
theConverters['val4'] = lambda o1,o2: o1.val4 != o2.val4 and o2.val4 or 'same'
theConverters['val5'] = lambda o1,o2: o1.val5 != o2.val5 and o2.val5 or 'same'
theConverters['val6'] = lambda o1,o2: o1.val6 != o2.val6 and o2.val6 or 'same'
theConverters['val7'] = lambda o1,o2: o1.val7 != o2.val7 and o2.val7 or 'same'
theConverters['val8'] = lambda o1,o2: o1.val8 != o2.val8 and o2.val8 or 'same'
theConverters['val9'] = lambda o1,o2: o1.val9 != o2.val9 and o2.val9 or 'same'


def getDiff6(o1,o2, requestedParms):

	global theConverters

	resultDict = {}

	for whichVal in requestedParms:
		try:
			localResult = theConverters[whichVal](o1,o2)
			if localResult != 'same':
				resultDict[whichVal] = localResult
				if requestedParms[whichVal]: requestedParms[whichVal](whichVal,resultDict )
		except: pass
	return resultDict


# ==== version 5 Just builds a record of all differences (ignoting requestedParms), and does not dispatch events

def getDiff5(o1, o2, requestedParms):

	try:
		resultDict = {o1.val1 != o2.val1 and 'val1': o2.val1 or 'same',
					o1.val2 != o2.val2 and 'val2': o2.val2 or 'same',
					o1.val3 != o2.val3 and 'val3': o2.val3 or 'same',
					o1.val4 != o2.val4 and 'val4': o2.val4 or 'same',
					o1.val5 != o2.val5 and 'val5': o2.val5 or 'same',
					o1.val6 != o2.val6 and 'val6': o2.val6 or 'same',
					o1.val7 != o2.val7 and 'val7': o2.val7 or 'same',
					o1.val8 != o2.val8 and 'val8': o2.val8 or 'same',
					o1.val9 != o2.val9 and 'val9': o2.val9 or 'same'}
	except:
		# Warning no such value in object
		return {}

	return resultDict


# ==== version 4


def getDiff4(o1, o2, requestedParms):

	resultDict = {}

	try:
		theDict1 = {'val1': o1.val1 != o2.val1 and o2.val1 or 'same',
					'val2': o1.val2 != o2.val2 and o2.val2 or 'same',
					'val3': o1.val3 != o2.val3 and o2.val3 or 'same',
					'val4': o1.val4 != o2.val4 and o2.val4 or 'same',
					'val5': o1.val5 != o2.val5 and o2.val5 or 'same',
					'val6': o1.val6 != o2.val6 and o2.val6 or 'same',
					'val7': o1.val7 != o2.val7 and o2.val7 or 'same',
					'val8': o1.val8 != o2.val8 and o2.val8 or 'same',
					'val9': o1.val9 != o2.val9 and o2.val9 or 'same'}
	except:
		# Warning no such value in object
		return resultDict

	for whichVal in requestedParms:
		try:
			if theDict1[whichVal] != 'same':
				resultDict[whichVal] = theDict1[whichVal]
				if requestedParms[whichVal]: requestedParms[whichVal](whichVal,resultDict )
		except: pass
	return resultDict



# version 3


# check 'val1' of o1/o2 and returns a dict with o2[val1] as the only entry if different. Otherwise, return {}
def checkVal1(o1, o2):
	if o1.val1 != o2.val1: return(o2.val1)
	return 'same'

def checkVal2(o1, o2):
	if o1.val2 != o2.val2: return(o2.val2)
	return 'same'

def checkVal3(o1, o2):
	if o1.val3 != o2.val3: return(o2.val3)
	return 'same'

def checkVal4(o1, o2):
	if o1.val4 != o2.val4: return(o2.val4)
	return 'same'

def checkVal5(o1, o2):
	if o1.val5 != o2.val5: return(o2.val5)
	return 'same'

def checkVal6(o1, o2):
	if o1.val6 != o2.val6: return(o2.val6)
	return 'same'

def checkVal7(o1, o2):
	if o1.val7 != o2.val7: return(o2.val7)
	return 'same'

def checkVal8(o1, o2):
	if o1.val8 != o2.val8: return(o2.val8)
	return 'same'

def checkVal9(o1, o2):
	if o1.val9 != o2.val9: return(o2.val9)
	return 'same'


jumpDict = {'val1':checkVal1, 'val2':checkVal2,'val3':checkVal3, 'val4':checkVal4,'val5':checkVal5, 'val6':checkVal6,'val7':checkVal7, 'val8':checkVal8,'val9':checkVal9}

def getDiff3(o1, o2, requestedParms):

	resultDict = {}

	for whichVal in requestedParms:
		try:
			result = jumpDict[whichVal](o1,o2)
			if result != 'same':
				resultDict[whichVal] = result
				if requestedParms[whichVal]: requestedParms[whichVal](whichVal,resultDict )
		except: pass
	return resultDict




# version 2

allSubEventsSupported = {'val1':0,'val2':0,'val3':0,'val4':0,'val5':0,'val6':0,'val7':0,'val8':0,'val9':0}


def getDiffMaster(o1, o2, requestedParms, masterHandler):

	resultDict = {}

	for whichVal in requestedParms:
		try:
			val1 = getattr(o1, whichVal)
			val2 = getattr(o2, whichVal)
			if val1 != val2:
				resultDict[whichVal] = val2
		except:
			pass
	return masterHandler('AtributeUpdate', resultDict)


def getDiff2(o1, o2, requestedParms, masterHandler):

	masterEventDict = {}
	deliveredEventsDict = {}

	for whichVal in requestedParms:
		try:
			val1 = getattr(o1,whichVal)
			val2 = getattr(o2,whichVal)
		except:
			pass
			continue

		if val1 != val2:
			# does this event have a special handler?
			if requestedParms[whichVal]:
				try:
					requestedParms[whichVal](whichVal,{whichVal:val2} )
					deliveredEventsDict[whichVal] = val2
				except:
					pass
					# message about undeliverable event
			else:
				# commemorate the undelivered event for the masterHandler
				masterEventDict[whichVal] = val2

	if masterEventDict != {}:
		if masterHandler:
			try:
				masterHandler('AtributeUpdate', masterEventDict)
				# and mark the events delivered
				deliveredEventsDict.update(masterEventDict)
			except:
				pass
				# message about failure to deliver master events
		else:
			# message that we have events targetted for master, but no master handler
			pass

	return deliveredEventsDict


# version 1 -
def getDiff1(o1, o2, requestedParms):

	if requestedParms == {}: return listAllDiffs(o1, o2, requestedParms)

	count = len(requestedParms)
	if not count: return {}

	resultDict = {}
	try:
		if 'val1' in requestedParms and o1.val1 != o2.val1:
			resultDict['val1'] = o2.val1
			count = count-1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val1']: requestedParms['val1']('val1',resultDict )
			if not count: return resultDict
	except: pass

	try:
		if 'val2' in requestedParms and o1.val2 != o2.val2:
			resultDict['val2'] = o2.val2
			count = count - 1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val2']: requestedParms['val2']('val2',resultDict )
			if not count: return resultDict
	except: pass

	try:
		if 'val3' in requestedParms and o1.val3 != o2.val3:
			resultDict['val3'] = o2.val3
			count = count - 1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val3']: requestedParms['val3']('val3',resultDict )
			if not count: return resultDict
	except: pass

	try:
		if 'val4' in requestedParms and o1.val4 != o2.val4:
			resultDict['val4'] = o2.val4
			count = count - 1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val4']: requestedParms['val4']('val4',resultDict )
			if not count: return resultDict
	except: pass

	try:
		if 'val5' in requestedParms and o1.val5 != o2.val5:
			resultDict['val5'] = o2.val5
			count = count - 1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val5']: requestedParms['val5']('val5',resultDict )
			if not count: return resultDict
	except: pass

	try:
		if 'val6' in requestedParms and o1.val6 != o2.val6:
			resultDict['val6'] = o2.val6
			count = count - 1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val6']: requestedParms['val6']('val6',resultDict )
			if not count: return resultDict
	except: pass

	try:
		if 'val7' in requestedParms and o1.val7 != o2.val7:
			resultDict['val7'] = o2.val7
			count = count - 1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val7']: requestedParms['val7']('val7',resultDict )
			if not count: return resultDict
	except: pass

	try:
		if 'val8' in requestedParms and o1.val8 != o2.val8:
			resultDict['val8'] = o2.val8
			count = count - 1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val8']: requestedParms['val8']('val8',resultDict )
			if not count: return resultDict
	except: pass

	try:
		if 'val9' in requestedParms and o1.val9 != o2.val9:
			resultDict['val9'] = o2.val9
			count = count - 1
			# Deliver the event if this sub event has a special handler
			if requestedParms['val9']: requestedParms['val9']('val9',resultDict )
			if not count: return resultDict
	except: pass

	return(resultDict)



# version 0 - just return list of all changes between the given objects... dont dispatch to event handler

def listAllDiffs(o1, o2, requestedParms):

	resultDict = {}
	try:
		if o1.val1 != o2.val1: resultDict['val1'] = o2.val1
	except: pass

	try:
		if o1.val2 != o2.val2: resultDict['val2'] = o2.val2
	except:
		pass

	try:
		if o1.val3 != o2.val3: resultDict['val3'] = o2.val3
	except:
		pass

	try:
		if o1.val4 != o2.val4: resultDict['val4'] = o2.val4
	except:
		pass

	try:
		if o1.val5 != o2.val5: resultDict['val5'] = o2.val5
	except:
		pass

	try:
		if o1.val6 != o2.val6: resultDict['val6'] = o2.val6
	except:
		pass

	try:
		if o1.val7 != o2.val7: resultDict['val7'] = o2.val7
	except:
		pass

	try:
		if o1.val8 != o2.val8: resultDict['val8'] = o2.val8
	except:
		pass

	try:
		if o1.val9 != o2.val9: resultDict['val9'] = o2.val9
	except:
		pass

	return(resultDict)


t1 = aTestObject(100,200,300,400,500,600,700,800,900)
t2 = aTestObject(101,201,300,400,500,600,700,801,901)


def eventHandlerNull(theEvent, eventParameters):
	return 0

def eventHandler(theEvent, eventParameters):
	print "got the event: " + str(theEvent) + " with parameters: " + str(eventParameters)
	return 0

def eventHandlerALL(theEvent, eventParameters):
	print "got the event: " + str(theEvent) + ". Processing all Differences: " + str(eventParameters)
	return 0

nIterations = 10000

def runTest(theTest, testName):

	lowestTime = 100000
	for n in range(10):
		startTime = timer()

		for i in range(nIterations):
			if testName in ["getDiff2","getDiff2M"]:
				if testName == "getDiff2":
					theTest(t1,t2,{'val1': eventHandlerNull, 'val2': eventHandlerNull}, 0)
				else:
					theTest(t1,t2,{'val1': 0, 'val2': 0}, eventHandlerNull)
			else:
				theTest(t1, t2, {'val1': eventHandlerNull, 'val2': eventHandlerNull})

		elapsedTime = timer() - startTime
		if elapsedTime < lowestTime: lowestTime = elapsedTime

	if testName in ["getDiff2","getDiff2M"]:
		if testName == "getDiff2":
			print(testName + ", Lowest Time: " + str(lowestTime) + " seconds. " + str(theTest(t1, t2, {'val1': eventHandler, 'val2': eventHandler}, 0)))
		else:
			print(testName + ", Lowest Time: " + str(lowestTime) + " seconds. " + str(theTest(t1, t2, {'val1': 0, 'val2': 0}, eventHandlerALL)))
	else:
		print(testName + ", Lowest Time: " + str(lowestTime) + " seconds. " + str(theTest(t1, t2, {'val1': eventHandler, 'val2': eventHandler})))

	return


def doNothingLarge(largeDict):
	pass
	return

def doNothingSmall(smallDict):
	pass
	return

def doNothing():
	pass
	return

def runTest1Parm(testName, parm1):

	lowestTime = 100000
	for n in range(10):
		startTime = timer()

		for i in range(nIterations):
			doNothingSmall(parm1)

		elapsedTime = timer() - startTime
		if elapsedTime < lowestTime: lowestTime = elapsedTime

	print(testName + ", Lowest Time: " + str(lowestTime) + " seconds. ")

	return

def runTest0Parm(testName):

	lowestTime = 100000
	for n in range(10):
		startTime = timer()

		for i in range(nIterations):
			doNothing()

		elapsedTime = timer() - startTime
		if elapsedTime < lowestTime: lowestTime = elapsedTime

	print(testName + ", Lowest Time: " + str(lowestTime) + " seconds. ")

	return

def parmPassingSpeedTest():
	localDictSmall = {"entry1":1, "entry2":2}
	localDictLarge = {}

	for x in range(100):
		localDictLarge['entry' + str(x)] = x

	runTest1Parm("runTest1Parm", localDictLarge)
	runTest1Parm("runTest1Parm", localDictSmall)
	runTest0Parm("runTest0Parm")

	return

t3 = t1
t1.val50 = 900
if t1 == t2: print "Equal"

quit()

startTime = timer()

for x in range(10000):
	t3 = t1

midTime = timer()

for x in range(10000):
	v1 = t1.val1
	v2 = t1.val2
	v55 = t1.val55
	v70 = t1.val70

endTime = timer()

print "T1/T2: " + str(midTime - startTime) + " " + str(endTime - midTime)

quit()

#Inside plugin.py, the events registration for update event should include a dict of sub-events of interest. Each one has its own event handler.
# That list will be used for the requestedParms value passed to getDiff1

# 1) make sure there is a registered handler for update events to this mmDev... if not, bail and ignore the event
# 2) call one of these routines (below -it will deliver sub events if they are registered in the update Event)
# 3) the routine below will return a dict of all relavent sub events... call the master handler from the mmDev if it is nonzero - as it wants the master update event
#		note: the mmdev doesnt have to register for both the master update event and sub events. If it wants sub events only, it can register the master handler as 0
#		similarly, if it wants only the master event, it can register the sub events {}.. all differences will be delivered to the master update handler registered for this mmDev
#		dont register empty handlers for both master and all sub-events... you will get no events

runTest(listAllDiffs, "listAllDiffs")
runTest(getDiff1, "getDiff1")
#runTest(getDiff3, "getDiff3")
#runTest(getDiff7, "getDiff7")
runTest(getDiff2, "getDiff2")
runTest(getDiff2, "getDiff2M")
#runTest(getDiff4, "getDiff4")
#runTest(getDiff5, "getDiff5")
#runTest(getDiff6, "getDiff6")
#runTest(getDiffMaster, "getDiffMaster")
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

