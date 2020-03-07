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

import random

#====================================
#============  Main  ================
#====================================

x = 0

class Object1():
	Value1 = 0
	Value2 = 0
	Value3 = 0

	def __init__(self, a, b, c):
		self.Value1 = a
		self.Value2 = b
		self.Value3 = c


	def	__repr__(self):
		resultString = str("Value1" + str(Object1.Value1))
		return resultString


	def __str__(self):
		resultString = ""
		myDict = vars(self)
		for keys, values in myDict.items():
			resultString = resultString + "Object1." + str(keys) + ':' + str(values) + "\n"
		return resultString

	def doSomething(self):
		print str(self.__class__.__name__)
		myDict = vars(self)
		for keys, values in myDict.items():
			print(str(keys) + ':' + str(values))

		return 0



#myObj = Object1(1,20,300)
#myObj.doSomething()

#print myObj


def doMath():
	global x
	x = x+1

def throughProc():
	doMath()

def invalidLoggindDirective():
	print("Invalid Logging Directive")

def nullProc(): pass

#print datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


#
#
# test performance in acces to variables from dict
# For the purposes of experimenting with consolidated log dispatch in MM
#



indi = {"Error.0":doMath, "Debug.0":doMath, "Log.0":doMath, "Force.0":doMath, "Warn.0":doMath,"Error.1":nullProc, "Debug.1":0, "Log.1":0, "Force.1":0, "Warn.1":0}
indi2 = {"Error.0":doMath, "Debug.0":doMath, "Log.0":doMath, "Force.0":doMath, "Warn.0":doMath,"Error.1":nullProc, "Debug.1":nullProc, "Log.1":nullProc, "Force.1":nullProc, "Warn.1":nullProc}

start = time.time()
for reps in range(1,1000000):
	doMath()
end = time.time()
print("Direct Call in seconds:" + str(end - start))



start = time.time()
for reps in range(1,1000000):
	theProc = indi["Error.1"]
	if theProc:
		theProc()
	else:
		pass
end = time.time()
print("Indirect (Null) Call in seconds:" + str(end - start))



start = time.time()
for reps in range(1, 1000000):
	indi.get("Error.1", invalidLoggindDirective)()
end = time.time()
print("Indirect Two (Null) Call in seconds:" + str(end - start))



start = time.time()
for reps in range(1,1000000):
	theProc = indi["Error.0"]
	if theProc:
		theProc()
	else:
		pass
end = time.time()
print("Indirect Call in seconds:" + str(end - start))



start = time.time()
for reps in range(1,1000000):
	try:
		indi["Debug.1"]()
	except:
		pass
end = time.time()
print("FailMode in seconds:" + str(end - start))



indi.get("Error.2", invalidLoggindDirective)()
