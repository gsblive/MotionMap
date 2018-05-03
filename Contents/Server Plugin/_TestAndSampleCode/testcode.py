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

occupied = False
if occupied: print("occupied = True")
if not occupied: print("occupied == False")
quit()


startTime = timer()


endTime = timer()

proc = subprocess.Popen('ls foo', stdout=subprocess.PIPE)
#output = proc.stdout.read()
output = proc.communicate()
if output: print "### Output: \n" + output
#if err: print "### Error: \n" + err

quit()
