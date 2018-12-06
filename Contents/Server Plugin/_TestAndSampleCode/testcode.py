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



#====================================
#============  Main  ================
#====================================

# Delay Queue related stuff
delayQueue = []
delayedFunctionKeys = {}
lastDelayProcRunTime = 0
FractionalGranularity = .000001
fractionalIndex = FractionalGranularity

TIMER_QUEUE_GRANULARITY = 5

############################################################################################
# findDelayedAction -  find first instance of registered DelayedAction, return its trigger time
#
############################################################################################
def findDelayedAction(theFunction):
	global delayQueue

	try:
		bisectKey = delayedFunctionKeys[theFunction]
	except:
		bisectKey = 0

	return bisectKey


############################################################################################
# delayDelayedAction - cancel all occurances of previously registered DelayedAction
#
############################################################################################
def delayDelayedAction(theFunction, offsetInSeconds):
	global delayQueue
	theParameters = {}

	bisectKey = findDelayedAction(
		theFunction)  # bisectKey is the localtime in seconds when the proc is scheduled to run

	if bisectKey:
		newTime = (bisectKey - time.mktime(time.localtime())) + offsetInSeconds  # calculate new time offset

		theIndex = bisect.bisect_left(delayQueue, (bisectKey,))
		bisectTuple = delayQueue[theIndex]

		theParameters = bisectTuple[1]
		theParameters['timeDeltaSeconds'] = newTime

		cancelDelayedAction(theFunction)  # delete the old entry
		return (registerDelayedAction(theParameters))  # and add the new entry
	else:
		return (0)


############################################################################################
# cancelDelayedAction - cancel all occurances of previously registered DelayedAction
#
############################################################################################
def cancelDelayedAction(theFunction):
	global delayQueue
	global delayedFunctionKeys

	try:
		bisectKey = delayedFunctionKeys[theFunction]
		if bisectKey:
			# There is a function waiting
			delayedFunctionKeys[theFunction] = 0  # Reset delayedFunctionKeys... to no function waiting
		else:
			return
	except:
		return  # no function waiting

	delayQueue.pop(bisect.bisect_left(delayQueue, (bisectKey,)))


############################################################################################
# registerDelayedAction - call a function at whenSeconds time (granularity of TIMER_QUEUE_GRANULARITY seconds)
#
# theParameters Requirements:
#	theFunction			the function to call on requested elapsed time (not human readable) Function must return Timer Reset delta value in number of seconds. 0 means stop timer.
#	timeDeltaSeconds	the number of seconds to wait before timer expires
#	theDevice			Use DeviceName
#	timerMessage		Optional, recommended. English translation of reason for timer (for debugging). Use ProcName at least
#
#	Example registerDelayedAction({'theFunction': myProc, 'timeDeltaSeconds':60, 'timerMessage':"GregsOfficeLight.periodicTime"})
#
############################################################################################
def registerDelayedAction(parameters):
	global delayQueue
	global lastDelayProcRunTime
	global delayedFunctionKeys
	global fractionalIndex
	global FractionalGranularity

	fractionalIndex = fractionalIndex + FractionalGranularity
	if fractionalIndex >= 1.0: fractionalIndex = FractionalGranularity

	theFunction = parameters['theFunction']
	whenSeconds = parameters['timeDeltaSeconds'] + time.mktime(time.localtime())
	bisectKey = whenSeconds + fractionalIndex

	cancelDelayedAction(theFunction)  # we only support one entry for this function at a time

	if time.mktime(time.localtime()) >= whenSeconds:
		# Time already expired, do it now
		theFunction(parameters)
	else:
		parameters['executionTime'] = whenSeconds
		bisect.insort(delayQueue, (bisectKey, parameters))
		delayedFunctionKeys[theFunction] = bisectKey  # We now mark this function as waiting

	if lastDelayProcRunTime:
		# Round the time up to the next timer run and return it for the convenience of the caller
		timeDelta = int((time.mktime(
			time.localtime()) - lastDelayProcRunTime) % TIMER_QUEUE_GRANULARITY)  # time since the last pass through timer
		if timeDelta: timeDelta = (TIMER_QUEUE_GRANULARITY - timeDelta)
		newSeconds = whenSeconds + timeDelta
	else:
		newSeconds = whenSeconds

	# Returns time when the function will be run
	return newSeconds


