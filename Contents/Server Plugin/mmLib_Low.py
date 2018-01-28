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

import mmLib_Log
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

superClass = 0

############################################################################################
#
#  Insteon Support
# 	The known insteon commands (that we care about)
#
############################################################################################

MAX_SEQUENTIAL_ERRORS_DEFAULT = 2
BEDTIMEMODE_NOT_POSSIBLE = 0
BEDTIMEMODE_ON = 1
BEDTIMEMODE_OFF = 2

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
delayedFunctions = {}
lastDelayProcRunTime = 0

# Timer Queue related stuff
timerQueue = deque()
timerQueueLoopCounter = 0
TIMER_QUEUE_GRANULARITY = 5

# scene verification stuff
verifySceneQueue = deque()

DeviceDict = {}

# One shot initialization routines (executed after 1 minute). Obsolete... we now use 'initComplete' subscription below
# initCompletionQueue = deque()

mmSubscriptions = {'isDayTime':[],'isNightTime':[],'initComplete':[]}

############################################################################################
#
# MotionMap NonVolatile Data
#
############################################################################################

# All the NonVolatile data... we send this to a file on quit, and reload it on start
# each dictionary entry is set up per deviceName at the mmDevice's descretion

mmNonVolatiles = {}
mmNVFileName = ""

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
		#mmLib_Log.logForce("=== Writing MotionMap Nonvolatile File: " + mmNVFileName )		# Full pathname
		mmLib_Log.logForce("=== Writing MotionMap Nonvolatile File: " + ntpath.basename(mmNVFileName) )	# Only File Name
	except:
		mmLib_Log.logForce(" === Error Writing Data... Nonvolatile file not found.")


	theNVFile = open(mmNVFileName, "wb")
	pickle.dump(mmNonVolatiles, theNVFile)
	theNVFile.close()


def initializeNVDict(theDevName):

	global mmNonVolatiles
	global mmNVFileName

	if mmNVFileName == "":
		# get Pathname parent of plugin... We dont want to replace the NV file every time we update the pugin
		current_file = os.path.abspath(os.path.dirname(__file__))
		target_dir = os.path.join(current_file, '../../../')
		mmNVPath = os.path.abspath(target_dir)
		mmNVFileName = mmNVPath +"/"+ _MotionMapPlugin.nvFileName
		#mmLib_Log.logForce("=== Loading MM NonVolatile Variables File: " + mmNVFileName)	# Full Pathname
		mmLib_Log.logForce("=== Loading MM NonVolatile Variables File: " + _MotionMapPlugin.nvFileName)	# Just Filename

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
	global mmSubscriptions
	global deviceTimeDeque
	global verifySceneQueue
	global loadDeque
	global controllerDeque
	global statisticsQueue
	global timerQueue
	global timerQueueLoopCounter
	global initCompletionQueue

	mmLib_Log.logForce("Resetting Globals")

	MotionMapDeviceDict = {}
	mmSubscriptions = {'isDayTime':[],'isNightTime':[],'initComplete':[]}

	deviceTimeDeque	= deque()
	verifySceneQueue = deque()
	initCompletionQueue = deque()

	loadDeque	= deque()

	timerQueue = deque()
	timerQueueLoopCounter = 0

	controllerDeque	= deque()

	statisticsQueue = deque()

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
# mmRegisterForTimer - call theFunction provided every numSeconds seconds (granularity of TIMER_QUEUE_GRANULARITY seconds)
#
############################################################################################
def mmRegisterForTimer(theFunction, numSeconds):

	global timerQueue
	global timerQueueLoopCounter

	if numSeconds < TIMER_QUEUE_GRANULARITY: floorNumber = TIMER_QUEUE_GRANULARITY
	else: floorNumber = numSeconds
	modifiedNum = floorNumber - (floorNumber % TIMER_QUEUE_GRANULARITY)

	timerQueue.append((theFunction, modifiedNum))		# insert into timer deque, make sure it is divisible by TIMER_QUEUE_GRANULARITY

	return(0)

########################################
#
#	runOneShotQueue
#
#  	Periodic time to process single-shot routines
#
########################################
def runOneShotQueue(theDeque):

	while 1:
		if theDeque:
			theProc = theDeque[0]                   # iterate over the scene list
			theProc()
			theDeque.popleft()
		else:
			break

############################################################################################
#
#  mmSubscribeToEvent - Subscribe to an mm server event
#
#	theEvent can be:
#		'isDayTime' - there has been a transition to Daytime
#		'isNightTime' - there has been a transition to Nighttime
#		'initComplete' - server startup initialization is now complete
#
#	theProc has no parameters
#
############################################################################################
def	mmSubscribeToEvent(theEvent, theProc):

	global mmSubscriptions

	mmEventUnsubscribe(theEvent, theProc)
	try:
		requestedEventList = mmSubscriptions[theEvent]
	except:
		mmLib_Log.logDebug("No Such Event type \'" + str(theEvent) + "\'")
		return

	requestedEventList.append(theProc)

	return


