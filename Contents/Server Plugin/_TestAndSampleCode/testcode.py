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

# Main Code

theDict = {}
delayQueue = []
delayedFunctions = {}

class anotherClass:

	def __init__(self, theValue):
		print(str('in anotherClass: '+ str(theValue)))
		self.insideVal = theValue





class bottomClass:


	def __init__(self, theDeviceParameters):
		print(str('in bottom class: '+ str(theDeviceParameters)))

try:
	if superClass: pass
except:
	superClass = bottomClass

class middleClass(superClass):


	def __init__(self, theDeviceParameters):
		super(middleClass, self).__init__(theDeviceParameters)
		print(str('in middle class: '+ str(theDeviceParameters)))


def _unidiff_output(expected, actual):
	import difflib
	expected = expected.splitlines(1)
	actual = actual.splitlines(1)
	d = difflib.Differ()
	diff = list(d.compare(expected, actual))

	return ''.join(diff)


def _only_diff(expected, actual):
	resultString = ''
	lines = _unidiff_output(expected, actual)

	for testLine in lines.splitlines():
		if testLine.startswith(('+', '-')):
			resultString = resultString + testLine + '\n'
	return resultString


def timeTest():
	#print("### TIMER " + str(round(690 / 60.0, 2)) + " minutes.")


	delayQueue = []
	delayQ = []
	delayTime = 0

	random.seed()

	print("Method1")


	for x in range(10000 , 20000):
		delayQueue.append((x, bottomClass))  # insert into timer deque

	print(delayQueue)

	# Now access the list 10000 times, measuring time
	startTime = time.time()

	#print("### TIMER " + str(m1DeltaTime) + "s")

	for x in range(0 , 10000):
		newTime = random.randint(1,9999) + 10000
		testVal = bisect.bisect_left(delayQueue, newTime)


	m1DeltaTime = time.time()-startTime
	print("### TIMER " + str(m1DeltaTime) + "s")


	#===============

	print("Method2")

	deviceDict = {}


	for x in range(10000 , 20000):
		deviceDict[str(x)] = bottomClass

	print(deviceDict)

	# Now access the list 10000 times, measuring time
	startTime = time.time()

	#print("### TIMER " + str(m1DeltaTime) + "s")

	for x in range(1 , 10000):
		newTime = random.randint(1,9999) + 10000
		testVal = deviceDict[str(newTime)]


	m1DeltaTime = time.time()-startTime
	print("### TIMER2 " + str(m1DeltaTime) + "s")

	#===============

	print("Method3")

	# Now access the list 10000 times, measuring time
	startTime = time.time()

	while delayQueue:
		elem = delayQueue[0]
		delayQueue.pop(0)
	m1DeltaTime = time.time()-startTime
	print("### TIMER3 " + str(m1DeltaTime) + "s")

	return

def	addToParameter5():

	global theDict

	myDict = theDict['EntryTwo']
	parameterFiveDict = myDict['Parameter5']
	parameterFiveDict['gregsName'] = "Brewer"

def twoDimensionalDictTest():

	global 	theDict

	theDict = {}

	theDict['EntryTwo'] = {'Parameter1': 10, 'Parameter2':20}

	myDict = theDict['EntryTwo']
	myDict['Parameter4'] = []
	myDict['Parameter5'] = {}
	myList = myDict['Parameter4']

	for x in range(1, 10):
		myList.append(x + 1000)

	print(theDict)
	addToParameter5()

	pickle.dump(theDict, open("tempTestFile.p", "wb"))

	return

mmNonVolitiles = {"Test1":1, "Test2":2}
nvFileName = "mmNonVolatiles"

def initializeDictEntry(theDict,theElement,theInitialValue):

	try: theResult = theDict[theElement]
	except:
		print( "Initializing '" + theElement)
		theResult = theDict[theElement] = theInitialValue

	return(theResult)



def initializeNVElement(theDeviceDict, theElement, theInitialValue):

	initializeDictEntry(theDeviceDict, theElement, theInitialValue)

	return(theDeviceDict[theElement])


