__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

# import json
import os
import traceback
import datetime

import indigo
import mmLib_Log
import mmLib_Low
import mmLib_Low
from collections import deque
from timeit import default_timer as timer
import time
import pprint

# Dispatch timeout in seconds
MM_DISPATCH_TIMEOUT = 15

# The command Queue
pendingCommands = deque()

############################################################################################
#
# MotionMap command queue processing
#
# Queue entries are deque entries that contain:
#	[theMMDevice(object), theCommand(string), commandParameters(dictionary)]
# corresponding to element 0,1, and 2 respectively
#
############################################################################################
############################################################################################

############################################################################################
# qInit - initialize command queue
############################################################################################

def qInit():

	global pendingCommands

	mmLib_Log.logForce("Initializing command queue")
	pendingCommands = deque()


	return(0)

############################################################################################
# qTimer - periodic time to check to see if we are stuck
############################################################################################
def qTimer(theParameters):

	mmLib_Log.logDebug(">>>CommandQ qTimer")
	if pendingCommands:
		theCommandParameters = pendingCommands[0]
		try:
			dispatchTime = theCommandParameters["dispatchTime"]
		except:
			mmLib_Log.logForce(">>>CommandQ command was never dispatched: " + str(theCommandParameters))
			startQ() 		# start the command queue again
			return(0)		# if a command was dispatched, the timer should have already been reset, so return 0 to not reset it again

		# The command on top of the queue simply timed out

		timeoutQ()

	return(0)		# Nothing Pending.. No need for timer

############################################################################################
# qPrint - print given deque (deck)
############################################################################################

def qPrint(theQ):
	map( pprint.pprint ,theQ)

############################################################################################
# qDelete - delete n entry from queue deque (deck)
############################################################################################
def qDelete(theQ, n):
	theQ.rotate(-n)
	theQ.popleft()
	theQ.rotate(n)

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
# emptyQ - empty the whole Queue
#	theCommandParameters is a required parameter because of architecture, but it is unused here
############################################################################################
def emptyQ(theCommandParameters):
	pendingCommands.clear()

############################################################################################
# popQ
#	theCommandParameters is a required parameter because of architecture, but it is unused here
############################################################################################
def popQ(theCommandParameters):
	if len(pendingCommands) > 0:dequeQ( 1 )

############################################################################################
# restartQ
#	theCommandParameters is a required parameter because of architecture, but it is unused here
############################################################################################
def restartQ(theCommandParameters):
	if len(pendingCommands) > 0:dequeQ( 0 )

############################################################################################
# printQ
#	theCommandParameters is a required parameter because of architecture, but it is unused here
############################################################################################
def printQ(theCommandParameters):

	displayQueue = "\n========================================="
	displayQueue = displayQueue + "\n======= Displaying Command Queue ========"
	displayQueue = displayQueue + "\n========================================="
	displayQueue = displayQueue + "\ndeviceName, command, theValue"

	theCount = 0
	for theCommandParameters in pendingCommands:                   # iterate over the deque's elements

		try:
			theDevice = mmLib_Low.MotionMapDeviceDict[theCommandParameters['theDevice']]
			theDeviceName = theDevice.deviceName
		except:
			theDeviceName = "none"

		try:
			theCommand = theCommandParameters["theCommand"]
		except:
			theCommand = "none"

		try:
			theValue = theCommandParameters['theValue']
		except:
			theValue = "none"

		displayQueue = displayQueue + '\n' + str(theCount) + ') ' + theDeviceName + ", " + theCommand + ", " + str(theValue)
		if theCount == 0:
			try:
				dispatchTime = theCommandParameters["dispatchTime"]
				displayQueue = displayQueue + " (Running for " + str(time.time() - dispatchTime) + " seconds, Enqueued " + str(time.time() - theCommandParameters["enqueueTime"]) + " seconds ago)"
			except:
				displayQueue = displayQueue + " (Not dispatched yet, Enqueued " + str(time.time() - theCommandParameters["enqueueTime"]) + " seconds ago)"
		else:
			displayQueue = displayQueue + " (Enqueued " + str(time.time() - theCommandParameters["enqueueTime"]) + " seconds ago)"

		theCount = theCount + 1

	mmLib_Log.logReportLine("Display MotionMap Queue\n" + displayQueue + "\n\n")

