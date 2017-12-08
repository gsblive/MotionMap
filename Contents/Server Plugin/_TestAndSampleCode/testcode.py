import time
from timeit import default_timer as timer

import DictionaryBasedQueueCode
import IndexBasedQueueCode
from collections import deque
import sys
import os.path
import socket
import platform


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


#theString = 'Hello there\n test1 \ntest2'
#theString2 = 'Jello there\n test1 \ntest2'
#resultString = _only_diff(theString, theString2)
#print(resultString)
fullHost = socket.gethostname()
print fullHost.split()[0]
print fullHost.split('.', 1)[0]
print(platform.node())
print(os.uname()[1])
	#d = Differ()
#result = list(d.compare(text1, text2))
#print(str(_unidiff_output("one two \n three four", "one two \n five six")))