def	cacheNVDict():

	global mmNonVolitiles

	theNVFile = open(nvFileName, "wb")
	pickle.dump(mmNonVolitiles, theNVFile)
	theNVFile.close()

def initializeNVDict(theDevName):

	global mmNonVolitiles

	needsCache = 0

	if mmNonVolitiles == {}:
		try:
			theNVFile = open(nvFileName, "rb")
			mmNonVolitiles = pickle.load(theNVFile)
			theNVFile.close()
		except:
			print("Creating new NV File: " + nvFileName)
			needsCache = 1

	initializeDictEntry(mmNonVolitiles, theDevName, {})

	if needsCache: cacheNVDict()

	return(mmNonVolitiles[theDevName])

def supermakedirs(path, mode):
    if not path or os.path.exists(path):
        return []
    (head, tail) = os.path.split(path)
    res = supermakedirs(head, mode)
    os.mkdir(path)
    os.chmod(path, mode)
    res += [path]
    return res



def	makeDictVersion1():

	for i in range(100000):
		theHeader = ["deviceName", "maxNonMotionTime", "maxOnTime", "daytimeOnLevel", "nighttimeOnLevel",
					 "specialFeatures", "onControllers", "sustainControllers", "maxSequentialErrorsAllowed",
					 "debugDeviceMode"]
		theDevice = ["BackStairsLights", 5, 30, 60, 25, "flash", "GarageHall3Multisensor;BackStairsMultisensor", "", 2,
					 "noDebug"]
		dictionary = dict(zip(theHeader, theDevice))

	print(dictionary)

def	makeDictVersion2():

	for i in range(100000):
		theHeader = ["deviceName", "maxNonMotionTime", "maxOnTime", "daytimeOnLevel", "nighttimeOnLevel",
					 "specialFeatures", "onControllers", "sustainControllers", "maxSequentialErrorsAllowed",
					 "debugDeviceMode"]
		theDevice = ["BackStairsLights", 5, 30, 60, 25, "flash", "GarageHall3Multisensor;BackStairsMultisensor", "", 2,
					 "noDebug"]
		#dictionary = dict(zip(theHeader, theDevice))

		#min(timeit.repeat(lambda: {k: v for k, v in zip(theHeader, theDevice)}))
		dictionary = {k: v for k, v in zip(theHeader, theDevice)}

	print(dictionary)

def makeDictVersion3():

	for i in range(100000):
		theHeader = ["deviceName", "maxNonMotionTime", "maxOnTime", "daytimeOnLevel", "nighttimeOnLevel",
					 "specialFeatures", "onControllers", "sustainControllers", "maxSequentialErrorsAllowed",
					 "debugDeviceMode"]
		theDevice = ["BackStairsLights", 5, 30, 60, 25, "flash", "GarageHall3Multisensor;BackStairsMultisensor", "", 2,
					 "noDebug"]

		dictionary = {}
		for theKey in theHeader:
			dictionary[theKey] = theDevice.pop(0)

	print(dictionary)


def makeDeviceSubmodelDictionary():

	DeviceDict = {}

	for newDevAddr in range(100):

		for subModel in ["Sub1","Sub2", "Sub3","Sub4"]:
			try:
				temp = DeviceDict[newDevAddr]
			except:
				DeviceDict[newDevAddr] = {}

			DeviceDict[newDevAddr][subModel] = "This is our Device"

	#print DeviceDict
	newDevAddr = 49
	submodel = "Sub2"
	for x in range(10000):
		tempData = DeviceDict[newDevAddr][subModel]
	return


def makeDeviceSubmodelDictionary2():

	deviceQueue = []
	deviceInfo = []

	for newDevAddr in range(100):

		for subModel in ["Sub1","Sub3", "Sub9","Sub4"]:
			bisect.insort(deviceQueue, (newDevAddr,subModel,"This is our device"))
			#deviceInfo[newDevAddr*10 + subModel] = "This is our device"
			#print "Insort " + str(newDevAddr) + subModel

	#print deviceQueue
	return

