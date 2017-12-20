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

x=10000

startTime = time.time()

while x:
	newTime = random.randint(1,10000) + time.mktime(time.localtime())
	delayQueue.append((newTime, bottomClass))  # insert into timer deque
	delayQueue.sort()
	x=x-1

m1DeltaTime = time.time()-startTime


print("### TIMER " + str(m1DeltaTime) + "s")
print(delayQueue)
print("Method2")

x=10000

startTime = time.time()

while x:
	newTime = random.randint(1,10000) + time.mktime(time.localtime())
	#bisect.bisect(delayQ, (newTime, bottomClass))
	bisect.insort(delayQ, (newTime, bottomClass))
	x=x-1

m2DeltaTime = time.time()-startTime

print("### TIMER " + str(m2DeltaTime) + "s")
print(delayQ)


if m1DeltaTime >= m2DeltaTime:
	print("Method 2 is faster.")
else:
	print("Method 1 is faster.")

#theString = 'Hello there\n test1 \ntest2'
#theString2 = 'Jello there\n test1 \ntest2'
#resultString = _only_diff(theString, theString2)
#print(resultString)
#fullHost = socket.gethostname()
#print fullHost.split()[0]
#print fullHost.split('.', 1)[0]
#print(platform.node())
#print(os.uname()[1])
	#d = Differ()
#result = list(d.compare(text1, text2))
#print(str(_unidiff_output("one two \n three four", "one two \n five six")))