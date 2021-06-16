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
timeTagDict = {}
canceledTimeTags = {}

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
			dispatchTime = theCommandParameters['dispatchTime']
		except:
			mmLib_Log.logForce(">>>CommandQ command was never dispatched")
			#mmLib_Log.logForce(">>>CommandQ command was never dispatched: Device " + str(theCommandParameters.get('theDevice', 'Unknown') + ". Command " + theCommandParameters.get('theCommand', 'Unknown') ))
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

		timeTag = theCommandParameters['enqueueTime']

		theDeviceName = theCommandParameters.get('theDevice', 'Unknown')
		theCommand = theCommandParameters.get('theCommand', 'Unknown')
		theValue = theCommandParameters.get('theValue', 'Unknown')

		displayQueue = displayQueue + '\n' + str(theCount) + ') ' + theDeviceName + ", " + theCommand + ", " + str(theValue)
		if canceledTimeTags.get(timeTag, None) != None: displayQueue = displayQueue + " CANCELLED"

		if theCount == 0:
			try:
				dispatchTime = theCommandParameters['dispatchTime']
				displayQueue = displayQueue + " (Running for " + str(time.time() - dispatchTime) + " seconds, Enqueued " + str(time.time() - theCommandParameters['enqueueTime']) + " seconds ago)"
			except:
				displayQueue = displayQueue + " (Not dispatched yet, Enqueued " + str(time.time() - theCommandParameters['enqueueTime']) + " seconds ago)"
		else:
			displayQueue = displayQueue + " (Enqueued " + str(time.time() - theCommandParameters['enqueueTime']) + " seconds ago)"

		theCount = theCount + 1
	displayQueue = displayQueue + "\n=========================================\n"
	if theCount:
		displayQueue = displayQueue + str(theCount)
		if theCount == 1:
			displayQueue = displayQueue + " Entry reported."
		else:
			displayQueue = displayQueue + " Entries reported."
	else:
		displayQueue = displayQueue + "\n=========================================\nNo Entries to report."

	mmLib_Log.logReportLine("Display MotionMap Queue\n" + displayQueue + "\n\n")


	mmLib_Log.logReportLine("\ntimeTagDict:\n" + str(timeTagDict) + "\n\n" + "canceledTimeTags:\n" + str(canceledTimeTags) + "\n\n")

############################################################################################
# timeoutQ - the entry in the top of the command queue timed out
############################################################################################
def timeoutQ():

	if pendingCommands:
		theCommandParameters = pendingCommands[0]
		theMMDevice = theCommandParameters['theMMDevice']
		mmLib_Log.logForce("*** timeoutQ Error: " + theCommandParameters['theDevice'] + " " + theCommandParameters['theCommand'])
		theMMDevice.errorCommandLow(theCommandParameters, 'Timeout' )
	else:
		mmLib_Log.logDebug("timeoutQ called with empty queue")

	return(0)

############################################################################################
# dispatchQ - dispatch the first entry in the queue... on error, return nonzero
############################################################################################
def	dispatchQ():

	global pendingCommands
	global timeTagDict
	global canceledTimeTags

	localError = 0

	while pendingCommands:
		# Keep looping to skip all cancelled commands

		theCommandParameters = pendingCommands[0]
		theMMDevice = theCommandParameters['theMMDevice']
		timeTag = theCommandParameters['enqueueTime']
		CommandID = theCommandParameters['theDevice'] + "." + theCommandParameters['theCommand']

		if canceledTimeTags.get(timeTag, None) != None:
			# commandQueue entry was in cancelled list... Dequeue it
			canceledTimeTags.pop(timeTag, None)
			timeTagDict.pop(CommandID, None)
			if len(pendingCommands) == 1:
				return(1)	# the caller StartQ() will dequeue this final command based on this error
			else:
				# Dequeue the command ourselves and Continue looking for a valid command
				pendingCommands.popleft()
		else:
			# not in cancel list, run the proc
			theCommandParameters['dispatchTime'] = time.time()
			#run the proc
			try:
				localError = theMMDevice.dispatchCommand(theCommandParameters)
				#if theMMDevice.debugDevice: mmLib_Log.logForce("dispatchCommand result " + str(localError) + " for " + theMMDevice.deviceName + " theCommandParameters: " + str(theCommandParameters))
			except:
				mmLib_Log.logError("DispatchCommand Failed.")
				mmLib_Log.logError("    Commmand Parameters: " + str(theCommandParameters))
				localError = 'Dque'
				# Error was noted in log... continue
				pass

			if localError in ['one', 'two', 'None']:
				localError = 0  # this is normal, the command is still in process

			if localError == 'Dque':
				# the pendingCommands.popleft will happen in StartQ below... do the rest of the cleanup here
				canceledTimeTags.pop(timeTag, None)
				timeTagDict.pop(CommandID, None)
			elif localError:
				mmLib_Log.logForce(CommandID + " Resulted in ErrorCode: " + str(localError))

			break	# Either way, we found the proc and are done processing it, so we are done with the loop
	return localError


