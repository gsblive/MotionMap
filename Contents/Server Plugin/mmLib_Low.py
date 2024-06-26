__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

# import json
#import os
#import traceback
#import datetime
import ntpath

try:
	import indigo
except:
	pass

import mmLib_Low
import mmLib_Log
import mmLib_Events

import _MotionMapPlugin
from collections import deque
import mmLib_CommandQ
import time
import itertools
import pickle
import collections
import bisect
import random
import os.path
import ast
import datetime

superClass = 0

############################################################################################
#
#  Insteon Support
# 	The known insteon commands (that we care about)
#
############################################################################################

MAX_SEQUENTIAL_ERRORS_DEFAULT = 2
AUTOMATIC_MODE_NOT_POSSIBLE = 'NA'	# Load Device Doesnt support Automatic Mode
AUTOMATIC_MODE_ACTIVE = 'ON'		# Load Device supports Automatic Mode and its currently active
AUTOMATIC_MODE_SLEEP = 'SLEEP'		# Load Device supports Automatic Mode and its currently de-activated till morning
AUTOMATIC_MODE_OFFLINE = 'OFF'		# Load Device supports Automatic Mode and its currently turned Off (no automatic actions will take place)

# for Battery Report
MOTION_MAX_ON_TIME = int(8*60*60)		# 8 hours in Seconds
MOTION_MAX_OFF_TIME = int(7*24*60*60)	# 7 Days in Seconds
MOTION_MAX_MISSED_COMMANDS = 2

# for HVAC processing
HVAC_SETBACK_THRESHOLD_TIME_SECONDS = 3600		# 1 hour

############################################################################################
#
# MotionMap Global Variables
#
############################################################################################

LEAD_TIME_FOR_FLASH = 60		# in seconds, the amount of time prior to automatically turning off a light that we should issue a flash-once command

# We use a dictionary to quickly look up our devices... this Dict contains both names and insteon.addresses for each mm object
MotionMapDeviceDict = {}

# a complete list of our devices that want housekeeping time
deviceTimeDeque	= deque()

# a list of our controller devices (motion Sensors)
controllerDeque	= deque()

# a list of our loadDevices (dimmers, switches, and outlets connected to load)
loadDeque	= deque()

# a list of all devices we queue for status requests
statisticsQueue = deque()

# Delay Queue related stuff
delayQueue = []
delayedFunctionKeys = {}
lastDelayProcRunTime = 0
FractionalGranularity = .000001
fractionalIndex = FractionalGranularity

TIMER_QUEUE_GRANULARITY = 2	# seconds

SubmodelDeviceDict = {}

MMSysNonvolatileData = {}	# the NVs specifically for MMSys

MMVirtualDeviceTypes = ["Scene","OccupationAction","OccupationGroup","CamMotion","ZWaveLockMgr"]
DebugDevices = {}
unknownAddress = {}

MM_Location = "UnitializedLocation" # This is a default value. Set Indigo Variable named <MMLocation>
MM_DEFAULT_CONFIG_FILE = "unitializedConfigFile" 	# this is reset in __Init__
nvFileName = str("uninitializedNVFileName")

############################################################################################
#
# MotionMap NonVolatile Data
#
############################################################################################

# All the NonVolatile data... we send this to a file on quit, and reload it on start
# each dictionary entry is set up per deviceName at the mmDevice's descretion

mmNonVolatiles = {}
mmNVFileName = ""
mmLogFolder = ""			# Gets set in plugin.py, __init__()

class anIndigoDev:

	def __init__(self, theValue, theName):
		self.onState = theValue
		self.name = theName

class anIndigoCmd:

	def __init__(self, theAddress, theBytes):
		self.address = theAddress
		self.cmdBytes = theBytes

def initializeDictEntry(theDict,theElement,theInitialValue):

	try:
		theResult = theDict[theElement]
	except:
		theDict[theElement] = theInitialValue
		theResult = theDict[theElement]

	return(theResult)


def initializeNVElement(theDeviceDict, theElement, theInitialValue):

	initializeDictEntry(theDeviceDict, theElement, theInitialValue)

	return(theDeviceDict[theElement])