############################################################################################
# timeoutQ - the entry in the top of the command queue timed out
############################################################################################
def timeoutQ():

	if pendingCommands:
		theCommandParameters = pendingCommands[0]
		theMMDevice = mmLib_Low.MotionMapDeviceDict[theCommandParameters['theDevice']]
		mmLib_Log.logForce("*** timeoutQ Error: " + theMMDevice.deviceName + " " + theCommandParameters['theCommand'])
		theMMDevice.errorCommandLow(theCommandParameters, 'Timeout' )
	else:
		mmLib_Log.logDebug("timeoutQ called with empty queue")

	return(0)

############################################################################################
# dispatchQ - dispatch the first entry in the queue... on error, return nonzero
############################################################################################
def dispatchQ():
	localError = 0
	if pendingCommands:
		qEntry = pendingCommands[0]
		theMMDevice = mmLib_Low.MotionMapDeviceDict[qEntry['theDevice']]
		theCommandParameters = qEntry
		mmLib_Log.logDebug("dispatchQ: " + theMMDevice.deviceName + " " + theCommandParameters['theCommand'])
		qEntry["dispatchTime"] = time.time()
		localError = theMMDevice.dispatchCommand(theCommandParameters)

		if localError in ['one', 'two']:
			localError = 0  # this is normal, the command is still in process

		if localError:
			# All other error codes are going to result in dequeue... typically this will be 'Dque' (meaning command is running async, no reason to wait) or 'Done' (meaning the command completed)
			mmLib_Log.logVerbose("*** Dispatching command " + theCommandParameters['theCommand'] + " for " + theMMDevice.deviceName + " yielded result code " + str(localError))
	else:
		mmLib_Log.logDebug("dispatchQ called with empty queue")

	return localError


############################################################################################
# startQ - Start Queue Processing, remove entries on top of the queue when there was an error dispatching commands
############################################################################################
def startQ():

	while pendingCommands:
		# Keep looping until you get a 0 result code (means in process), or you run out of pending commands
		if dispatchQ():
			# there was an error dispatching the command... dequeue it and try the next command
			pendingCommands.popleft()
		else:
			# The command is in the queue and running, start the timeout timer
			qEntry = pendingCommands[0]

			mmLib_Low.registerDelayedAction({'theFunction': qTimer, 'timeDeltaSeconds': MM_DISPATCH_TIMEOUT, 'theDevice': "CommandQueue", 'timerMessage': "15 second timeout for: " + qEntry["theDevice"] + " " + qEntry["theCommand"]})
			break

	if not pendingCommands:
		mmLib_Low.cancelDelayedAction(qTimer)

	return(0)

############################################################################################
# findQ = does not look into first queue element, its already being processed
############################################################################################
def findQ(theDevice, theCommandParameters, findDirective):

	n=0
	targetID = theDevice.deviceName
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
############################################################################################
def flushQ(theDevice, theCommandParameters, matchingEntries):

	n=findQ(theDevice, theCommandParameters, matchingEntries)
	if n:
		mmLib_Log.logForce("flushQ - flushing queued command " + theDevice.deviceName + ": " + theCommandParameters["theCommand"])
		qDelete(pendingCommands, n)

	return n

############################################################################################
#
# getQTopDev
#
############################################################################################
def getQTopDev():
	theDev = 0

	if pendingCommands:
		qEntry = pendingCommands[0]
		theName = qEntry["theDevice"]
		try:
			theDev = mmLib_Low.MotionMapDeviceDict[theName]
		except:
			pass

	return theDev

############################################################################################
#
# enqueQ
#
############################################################################################
def enqueQ(theTargetDevice, theCommandParameters, flushDirective ): # theCommandParameters is a dictionary

	startTheQueue = not pendingCommands

	if flushDirective: flushQ(theTargetDevice, theCommandParameters, flushDirective)    # Get rid of the old ones if asked
	qEntry = theCommandParameters
	qEntry['theIndigoDeviceID'] = theTargetDevice.devIndigoID
	qEntry["enqueueTime"] = time.time()

	pendingCommands.append(qEntry)

	if startTheQueue:
		startQ() # Start Command Queue Processing

############################################################################################
#
# dequeQ
#
############################################################################################
def dequeQ( dequeueFirst ): # theCommandParameters is a dictionary

	if dequeueFirst:
		try:
			pendingCommands.popleft()		# pop if needed
		except:
			mmLib_Log.logWarning("dequeQ: Pop called, but the queue is empty")

	startQ() 				# Start Command Queue Processing