def makeDeviceSubmodelDictionary3():

	DeviceDict = {}

	for newDevAddr in range(100):

		for subModel in ["Sub1","Sub2", "Sub3","Sub4"]:
			try:
				temp = DeviceDict[newDevAddr]
			except:
				DeviceDict[newDevAddr] = {}

			DeviceDict[str(newDevAddr) + subModel] = "This is our Device"

	newDevAddr = str(49)
	submodel = "Sub2"
	findThis = str(newDevAddr) + subModel
	for x in range(10000):
		tempData = DeviceDict[findThis]

	#print DeviceDict[str(newDevAddr) + subModel]

	return

indentList =   ['',
				' ',
				'  ',
				'   ',
				'    ',
				'     ',
				'      ',
				'       ',
				'        ',
				'         ',
				'          ',
				'           ',
				'            ',
				'             ',
				'              ',
				'               ',
				'                ',
				'                 ',
				'                  ',
				'                   ',
				'                    ',
				'                    +']

def displayMessage(logType, logMessage, diplayProc):

	global indentList

	finalString = ""

	theTrace = traceback.extract_stack()
	NestingDepth = len(theTrace) - 3
	aLine = theTrace[NestingDepth]

	if NestingDepth < 0: NestingDepth = 0
	elif NestingDepth > 20: NestingDepth = 21

	indent = indentList[NestingDepth]
	callingFile = os.path.basename(str(aLine[0]))
	callingProc = str(aLine[2])
	callingLine = str(aLine[1])
	callingTime = datetime.datetime.now().strftime("%I:%M:%S %p")
	callingPackage = str("(" + callingFile + "." + callingProc + ":" + callingLine + ")" )

	NestingDepth = random.randint(1, 20)

	finalString = '{0:<22} {1}'.format(str('|' * NestingDepth), str(callingTime + " " + ': ' + logMessage + " " + callingPackage))

	return finalString


random.seed()

configFileName = "/Library/Application Support/Perceptive Automation/Indigo 7/Plugins/MotionMap 3.indigoPlugin/Contents/Server Plugin/_Configurations/mmConfig.SkyCastle.csv"
logMessage = "Parsing file: " + ntpath.basename(configFileName)


theMessage = displayMessage('mMForce', logMessage, 1)
print '{0:<34} {1}'.format("MotionMap3" + " " + 'mmForce', theMessage)

theMessage = displayMessage('mMForce', logMessage, 0)
print '{0:<34} {1}'.format('MotionMap3 Error', theMessage)