def	cacheNVDict():

	global mmNonVolatiles
	global mmNVFileName

	try:
		os.mkdir(mmLogFolder)
	except Exception as err:
		if err.args[0] != 17:
			print(("Creation of the directory %s failed" % mmLogFolder))

	try:
		mmLib_Log.logForce("=== Writing MotionMap Nonvolatile File: " + ntpath.basename(mmNVFileName) )	# Only File Name
	except:
		mmLib_Log.logForce(" === Error Writing Data... Nonvolatile file not found.")


	theNVFile = open(mmNVFileName, "wb")
	pickle.dump(mmNonVolatiles, theNVFile)
	theNVFile.close()

#
# Each device has its own set of variables that can be accessed after initializeNVDict is called
# This routine does the initialization and returns the variables
#
def initializeNVDict(theDevName):

	global mmNonVolatiles
	global mmNVFileName
	global mmLogFolder

	if mmNVFileName == "":
		# get Pathname parent of plugin... We dont want to replace the NV file every time we update the pugin
		mmNVFileName = mmLogFolder + nvFileName
		#mmLib_Log.logForce("=== Loading MM NonVolatile Variables File: " + mmNVFileName)	# Full Pathname
		mmLib_Log.logForce("=== Loading MM NonVolatile Variables File: " + nvFileName)	# Just Filename

	needsCache = 0

	if mmNonVolatiles == {}:
		try:
			theNVFile = open(mmNVFileName, "rb")
			mmNonVolatiles = pickle.load(theNVFile)
			theNVFile.close()
		except:
			#mmLib_Log.logForce("==== Creating new NonVolatile File: " + mmNVFileName)		# Full pathname
			mmLib_Log.logForce("==== Creating new NonVolatile File: " + ntpath.basename(mmNVFileName))	# ony file Name
			needsCache = 1

	initializeDictEntry(mmNonVolatiles, theDevName, {})

	if needsCache:
			cacheNVDict()

	return(mmNonVolatiles[theDevName])


############################################################################################
#
# resetGlobals - Reset all the globals to default state (not including nonvolatiles above)
#
############################################################################################

def resetGlobals():
	global MotionMapDeviceDict
	global deviceTimeDeque
	global loadDeque
	global controllerDeque
	global statisticsQueue
	global MMSysNonvolatileData

	mmLib_Log.logForce("Resetting Globals")
	MotionMapDeviceDict = {}

	mmLib_Events.initializeEvents()		# this resets the event globals

	deviceTimeDeque	= deque()

	loadDeque	= deque()

	controllerDeque	= deque()

	statisticsQueue = deque()
	mmLib_Log.logForce("initializing MMSysNonvolatileData")
	MMSysNonvolatileData = initializeNVDict('MMSys')



############################################################################################

############################################################################################
############################################################################################
#
# Indigo Support routines
#
############################################################################################
############################################################################################

############################################################################################
#
# addressTranslate
#
#	if we receive a command to a device that is unregistered in MM, we dont know its name...
# This routine will translate the address to name and preserve the info for error/warning notifications
#
############################################################################################
def addressTranslate(desiredAddress):
	#mmLib_Log.logForce("####->Calling addressTranslate for " + str(desiredAddress))

	# Check to see if we have captured the name before.. this is the fast way
	lookedUp = unknownAddress.get(desiredAddress, "Unknown")
	if lookedUp != "Unknown":
		#mmLib_Log.logForce("####->In addressTranslate for " + str(desiredAddress) + " returning " + str(lookedUp))
		return (lookedUp)

	# not already in list, traverse the indigo device list add a dict entry for it

	for dev in indigo.devices.iter():
		if dev.address == desiredAddress:
			mmLib_Log.logForce("####->Adding " + dev.name + " to unknownList with address of " + str(desiredAddress))
			unknownAddress[str(desiredAddress)] = str(dev.name)
			return (str(dev.name))

	mmLib_Log.logForce("####->In addressTranslate for " + str(desiredAddress) + " returning Undefined")		# This should never happen, if it does there is a serious problem
	return ("Undefined")

