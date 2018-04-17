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



#====================================
#============  Main  ================
#====================================

startTime = timer()


endTime = timer()

line = "deviceName,unoccupationDelay,daytimeOnLevel,nighttimeOnLevel,specialFeatures,onControllers,sustainControllers,maxSequentialErrorsAllowed,debugDeviceMode"
lineList = line.strip()
lineList = lineList.split(",")
currentHeader = lineList

line = "BackStairsLights,5,60,25,flash,GarageHall3MultisensorMotion;BackStairsMultisensorMotion,,2,noDebug"

lineList = line.strip()
lineList = lineList.split(",")
initParameters = dict(zip(currentHeader, lineList))

print str(initParameters)

if not initParameters['sustainControllers']:print "no controllers"
quit()