if 0:
	theStartTime = time.clock()
	makeDeviceSubmodelDictionary()
	newTime = time.clock()
	print("makeDeviceSubmodelDictionary Time: " + str(newTime - theStartTime))

	theStartTime = time.clock()
	makeDeviceSubmodelDictionary3()
	newTime = time.clock()
	print("makeDeviceSubmodelDictionary3 Time: " + str(newTime - theStartTime))

	theStartTime = time.clock()
	makeDeviceSubmodelDictionary3()
	newTime = time.clock()
	print("makeDeviceSubmodelDictionary3 Time: " + str(newTime - theStartTime))

	theStartTime = time.clock()
	makeDeviceSubmodelDictionary()
	newTime = time.clock()
	print("makeDeviceSubmodelDictionary Time: " + str(newTime - theStartTime))






	theStartTime = time.clock()
	makeDictVersion1()
	newTime = time.clock()
	print("makeDictVersion1 Time: " + str(newTime - theStartTime))


	theStartTime = time.clock()
	makeDictVersion2()
	newTime = time.clock()
	print("makeDictVersion2 Time: " + str(newTime - theStartTime))

	theStartTime = time.clock()
	makeDictVersion3()
	newTime = time.clock()
	print("makeDictVersion3 Time: " + str(newTime - theStartTime))



	#s = {1,2,4,5,6}
	#theDevice = {"BackStairsLights",5,30,60,25,"flash","GarageHall3Multisensor;BackStairsMultisensor","",2,"noDebug"}
	#theDevice = ["a","b","c","d","e"]
	#print dict.fromkeys(s, theDevice)
	#print dict.fromkeys(theHeader, theDevice)







	myTemplate = "\'Identifyer\':@0,\'Data\':@1"
	myValues = ['TestID','{\'field1\':001,\'field2\':002}']
	aString = myTemplate

	for index in range(0,len(myValues)):
		indexString = '@' + str(index)
		aString = aString.replace(indexString, myValues[index])

	print(aString)





	text = '000 001 002 003'
	words = ['now','is', 'the', 'time']

	print [words[int(item)] for item in text.split()]

	str = "What $noun$ is $verb$?"
	print str.replace("$noun$", "the heck")

	myStr = "Identifyer:@0,Data:@1"
	print myStr.replace("@0", "MyTest")

	myTemplate = "Identifyer:@0,Data:@1"
	myValues = ['TestID','TestVal']
	anIndex = 0
	for elem in enumerate(myValues):
		#theIndex = '@'+ str(index)
		print('@' + str(anIndex))
	#	print(myTemplate.replace('@0', elem))
		#myTemplate.replace("@"+str(index), str(elem))
		anIndex = anIndex + 1
	#print(myTemplate)


	fileDir = os.path.dirname(os.path.realpath('__file__'))
	print fileDir

	print os.path.basename(__file__)                      # script1.py
	print os.path.basename(os.path.realpath(sys.argv[0])) # script1.py
	print os.path.abspath(__file__)                       # C:\testpath\script1.py
	print os.path.realpath(__file__)                      # C:\testpath\script1.py
	print os.getcwd()
	current_file = os.path.abspath(os.path.dirname(__file__))
	parent_of_parent_dir = os.path.join(current_file, '../../../../')
	print os.path.abspath(parent_of_parent_dir)                       # C:\testpath\script1.py

	#supermakedirs("/Library/Application Support/MotionMap/", 0755)

	#os.makedirs("/Library/Application Support/MotionMap/", 0755)
	# os.makedirs('full/path/to/new/directory', desired_permission)
	#originalMask = os.umask(0)
	#os.makedirs("/Library/Application Support/MotionMap/", 0755)
	#os.umask(originalMask)

	#theNVFile = open("/Library/Application Support/MotionMap/" + nvFileName, "wb")
	#pickle.dump(mmNonVolitiles, theNVFile)
	#theNVFile.close()


	ourmmNonVolitiles = initializeNVDict("GregsDevice")
	storedValue = initializeNVElement(ourmmNonVolitiles, "FirstEntry",100)

	print(str(storedValue))

	ourmmNonVolitiles = mmNonVolitiles["GregsDevice"]
	ourmmNonVolitiles["FirstEntry"] = ourmmNonVolitiles["FirstEntry"] + 325

	print(str(ourmmNonVolitiles["FirstEntry"]))

	cacheNVDict()

	cThis = anotherClass(101234)
	print(cThis.insideVal)


	# Save Motion, Temp, and Offline Statistics to a multi-dimensional Dict, then load and Save with Pickle.
	# Example: mmNonVolitiles{'TheDeviceName':{'DeviceSpecificErrorCount':1,'DeviceSpecificOfflineCount':2}, 'TheDeviceName2':{AListOfAccessTimes:[],'AccessTimesDeltaList':[]}}
	# Each device will be responsible for adding its parameters into the list... mmLib_Low will save/restore the list in resetOfflineStatistics/saveOfflineStatistics/restoreOfflineStatistics.
	#  Note Each device can keep pointer to of its parameter dictionary
	# in its init routine: myNonVolitileParametersDict = mmNonVolitiles['MyDevName'], then later use self.myNonVolitileParametersDict['parameterName'] = whatever

	twoDimensionalDictTest()
	aDict = pickle.load(open("tempTestFile.p", "rb"))

	myDict = aDict['EntryTwo']
	myList = myDict['Parameter4']

	for x in range(1, 10):
		myList.append(x + 2200)

	print(aDict)