############################################################################################
#
#	initIndigoVariable
#
#		Make an insteon Variable (if needed) and set its value to default. If the variable already exists, do nothing.
#
############################################################################################
def initIndigoVariable(theVarName, theDefaultValue):

	try:
		theVarValue = indigo.variables[theVarName].value
	except:
		mmLib_Log.logForce(">>> Indigo variable  \'" + theVarName + "\' does not exist... creating it and setting it to \'" + theDefaultValue + "\' .")
		theVarValue = indigo.variable.create(theVarName, theDefaultValue)

	return(theVarValue)

############################################################################################
#
#	setIndigoVariable
#
#		Set an insteon Variable. Create it if it doesnt exist.
#
############################################################################################
def setIndigoVariable(theVarName, theValue):

	try:
		indigo.variable.updateValue(theVarName, str(theValue))
		theVarValue = theValue
	except:
		theVarValue = initIndigoVariable(theVarName, theValue)

	return(theVarValue)

############################################################################################
#
#	getIndigoVariable
#
#		Get an insteon Variable. Set it to default if it doesnt exist.
#
############################################################################################
def getIndigoVariable(theVarName, theDefaultValue):

	theVarValue = initIndigoVariable(theVarName, theDefaultValue)

	return(theVarValue)


############################################################################################
#
#	readIndigoVariable
#
#		Get an insteon Variable.
#
############################################################################################
def readIndigoVariable(theVarName):

	try:
		theVarValue = indigo.variables[theVarName].value
	except:
		theVarValue = "n/a"

	return(theVarValue)



############################################################################################
#
#  daytimeTransition - Event gets executed when it becomes daytime
#
############################################################################################
def	daytimeTransition(eventID, eventParameters):

	global MMSysNonvolatileData

	if indigo.variables['MMDayTime'].value == "true":
		mmLib_Log.logReportLine( "\n*** It is now Daytime *** | Indigo Variable \'MMDayTime\' value = " + str(indigo.variables['MMDayTime'].value) + "\n")
		# only process the reports if they have not been processed in the past 23 hours (we only want them once a day)
		lastDaytimeTransition = initializeNVElement(MMSysNonvolatileData, "lastReportTime", 0)

		secondsSinceLastReport = int( time.mktime(time.localtime()) - lastDaytimeTransition)
		if  secondsSinceLastReport > 23*60*60:
			MMSysNonvolatileData["lastReportTime"] = int( time.mktime(time.localtime()))
			processOfflineReport({'theCommand': 'offlineReport', 'theDevice': 'errorCounter', 'theMode': 'Email'})
			processUnregistertedReport({'theCommand': 'unregisteredReport', 'theMode': 'Email'})
			batteryReport({'theCommand': 'batteryReport', "ReportType":"Terse"})
		else:
			mmLib_Log.logForce("Skipping Daytime reports due to recent report presentation " + str(datetime.timedelta(seconds=secondsSinceLastReport)) + " ago.")

	else:
		mmLib_Log.logReportLine("*** It is now Nighttime *** | Indigo Variable \'MMDayTime\' value = " + str(indigo.variables['MMDayTime'].value))
	return



############################################################################################
# mmRunTimer - process timer functions registered above
#
############################################################################################
def	mmRunTimer():

	global delayQueue

	if delayQueue: mmRunDelayedProcs()

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
# updateDelayedActionParameters - update the command parameters associated with the delayed
# action associated with theFunction
#
############################################################################################
def updateDelayedActionParameters(theFunction, newParameters):

	global delayQueue

	mmLib_Log.logForce("updateDelayedActionParameters NewParameters: " + str(newParameters))

	bisectKey = findDelayedAction(theFunction)	# bisectKey is the localtime in seconds when the proc is scheduled to run

	if bisectKey:
		theIndex = bisect.bisect_left(delayQueue, (bisectKey,))
		bisectTuple = delayQueue[theIndex]

		theParameters = bisectTuple[1]

		for key in newParameters:
			theParameters[key] = newParameters[key]
	else:
		mmLib_Log.logWarning("*** updateDelayedActionParameters Updated Parameters3: " + str(theFunction) + " not found ***")
	return(0)