############################################################################################
#
#  mmEventUnsubscribe - Subscribe to an mm server event
#
#	theProc is the procedure we are unsubscribing
#
############################################################################################
def	mmEventUnsubscribe(theEvent, theProc):

	global mmSubscriptions

	try:
		requestedEventList = mmSubscriptions[theEvent]
	except:
		mmLib_Log.logDebug("No Such Event type \'" + str(theEvent) + "\'")
		return

	try:
		requestedEventList.remove(theProc)
	except:
		mmLib_Log.logVerbose("Proc \'" + str(theProc) + "\' is not registered.")

	return


############################################################################################
#
#  mmRunSubscriptions - Process the specific subscription Event
#
############################################################################################
def	mmRunSubscriptions(theEvent):

	global mmSubscriptions

	try:
		requestedEventList = mmSubscriptions[theEvent]
	except:
		mmLib_Log.logDebug("No Such Event type \'" + str(theEvent) + "\'")
		return

	for aProc in requestedEventList:
		aProc()

	return

############################################################################################
#
#  mmIsDaytime - Event gets executed when it becomes daytime
#
############################################################################################
def	mmIsDaytime():

	mmLib_Log.logReportLine("*** It is now Daytime ***")
	processOfflineReport({'theCommand': 'offlineReport', 'theDevice': 'errorCounter', 'theMode': 'Email'})
	batteryReport({'theCommand': 'batteryReport', "ReportType":"Terse"})

	return

############################################################################################
#
#  mmIsNighttime - Event gets executed when it becomes nighttime
#
############################################################################################
def	mmIsNighttime():

	mmLib_Log.logReportLine("*** It is now nightime ***")

	return

############################################################################################
#
#  mmDaylightTransition - General MotionMap day/night transition stuff. Dispatch the appropriate Event to the mmDevices
#
############################################################################################
def	mmDaylightTransition(isNowDaytime):

	if isNowDaytime == 'true':
		theEvent = 'isDayTime'
	else:
		theEvent = 'isNightTime'

	mmRunSubscriptions(theEvent)

	return

############################################################################################
# mmRunTimer - process timer functions registered above
#
############################################################################################
def	mmRunTimer():

	global timerQueue
	global timerQueueLoopCounter
	global verifySceneQueue
	global delayQueue

	mmLib_Log.logDebug("MM " + str(TIMER_QUEUE_GRANULARITY) + " second Timer starting with Q " + str(timerQueue))

	if verifySceneQueue: runOneShotQueue(verifySceneQueue)

	timerQueueLoopCounter = timerQueueLoopCounter + TIMER_QUEUE_GRANULARITY	# Do your stuff here

	#if initCompletionQueue and (timerQueueLoopCounter % 60) == 0:
	#	mmLib_Log.logDebug("Running 1 minute initialization completion routines ")
	#	runOneShotQueue(initCompletionQueue)

	for elem in timerQueue:
		if (timerQueueLoopCounter % elem[1]) == 0:
			elem[0]()

	if delayQueue: mmRunDelayedProcs()


############################################################################################
# cancelDelayedAction - cancel all occurances of previously registered DelayedAction
#
############################################################################################
def cancelDelayedAction(theFunction):

	global delayQueue

	# GB Fix me... use an additional dictionary that converts theFunction to time to run... lookup time and start this loop at bisect.bisect_right()

	try:
	 	theTime = delayedFunctions[theFunction]
		if theTime :
			# There is a function waiting
			delayedFunctions[theFunction] = 0	# Reset delayedFunctions... to no function waiting
		else: return
	except: return	# no function waiting
	# now we have thetime to do the bisect_right (saves a bunch of time)

	index = bisect.bisect_left(delayQueue, theTime)

	count = len(delayQueue)
	while index < count:
		elem = delayQueue[index]
		theParameters = elem[1]
		elemFunction = theParameters['theFunction']
		if theFunction == elemFunction:
			delayQueue.pop(index)
			return
		index = index + 1


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

	theFunction = parameters['theFunction']
	whenSeconds = parameters['timeDeltaSeconds'] + time.mktime(time.localtime())

	cancelDelayedAction(theFunction)		# we only support one entry for this function at a time

	if time.mktime(time.localtime()) >= whenSeconds:
		# Time already expired, do it now
		theFunction(parameters)
	else:
		bisect.insort(delayQueue, (whenSeconds,parameters))
		delayedFunctions[theFunction] = whenSeconds		# We now mark this function as waiting

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
		elem = delayQueue[index]
		theParameters = elem[1]
		if (not specificDevice or specificDevice == theParameters['theDevice']) and (not specificProc or specificProc in theParameters['timerMessage']):
			theMessage = theMessage + str('{0:<3} {1:<14} {2:<46} {3:<80}'.format(" ", str(minutesAndSecondsTillTime(elem[0])), theParameters['theDevice'], theParameters['timerMessage']))
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
############################################################################################
def	mmRunDelayedProcs():

	global delayQueue
	global lastDelayProcRunTime

	lastDelayProcRunTime = int(time.mktime(time.localtime()))

	count = len(delayQueue)
	while count:
		elem = delayQueue[0]
		theParameters = elem[1]
		elemFunction = theParameters['theFunction']
		if (time.mktime(time.localtime()) >= elem[0]):
			delayQueue.pop(0)
			delayedFunctions[elemFunction] = 0  # We now mark this function as waiting
			resetDelta = elemFunction(theParameters)
			if resetDelta:
				theParameters['timeDeltaSeconds'] = resetDelta
				# if we got here, there is a reset value... queue it up again. Otherwise, its been deleted above, so ready to continue
				registerDelayedAction(theParameters)
		else:
			return	# the list is in time order, if we got here, there is no need to look at the rest of the list
		count = count - 1



