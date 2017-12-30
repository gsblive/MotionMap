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


# Main Code



class bottomClass(object):


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