############################################################################################
# delayDelayedAction - cancel all occurances of previously registered DelayedAction
#
############################################################################################
def delayDelayedAction(theFunction, offsetInSeconds):

	global delayQueue

	bisectKey = findDelayedAction(theFunction)	# bisectKey is the localtime in seconds when the proc is scheduled to run

	if bisectKey:
		newTime = (bisectKey - time.mktime(time.localtime())) + offsetInSeconds		# calculate new time offset

		theIndex = bisect.bisect_left(delayQueue, (bisectKey,))
		bisectTuple = delayQueue[theIndex]

		theParameters = bisectTuple[1]
		theParameters['timeDeltaSeconds'] = newTime

		cancelDelayedAction(theFunction)		# delete the old entry
		return(registerDelayedAction(theParameters))	# and add the new entry
	else:
		return(0)

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
			delayedFunctionKeys[theFunction] = 0	# Reset delayedFunctionKeys... to no function waiting
		else:
			return
	except:
		return	# no function waiting

	delayQueue.pop(bisect.bisect_left(delayQueue, (bisectKey, )))


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

	fractionalIndex = fractionalIndex+FractionalGranularity
	if fractionalIndex >= 1.0: fractionalIndex = FractionalGranularity

	theFunction = parameters['theFunction']
	whenSeconds = parameters['timeDeltaSeconds'] + time.mktime(time.localtime())
	bisectKey = whenSeconds + fractionalIndex

	cancelDelayedAction(theFunction)		# we only support one entry for this function at a time

	if time.mktime(time.localtime()) >= whenSeconds:
		# Time already expired, do it now
		theFunction(parameters)
	else:
		parameters['executionTime'] = whenSeconds
		bisect.insort(delayQueue, (bisectKey, parameters))
		delayedFunctionKeys[theFunction] = bisectKey  # We now mark this function as waiting

	if lastDelayProcRunTime:
		# Round the time up to the next timer run and return it for the convenience of the caller
		timeDelta = int((time.mktime(time.localtime()) - lastDelayProcRunTime) % TIMER_QUEUE_GRANULARITY)	# time since the last pass through timer
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
def	mmGetDelayedProcsList(theCommandParameters):

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

		if (not specificDevice or specificDevice == theParameters['theDevice']) and (not specificProc or specificProc in theParameters['timerMessage']):
			theMessage = theMessage + str('{0:<3} {1:<14} {2:<46} {3:<80}'.format(" ", str(minutesAndSecondsTillTime(theParameters['executionTime'])), theParameters['theDevice'], theParameters['timerMessage']))
			theMessage = theMessage + "\n"
			numShown = numShown + 1
		index = index+1

	theMessage = theMessage + "   Number of Entries: " + str(numShown) + "\n"
	theMessage = theMessage + "==== mmPrintDelayedProcs end ====" + "\n"
	return(theMessage)


############################################################################################
# mmPrintDelayedProcs - process timer functions registered for above
#
############################################################################################
def	mmPrintDelayedProcs(theCommandParameters):

	mmLib_Log.logReportLine(mmGetDelayedProcsList(theCommandParameters))