############################################################################################
# startQ - Start Queue Processing, remove entries on top of the queue when there was an error dispatching commands
############################################################################################
def startQ():

	global pendingCommands

	while pendingCommands:
		# Keep looping until you get a 0 result code (means in process), or you run out of pending commands
		if dispatchQ():
			# there was an error dispatching the command... dequeue it and try the next command
			pendingCommands.popleft()
		else:
			# The command is in the queue and running, start the timeout timer
			qEntry = pendingCommands[0]

			mmLib_Low.registerDelayedAction({'theFunction': qTimer, 'timeDeltaSeconds': MM_DISPATCH_TIMEOUT, 'theDevice': "CommandQueue", 'timerMessage': "15 second timeout for: " + qEntry['theDevice'] + " " + qEntry['theCommand']})
			break

	if not pendingCommands:
		mmLib_Low.cancelDelayedAction(qTimer)

	return(0)

############################################################################################
#
# flushQ - note we only look for a single entry because we only support 1 queue entry per command type per device
#
#	Flush all PendingCommands entries whos device name matches theCommandParameters['theDevice'] and the other elements listed in matchingEntries match the provided commandParameters Entry (theCommandParameters)
#
# ############################################################################################
def flushQ(theDeviceName, theCommandParameters, matchingEntries):

	#All you need to do is move the timeTag (if one) to canceledTimeTags

	global pendingCommands
	global timeTagDict
	global canceledTimeTags

	# Look up the commandID
	CommandID = theCommandParameters['theDevice'] + "." + theCommandParameters['theCommand']

	try:
		timeTag = timeTagDict[CommandID]
	except:
		#Not found, No work to do
		return 0

	timeTagDict.pop(CommandID, None)			# take the entry out of the time tag queue so it wont be found again
	canceledTimeTags[timeTag] = 1				# and mark this found entry cancelled. when running through the queue later, we will see this flag and not dispatch the command

	return 0

############################################################################################
#
# getQTopDev
#
############################################################################################
def getQTopDev():

	global pendingCommands

	theDev = 0

	if pendingCommands:
		qEntry = pendingCommands[0]
		theName = qEntry['theDevice']
		try:
			theDev = mmLib_Low.MotionMapDeviceDict[theName]
		except:
			# It can never get here... dont do anything
			pass

	return theDev

############################################################################################
#
# enqueQ
#
############################################################################################
def enqueQ(theTargetDevice, theCommandParameters, flushDirective):


	global pendingCommands
	global timeTagDict
	global canceledTimeTags

	localParameters = {}

	# theCommandParameters is a dictionary

	startTheQueue = not pendingCommands

	timeTag = time.time()
	CommandID = theCommandParameters['theDevice'] + "." + theCommandParameters['theCommand']

	try:
		theCommandParameters['theMMDevice'] = theTargetDevice
		theCommandParameters['theIndigoDeviceID'] = theTargetDevice.devIndigoID
		theCommandParameters['enqueueTime'] = timeTag
	except Exception as err:
		mmLib_Log.logError("Cannot Enqueue mmDevice: " + str(theTargetDevice) + " Error: " + str(err))

	if flushDirective:
		flushQ(theTargetDevice, theCommandParameters, flushDirective)  # Get rid of the old ones if asked
	else:
		mmLib_Log.logDebug("No flush Directive for mmDevice " + str(theTargetDevice))

	pendingCommands.append(theCommandParameters)
	timeTagDict[CommandID] = timeTag	# this will be used to cancel this command by timeTag in the future if need be

	if startTheQueue:
		startQ() # Start Command Queue Processing

############################################################################################
#
# dequeQ - Dequeue first pendingCommand (optional) and restart the queue
#
############################################################################################
def dequeQ( dequeueFirst ):
	global pendingCommands
	global timeTagDict
	global canceledTimeTags
	# queue entries are commandParameter dictionaries
	if dequeueFirst == 1:
		if pendingCommands:
			theCommandParameters = pendingCommands[0]
			timeTag = theCommandParameters['enqueueTime']
			CommandID = theCommandParameters['theDevice'] + "." + theCommandParameters['theCommand']

			canceledTimeTags.pop(timeTag, None)
			timeTagDict.pop(CommandID, None)
			pendingCommands.popleft()		# pop the command
		else:
			mmLib_Log.logWarning("dequeQ: Pop called, but the queue is empty")

	startQ() 				# Start Command Queue Processing


