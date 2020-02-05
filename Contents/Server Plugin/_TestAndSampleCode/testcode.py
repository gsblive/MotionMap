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

testDict = {'Test1':1, 'Test2':2, 'Test3':3}
bisectTuple = [0,1]
result = 0
#====================================
#============  Main  ================
#====================================

print("Length of testDict = " + str(len(testDict)))
print("Length of bisectTuple = " + str(len(bisectTuple)))
try:
	print("Length of result = " + str(len(result)))
except:
	print("Length of result = 1 (its an int)")

print("TestDict is a " + str(type(testDict)))
print("bisectTuple is a " + str(type(bisectTuple)))
print("result is a " + str(type(result)))

if str(type(result)) == "<type 'int'>":
	print "result is an int"
else:
	print "result is NOT an int"

if not isinstance(result, str): print "result is not a string according to isinstance"
if isinstance(result, int): print "result is an int according to isinstance"
if isinstance(testDict, dict): print "testDict is a dict according to isinstance"