############################################################################################
# mmRunDelayedProcs - process timer functions registered for above
#
#	The DelayedProcs called can return either of these 2 things:
#		dict	A dict of command updates (must include 'timeDeltaSeconds' in order to requeue the delayProc
#		int		The number of seconds in the future that the proc should be executed again
#					If 0, the proc is dequeued entirely
#
############################################################################################
def	mmRunDelayedProcs():

	global delayQueue
	global lastDelayProcRunTime

	lastDelayProcRunTime = int(time.mktime(time.localtime()))

	count = len(delayQueue)
	while count:
		bisectTuple = delayQueue[0]
		bisectKey = bisectTuple[0]
		theParameters = bisectTuple[1]
		when = theParameters['executionTime']
		if (time.mktime(time.localtime()) >= when):
			DelayedFunction = theParameters['theFunction']
			delayQueue.pop(0)
			delayedFunctionKeys[DelayedFunction] = 0  # We now mark this function as waiting
			try:
				delayedFunctionResult = DelayedFunction(theParameters)
			except Exception as exception:
				mmLib_Log.logError(" DelayedProc Error: " + str(exception) + " in function: " + str(DelayedFunction))
				delayedFunctionResult = 0

			if isinstance(delayedFunctionResult, dict):
				# one or more command parameters are being change as a result of the function call
				# one of the command parameters being updated must be 'timeDeltaSeconds', or we wouldnt be able to requeue the timer function
				# so parse out the 'timeDeltaSeconds' into delayedFunctionResult to be used for the requeue below
				requeueTime = delayedFunctionResult.get('timeDeltaSeconds',0)
				if requeueTime:
					for key in delayedFunctionResult:
						theParameters[key] = delayedFunctionResult[key]

				else:
					mmLib_Log.logWarning("*** DelayedProc Warning: Delayed Function Result was Dict but did not contain a nonzero \'timeDeltaSeconds\'. " + str(DelayedFunction) + " will not be requeued.")
			else:
				requeueTime = delayedFunctionResult

			if requeueTime:
				theParameters['timeDeltaSeconds'] = requeueTime
				# if we got here, there is a reset value... queue it up again. Otherwise, its been deleted above, so ready to continue
				registerDelayedAction(theParameters)
		else:
			return	# the list is in time order, if we got here, there is no need to look at the rest of the list
		count = count - 1




############################################################################################
#
# resetOfflineStatistics
#	Reset all the saved offline Statistics to the file.
#
#	in theCommandParameters: Not used, but necessary for command dispatcher
#
#############################################################################################
def resetOfflineStatistics(theCommandParameters):

	global mmNVFileName

	mmLib_Log.logForce("Resetting onine statistics in NVFile " + mmNVFileName)
	setIndigoVariable("StatisticsResetTime", time.strftime("%m/%d/%Y %I:%M:%S"))

	for mmDev in statisticsQueue:
		mmDev.ourNonvolatileData["timeoutCounter"] = 0
		mmDev.ourNonvolatileData["errorCounter"] = 0
		mmDev.ourNonvolatileData["highestSequentialErrors"] = 0
		mmDev.ourNonvolatileData["unresponsive"] = 0
		mmDev.ourNonvolatileData["sequentialErrors"] = 0
	return(0)



############################################################################################
#
# String parsing and handling
#
############################################################################################

#
# return all the difference between two objects
#
def _unidiff_output(expected, actual):
	import difflib
	expected = expected.splitlines(1)
	actual = actual.splitlines(1)
	d = difflib.Differ()
	diff = list(d.compare(expected, actual))

	return ''.join(diff)

#
# return only the diffrerences between two objects
#
def _only_diff(expected, actual):
	resultString = '\n'
	lines = _unidiff_output(expected, actual)

	for testLine in lines.splitlines():
		print(testLine)
		if testLine.startswith('-'):
			resultString = resultString + testLine + ' -> '
		elif testLine.startswith('+'):
			resultString = resultString + testLine + '\n'

	return resultString

############################################################################################
#
# processUnregistertedReport
#	Check for error results for each device we ask status for (all load and companion devices)
#
#	in theCommandParameters:
#
#############################################################################################
def processUnregistertedReport(theCommandParameters):

	if statisticsQueue:

		try:
			sendEmail = theCommandParameters['theMode']
		except:
			sendEmail = 0

		theLine = str("==================================================")
		mmLib_Log.logReportLine(theLine)
		theEmail = theLine
		theLine = str("Running processUnregistertedReport.")
		mmLib_Log.logReportLine(theLine)
		theEmail = theEmail + '\n' +  theLine
		theLine = str("The following devices are not registered with MotionMap")
		mmLib_Log.logReportLine(theLine)
		theEmail = theEmail + '\n' +  theLine
		theLine = str("==================================================")
		mmLib_Log.logReportLine(theLine)
		theEmail = theEmail + '\n' +  theLine


		numberShown = 0

		for devName in list(unknownAddress.values()):
			numberShown = numberShown + 1
			theLine = str(devName)
			mmLib_Log.logReportLine(theLine)
			theEmail = theEmail + '\n' +  theLine

		if numberShown == 0:
			theLine = str("  ** Nothing to show ** ")
			mmLib_Log.logReportLine(theLine)
			theEmail = theEmail + '\n' +  theLine

		theLine = str("=============== End of Report ====================")
		mmLib_Log.logReportLine(theLine)
		theEmail = theEmail + '\n' +  theLine

		if sendEmail:
			if numberShown == 0:
				mmLib_Log.logReportLine("===== Not Sending Email (no data to report) ======")
			else:
				theSubject = str("MotionMap2 " + str(indigo.variables["MMLocation"].value)+ " UnregisteredReport")
				theRecipient = "greg@GSBrewer.com"
				#mmLog.logReportLine( "Sending Email. Recipient: " + theRecipient + " TheSubject: " + theSubject)
				indigo.server.sendEmailTo(theRecipient, subject=theSubject, body=theEmail)
				# we sent the email, clear the report
				resetOfflineStatistics({})



