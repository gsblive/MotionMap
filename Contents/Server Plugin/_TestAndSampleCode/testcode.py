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



#====================================
#============  Main  ================
#====================================

startTime = timer()

resetEventMap = {'OccupiedAll':'UnoccupiedAll', 'UnoccupiedAll':'OccupiedAll', 'on':'off', 'off':'on' }
occupationEvents = ['on', 'off', 'OccupiedPartial', 'OccupiedAll', 'UnoccupiedAll']
#occupationEvents = ['on', 'off', 'OccupiedAll', 'UnoccupiedAll']
resetEvents = []
allEvents = []

allEvents = occupationEvents[:]
allEvents.append('test')

for anEntry in allEvents: print anEntry
print str(allEvents)
print str(occupationEvents)

endTime = timer()

print str(endTime - startTime)

quit()