############################################################################################
#
# getStatFileName
#	Return the name of the Statistics file.
#
#
#############################################################################################
def getStatFileName():

	theStatFileName = str("mmStat." + indigo.variables["MMLocation"].value) + ".p"

	return theStatFileName

############################################################################################
#
# resetOfflineStatistics
#	Reset all the saved offline Statistics to the file.
#
#	in theCommandParameters: Not used, but necessary for command dispatcher
#
#############################################################################################
def resetOfflineStatistics(theCommandParameters):

	devDict = {}

	theStatFileName = getStatFileName()
	mmLib_Log.logForce("Resetting onine statistics file " + theStatFileName)
	setIndigoVariable("StatisticsResetTime", time.strftime("%m/%d/%Y %I:%M:%S"))

	for mmDev in statisticsQueue:
		mmDev.timeoutCounter = 0
		mmDev.errorCounter = 0
		mmDev.highestSequentialErrors = 0
		mmDev.unresponsive = 0
		mmDev.sequentialErrors = 0

	return(0)

############################################################################################
#
# saveOfflineStatistics
#	Save all the offline Statistics to a file. Operates for every device in StatusQueue that have had errors
#
#
#############################################################################################
def saveOfflineStatistics():

	devDict = {}
	for mmDev in statisticsQueue:
		entryName = mmDev.deviceName
		if mmDev.timeoutCounter or mmDev.errorCounter:
			entryStatistics = {"timeoutCounter": mmDev.timeoutCounter, "errorCounter": mmDev.errorCounter, "highestSequentialErrors":mmDev.highestSequentialErrors}
			devDict[entryName] = entryStatistics

	theStatFileName = getStatFileName()
	pickle.dump( devDict, open( theStatFileName, "wb" ) )

	return(0)

############################################################################################
#
# restoreOfflineStatistics
#	Restore all the offline Statistics from a file. Operates for every device in StatusQueue that have had errors
#
#
#############################################################################################
def restoreOfflineStatistics():

	devDict = {}

	theStatFileName = getStatFileName()
	try:
		devDict = pickle.load(open(theStatFileName, "rb"))
	except:
		pass
	
	if devDict:

		mmLib_Log.logForce("Loading Statistics file: " + theStatFileName)
		mmLib_Log.logVerbose("  Contents: " + str(devDict))


		for mmDev in statisticsQueue:
			entryName = mmDev.deviceName

			try:
				entryStatistics = devDict[entryName]
			except:
				continue

			try:mmDev.timeoutCounter = entryStatistics["timeoutCounter"]
			except: pass

			try:mmDev.errorCounter = entryStatistics["errorCounter"]
			except: pass

			try:mmDev.highestSequentialErrors = entryStatistics["highestSequentialErrors"]
			except: pass

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
			elif whichDevices == 'sequentialErrors' and mmDev.sequentialErrors > 0: showIt = 1
			elif whichDevices == 'offline' and mmDev.unresponsive > 0: showIt = 1
			elif whichDevices == 'errorCounter' and int(mmDev.errorCounter) > 0: showIt = 1
			else: showIt = 0

			if showIt:
				numberShown = numberShown + 1
				theLine = str(mmDev.deviceName + ". TimeoutCount: " + str(mmDev.timeoutCounter) + ". ErrorCount: " + str(mmDev.errorCounter) + " Highest Sequential Errors: " + str(mmDev.highestSequentialErrors) + " of " + str(mmDev.maxSequentialErrors) + ". Current Sequential Errors: " + str(mmDev.sequentialErrors) + ". " )
				if mmDev.unresponsive:
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