############################################################################################
#
# processOfflineReport
#	Check for error results for each device we ask status for (all load and companion devices)
#
#	in theCommandParameters:
#
#  theDevice:
# 		'all'					Print all of them (Default)
#		'errorCounter'			Print any with a nonzero errorCounter
#		'sequentialErrors'		Print any with a nonzero sequentialErrors (the count of how many errors in a row)
#		'offline'				The device who think they are offline
#
#############################################################################################
def processOfflineReport(theCommandParameters):

	if statisticsQueue:
		newList = sorted(statisticsQueue, key=lambda mmRoot: mmRoot.deviceName)

		try:
			whichDevices = theCommandParameters['theDevice']
		except:
			whichDevices = 'all'

		try:
			sendEmail = theCommandParameters['theMode']
		except:
			sendEmail = 0

		theLine = str("==================================================")
		mmLib_Log.logReportLine(theLine)
		theEmail = theLine
		theLine = str("Running processOfflineReport for " + whichDevices + ". Activity since " + indigo.variables["StatisticsResetTime"].value)
		mmLib_Log.logReportLine(theLine)
		theEmail = theEmail + '\n' +  theLine
		theLine = str("==================================================")
		mmLib_Log.logReportLine(theLine)
		theEmail = theEmail + '\n' +  theLine


		numberShown = 0

		for mmDev in newList:
			if whichDevices == 'all': showIt = 1
			elif whichDevices == 'sequentialErrors' and mmDev.ourNonvolatileData["sequentialErrors"] > 0: showIt = 1
			elif whichDevices == 'offline' and mmDev.ourNonvolatileData["unresponsive"] > 0: showIt = 1
			elif whichDevices == 'errorCounter' and int(mmDev.ourNonvolatileData["errorCounter"]) > 0: showIt = 1
			else: showIt = 0

			if showIt:
				numberShown = numberShown + 1
				theLine = str(mmDev.deviceName + ". TimeoutCount: " + str(mmDev.ourNonvolatileData["timeoutCounter"]) + ". ErrorCount: " + str(mmDev.ourNonvolatileData["errorCounter"]) + " Highest Sequential Errors: " + str(mmDev.ourNonvolatileData["highestSequentialErrors"]) + " of " + str(mmDev.maxSequentialErrors) + ". Current Sequential Errors: " + str(mmDev.ourNonvolatileData["sequentialErrors"]) + ". " )
				if mmDev.ourNonvolatileData["unresponsive"]:
					theLine = theLine + "*** Is Offline ***"
				mmLib_Log.logReportLine(theLine)
				theEmail = theEmail + '\n' +  theLine

		if numberShown == 0:
			theLine = str("  ** Nothing to show ** ")
			mmLib_Log.logReportLine(theLine)
			theEmail = theEmail + '\n' +  theLine

		theLine = str("=============== End of Report ====================")
		mmLib_Log.logReportLine(theLine)
		theEmail = theEmail + '\n' +  theLine

		if sendEmail:
			if numberShown == 0:
				mmLib_Log.logReportLine("===== Not Sending Email (no data to report) ======")
			else:
				theSubject = str("MotionMap2 " + str(indigo.variables["MMLocation"].value)+ " OfflineReport: " + whichDevices)
				theRecipient = "greg@GSBrewer.com"
				#mmLog.logReportLine( "Sending Email. Recipient: " + theRecipient + " TheSubject: " + theSubject)
				indigo.server.sendEmailTo(theRecipient, subject=theSubject, body=theEmail)
				# we sent the email, clear the report
				resetOfflineStatistics({})

