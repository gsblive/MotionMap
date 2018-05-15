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


tenthValues = [1,3,20,65,190,230,280,320,380,470,900,1500,2100,2700,3600,4800]

#
#	Support for SetBrightnessWithRamp (0x2E)
#
#	makeCmdModifier(level,RampRateSeconds)
# 		where
# 			Level = 0-100%
# 		and
# 			RampRateSeconds = .1-480 seconds

# cmd modifier = Bits 4-7 = OnLevel + 0x0F and Bits 0-3 = 2 x RampRate + 1
#		where
# 			onLevel is 16 levels of brightness (0-15) : 0 = off and 15 = 100%
# 		and
# 			RampRate = 0-15 log indexed into [1,3,20,65,190,230,280,320,380,470,900,1500,2100,2700,3600,4800] seconds,
# 			then inverted by subtracting it by 15:
#
def makeCmdModifier(level,RampRateSeconds):

	if RampRateSeconds < 0.1: RampRateSeconds = 0.1
	elif RampRateSeconds > 480: RampRateSeconds = 480

	onLevel = int(level / 6.5) * 0x10

	iPoint = bisect.bisect_left(tenthValues, int(RampRateSeconds * 10))
	#print str(tenthValues[iPoint]/10.0) + " is closest to requested " + str(RampRateSeconds) + " seconds"

	finalCmd = onLevel + (15-iPoint)
	return finalCmd

print str(0x2e)
quit()

level = 50
RampRateSeconds = 0.1

print hex(makeCmdModifier(level,RampRateSeconds))

quit()

startTime = timer()
theRampRate = 1
theValue = 90
onlevel = ((((theValue/6) + 0x0F) << 4) & 0xF0) + (theRampRate * 2 + 1)
print hex(onlevel)



quit()

secondParm = int((theRampRate*0x10))+int((theValue/6))

print hex(100/6)
print hex(secondParm)

endTime = timer()

quit()