############################################################################################
#
# displayAllMotionStatus
#	display motion status of a single device or all loadDevices
#	if 'theDevice' == 'all", do all devices
#
############################################################################################
def displayMotionStatus(theCommandParameters):

	whichDevice = theCommandParameters['theDevice']

	if indigo.variables['MMDayTime'].value == 'true':
		mmLib_Log.logReportLine("============== ** DAYTIME ** ==================")
	else:
		mmLib_Log.logReportLine("============= ** NIGHTTIME ** =================")

	if whichDevice == 'all':
		mmLib_Log.logReportLine("Display Motion Status for all Load Devices.")
		mmLib_Log.logReportLine("===============================================")

		for mmDev in loadDeque:
			mmDev.deviceMotionStatus

	elif whichDevice == 'on':
		mmLib_Log.logReportLine("Display Motion Status for all ON Load Devices.")
		mmLib_Log.logReportLine("===============================================")

		for mmDev in loadDeque:
			if mmDev.theIndigoDevice.onState == True: mmDev.deviceMotionStatus
	else:
		mmLib_Log.logReportLine("Display Motion Status for Device " + whichDevice)
		mmLib_Log.logReportLine("===============================================")
		mmDev = MotionMapDeviceDict[whichDevice]
		mmDev.deviceMotionStatus

	return(0)

############################################################################################
#
# batteryReport
#	report the state of the controller batteries
#
############################################################################################
def batteryReport(theCommandParameters):

	emailString = ""
	resultTotal = 0

	try:
		theReportType = theCommandParameters["ReportType"]
	except:
		theReportType = "Terse"

	addString = "==============================================="
	mmLib_Log.logReportLine(addString)
	emailString = emailString + addString + "\n"

	if theReportType == "Terse":
		addString = "Display Battery Status for Controller Devices that have low battery."
	else:
		addString = "Display Battery Status for all Controller Devices."

	mmLib_Log.logReportLine(addString)
	emailString = emailString + addString + "\n"

	addString = "==============================================="
	mmLib_Log.logReportLine(addString)
	emailString = emailString + addString + "\n"


	for mmDev in controllerDeque:
		addString = mmDev.checkBattery(theCommandParameters)
		if addString != "":
			emailString = emailString + addString + "\n"
			resultTotal = resultTotal+1

	if resultTotal == 0:
		addString = "** Nothing to Report **"
		mmLib_Log.logReportLine(addString)
		emailString = emailString + addString + "\n"

	addString = "=============== end of report ==================="
	mmLib_Log.logReportLine(addString)
	emailString = emailString + addString + "\n"

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

	mmLib_Log.logForce("Resetting mmInsteons to current system status.")

	for mmDev in controllerDeque:
		mmLib_Log.logDebug("Initializing occupancy for " + mmDev.deviceName)
		mmDev.deviceTime()

	return(0)


######################################################
#
# subscribeToControllerEvents - Tell one or more controllers to stat sending us events
#
#	theControllers		The list of controllers to subscribe to (motion sensors for example)
#	theEvents			The List of events we want
# 	theHandler			The Handler to call when the event happens
#	subscriberName		The Name of the device Subscribing
#
######################################################
def subscribeToControllerEvents(theControllers, theEvents, theHandler, subscriberName):

	for controllerName in theControllers:
		if not controllerName: continue
		try:
			mmControllerDev = MotionMapDeviceDict[controllerName]
		except:
			mmLib_Log.logForce("Device not found. Cannot add events " + str(theEvents) + " to event Deque of " + controllerName)
			continue

		mmControllerDev.addToControllerEventDeque(theEvents, theHandler, subscriberName)		# subscribe to events


############################################################################################
#
# minutesAndSecondsTillTime
#	called at INIT time to make sure the motion sensors are in sync with reality
#
############################################################################################
def minutesAndSecondsTillTime(futureTimeInSeconds):

	theTimeSeconds = int(futureTimeInSeconds - time.mktime(time.localtime()))
	theTimeMinutes = int(theTimeSeconds / 60)
	if theTimeMinutes:
		theTimeSeconds = int(theTimeSeconds % 60)
		theResultString = str(theTimeMinutes) + "m," + str(theTimeSeconds) + "s"
	else:
		theResultString = str(theTimeSeconds) + " seconds"

	return theResultString


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
def makeMMSignature(anID, anAddr):
	return 'id.' + str(anID) + '.addr.' + str(anAddr)

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
#  cacheNonVolatiles - Write out nonvolatile data to a file
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
	# now subscribe to time events
	registerDelayedAction({'theFunction': cacheNonVolatiles, 'timeDeltaSeconds': int(random.randint(60*60,60*60*2)), 'theDevice': "MotionMap System", 'timerMessage': "cacheNonVolatiles"})