############################################################################################
#
# displayAllMotionStatus
#	display motion status of a single device or all loadDevices
#	if 'theDevice' == 'all", do all devices
#
############################################################################################
def displayMotionStatus(theCommandParameters):


	# handle general case (systemwide status)

	theDeviceName = theCommandParameters.get('theDevice', 0)

	if theDeviceName:
		if indigo.variables['MMDayTime'].value == 'true':
			mmLib_Log.logReportLine("============== ** DAYTIME ** ==================")
		else:
			mmLib_Log.logReportLine("============= ** NIGHTTIME ** =================")

		if theDeviceName == 'all':
			mmLib_Log.logReportLine("Display Motion Status for all Load Devices.")
			mmLib_Log.logReportLine("===============================================")

			for mmDev in loadDeque:
				mmDev.deviceMotionStatus()

		elif theDeviceName == 'on':
			mmLib_Log.logReportLine("Display Motion Status for all ON Load Devices.")
			mmLib_Log.logReportLine("===============================================")

			for mmDev in loadDeque:
				if mmDev.theIndigoDevice.onState == True: mmDev.deviceMotionStatus()
		else:
			# device specific status
			theDevice = MotionMapDeviceDict.get(theDeviceName, "None")
			if theDevice == None:
				mmLib_Log.logError("Couldnt find device named: " + theDeviceName)
				return (0)
			mmLib_Log.logReportLine("Display Motion Status for Device " + theDeviceName)
			mmLib_Log.logReportLine("===============================================")
			theDevice.deviceMotionStatus()
	else:
		mmLib_Log.logError("No Device Name given, no operation performed.")

	return(0)

############################################################################################
#
# batteryReport
#	report the state of the controller batteries
#
############################################################################################
def batteryReport(theCommandParameters):

	liveString = ""
	deadString = ""
	emailString = ""

	resultTotal = 0

	try:
		theReportType = theCommandParameters["ReportType"]
	except:
		theReportType = "ALL"
		theCommandParameters["ReportType"] = theReportType

	emailString = "\n===============================================\n"

	if theReportType == "DEAD":
		addString = "(" + theReportType + ") Display Battery Status for Controller Devices that have low battery."
	elif theReportType == "LIVE":
		addString = "(" + theReportType + ") Display Battery Status for Controller Devices that are working properly and active."
	else:
		addString = "(" + theReportType + ") Display Battery Status for all Controller Devices."

	emailString = emailString + addString + "\n" + "===============================================\n"

	#	Call CheckBattery for each controller device:
	#	Parameter "ReportType" =
	#		'DEAD'	Report only Dead or unresponsive controller devices
	#		'LIVE'	Report all controller type devices that are responsive
	#		'ALL'	Report All Controllers. regardless of responsiveness (includes motion sensitive cameras)

	for mmDev in controllerDeque:
		addString = mmDev.checkBattery(theCommandParameters)
		#mmLib_Log.logReportLine("Test : " + addString)

		if addString != "":
			# if the result talks about a dead battery, put it in the dead list. Else the standard list
			if addString[-5:] == "dead.":
				mmLib_Log.logReportLine("Test: Adding " + addString + " to Deadlist")
				deadString = deadString + addString + "\n"
			else:
				liveString = liveString + addString + "\n"
			resultTotal = resultTotal+1

	if resultTotal == 0:
		emailString = emailString + "** Nothing to Report **\n"
	else:
		# combine string buckets
		emailString = emailString + deadString + liveString

	emailString = emailString + "=============== end of report ===================\n"

	mmLib_Log.logReportLine(emailString)

	if resultTotal != 0:
		theSubject = str("MotionMap2 " + str(indigo.variables["MMLocation"].value)+ " BatteryReport")
		theRecipient = "greg@GSBrewer.com"
		indigo.server.sendEmailTo(theRecipient, subject=theSubject, body=emailString)
	else:
		mmLib_Log.logReportLine("===== Not Sending Email (no data to report) ======")

	return(0)