############################################################################################
# mmGetDelayedProcsList - process timer functions registered for above
#
############################################################################################
def mmGetDelayedProcsList(theCommandParameters):
	global delayQueue
	theMessage = '\n'

	try:
		specificDevice = theCommandParameters['theDevice']
	except:
		specificDevice = ''

	try:
		specificProc = theCommandParameters['proc']
	except:
		specificProc = ''

	if specificDevice != '':
		theMessage = theMessage + "==== DelayedProcs related to device " + specificDevice + " ====\n"
	else:
		if specificProc != '':
			theMessage = theMessage + "==== DelayedProcs related to proc name " + specificProc + " ====\n"
		else:
			theMessage = theMessage + "==== DelayedProcs for all devices ====\n"

	theMessage = theMessage + '{0:<3} {1:<14} {2:<46} {3:<80}'.format(" ", "Delta Time", "Device", "Notes")
	theMessage = theMessage + "\n"
	theMessage = theMessage + '{0:<3} {1:<14} {2:<46} {3:<80}'.format(" ", "__________", "______", "_____")
	theMessage = theMessage + "\n"

	count = len(delayQueue)
	index = 0
	numShown = 0

	while index < count:
		bisectTuple = delayQueue[index]
		bisectKey = bisectTuple[0]
		theParameters = bisectTuple[1]

		if (not specificDevice or specificDevice == theParameters['theDevice']) and (
				not specificProc or specificProc in theParameters['timerMessage']):
			theMessage = theMessage + str('{0:<3} {1:<14} {2:<46} {3:<80}'.format(" ", str(
				minutesAndSecondsTillTime(theParameters['executionTime'])), theParameters['theDevice'],
																				  theParameters['timerMessage']))
			theMessage = theMessage + "\n"
			numShown = numShown + 1
		index = index + 1

	theMessage = theMessage + "   Number of Entries: " + str(numShown) + "\n"
	theMessage = theMessage + "==== mmPrintDelayedProcs end ====" + "\n"
	return (theMessage)


############################################################################################
# mmPrintDelayedProcs - process timer functions registered for above
#
############################################################################################
def mmPrintDelayedProcs(theCommandParameters):
	print(mmGetDelayedProcsList(theCommandParameters))

############################################################################################
#
# minutesAndSecondsTillTime
#
#
############################################################################################
def minutesAndSecondsTillTime(futureTimeInSeconds):

	theTimeSeconds = int(futureTimeInSeconds - time.mktime(time.localtime()))
	return secondsToMinutesAndSecondsString(theTimeSeconds)

############################################################################################
#
# secondsToMinutesAndSecondsString
#
#
############################################################################################
def secondsToMinutesAndSecondsString(theTimeSeconds):

	theTimeMinutes = int(theTimeSeconds / 60)
	if theTimeMinutes:
		theTimeSeconds = int(theTimeSeconds % 60)
		theResultString = str(theTimeMinutes) + "m," + str(theTimeSeconds) + "s"
	else:
		theResultString = str(theTimeSeconds) + " seconds"

	return theResultString

def	sampleFunction0(parameters):
	return 0
def	sampleFunction1(parameters):
	return 0
def	sampleFunction2(parameters):
	return 0
def	sampleFunction3(parameters):
	return 0
def	sampleFunction4(parameters):
	return 0
def	sampleFunction5(parameters):
	return 0
def	sampleFunction6(parameters):
	return 0
def	sampleFunction7(parameters):
	return 0
def	sampleFunction8(parameters):
	return 0
def	sampleFunction9(parameters):
	return 0
def	sampleFunction100(parameters):
	return 0

functionList = [sampleFunction0,sampleFunction1,sampleFunction2,sampleFunction3,sampleFunction4,sampleFunction5,sampleFunction6,sampleFunction7,sampleFunction8,sampleFunction9]
theParameters = {}
index = 0
count = 10

while index < count:
	registerDelayedAction( {'theFunction': functionList[index], 'timeDeltaSeconds': 10 + index, 'theDevice': "device"+ str(index), 'timerMessage': "Sample with index of " + str(index)})
	index = index + 1

mmPrintDelayedProcs({})
delayDelayedAction(sampleFunction5, 100)
mmPrintDelayedProcs({})
delayDelayedAction(sampleFunction7, 100)
mmPrintDelayedProcs({})
delayDelayedAction(sampleFunction0, 100)
mmPrintDelayedProcs({})
delayDelayedAction(sampleFunction9, 100)
delayDelayedAction(sampleFunction100, 100)
mmPrintDelayedProcs({})


quit()