############################################################################################
#
# refreshControllers
#	called at INIT time to make sure the motion sensors are in sync with reality
#
############################################################################################
def refreshControllers():


	for mmDev in controllerDeque:
		try:
			if mmDev.debugDevice: mmLib_Log.logForce("Initializing occupancy for " + mmDev.deviceName)
			mmDev.deviceTime()
			if mmDev.debugDevice: mmLib_Log.logForce("Occupancy initialized for " + mmDev.deviceName)
		except:
			mmLib_Log.logForce("Failure to initialize occupancy for " + mmDev.deviceName)

	return(0)


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


############################################################################################
#
# minutesAndSecondsTillTime
#
#
############################################################################################
def minutesAndSecondsTillTime(futureTimeInSeconds):

	theTimeSeconds = int(futureTimeInSeconds - time.mktime(time.localtime()))
	return secondsToMinutesAndSecondsString(theTimeSeconds)


######################################################
#
#
# calculateControllerOccupancyTimeout - returns how many minutes a region (a set of controllers controllers) must
#	be inactive before unoccupancy is assumed
#
#
#	theControllers		The list of controllers
#	theMode				'lowest' 	Return the lowest possible amount of time that this list may become unoccupied after an occupation event
#						'highest'	Return the highest possible amount of time that this list may become unoccupied after an occupation event
#
# 	returns an int (minutes)
#
#
######################################################
def calculateControllerOccupancyTimeout(theControllers, theMode):


	theResult = 1000000		# unrfeasonably high result if no controllers are present

	for controllerName in theControllers:
		if not controllerName: continue
		try:
			mmControllerDev = MotionMapDeviceDict[controllerName]
		except:
			mmLib_Log.logForce("Device not found. Cannot calculate Occupancy Timeout for " + str(controllerName) + ". Continuing.")
			continue

		theDeviceTimeout = mmControllerDev.getOccupancyTimeout()

		if theMode == 'lowest':
			# We are looking for the lowest timeout
			if theDeviceTimeout < theResult: theResult = theDeviceTimeout
		else:
			# We are looking for the highest timeout
			if theDeviceTimeout > theResult: theResult = theDeviceTimeout

	if theResult == 1000000: mmLib_Log.logForce("Error: No controllers found. Cannot calculate Occupancy Timeout for " + str(controllerName) + ".")
	return theResult


#
# 	makeMMSignature
#
#def makeMMSignature(anID, anAddr):
#	return 'id.' + str(anID) + '.addr.' + str(anAddr)

#
# 	makeSceneAddress
#
def makeSceneAddress(sceneNumber):
	return "scene.addr." + str(sceneNumber)


############################################################################################
############################################################################################
#
# MotionMap Device Definitions
#
############################################################################################
############################################################################################



############################################################################################
############################################################################################
#
# Initialization Routines
#
############################################################################################
############################################################################################

#
#  cacheNonVolatiles - Write out nonvolatile data to a file (periodic routine)
#
def	cacheNonVolatiles(parameters):
	cacheNVDict()
	return(int(random.randint(60*60,60*60*2)))	# run again between 1 and 2 hours

############################################################################################
#
# init()	Initialization Entry
#
############################################################################################
def init():
	random.seed()
	# this happens before parsing config file
	mmLib_Log.logForce("Initializing mmLow")
	setIndigoVariable('MMDayTime', indigo.variables['isDaylight'].value)
	setIndigoVariable('MMDefeatMotion', 'false')
	setIndigoVariable('MMListenerName', _MotionMapPlugin.MM_NAME + '.listener')
	initIndigoVariable("StatisticsResetTime", time.strftime("%m/%d/%Y %I:%M:%S"))	# in this variable's case, only init it if it doesnt exist.
	resetGlobals()
	# set a periodic process of caching the nonvolitile data
	registerDelayedAction({'theFunction': cacheNonVolatiles, 'timeDeltaSeconds': int(random.randint(60*60,60*60*2)), 'theDevice': "MotionMap System", 'timerMessage': "cacheNonVolatiles"})
