import time
from timeit import default_timer as timer

import DictionaryBasedQueueCode
import IndexBasedQueueCode
from collections import deque
import sys
import os.path


# Main Code



def test1():
	pass

def test2():
	pass



############################################################################################
# mmRunDelayedProcs - process timer functions subscribed above
#
############################################################################################
def	mmRunDelayedProcs(delayQueue):

	count = len(delayQueue)
	while count:
		elem = delayQueue[0]
		if (3 >= elem[0]):
			#elem[1]()
			delayQueue.pop(0)
		else:
			return	# the list is in time order, if we got here, there is no need to look at the rest of the list
		count = count - 1


def cancelDelayedActionx(delayQueue, theFunction):

	count = len(delayQueue)
	index = 0
	while count:
		elem = delayQueue[index]
		if theFunction == elem[1]:
			delayQueue.pop(index)
		else:
			index = index+1
		count = count - 1

def cancelDelayedAction(delayQueue, theFunction):

	count = len(delayQueue)
	index = 0
	while count:
		count = count - 1
		elem = delayQueue[count]
		if theFunction == elem[1]:
			delayQueue.pop(count)

def	sortedList():
	for x in range(0,10000):
		#delayQueue = deque()
		delayQueue = []
		delayQueue.append((3,'chance'))
		delayQueue = sorted(delayQueue)
		delayQueue.append((6,'kc'))
		delayQueue = sorted(delayQueue)
		delayQueue.append((5,'trixie'))
		delayQueue = sorted(delayQueue)
		delayQueue.append((1,'kc'))
		delayQueue = sorted(delayQueue)
		delayQueue.append((2,'pythor'))
		delayQueue = sorted(delayQueue)

	#print(str(newQ))

def	sortList():
	for x in range(0,10000):
		#delayQueue = deque()
		delayQueue = []
		delayQueue.append((3,'chance'))
		delayQueue.sort()
		delayQueue.append((6,'kc'))
		delayQueue.sort()
		delayQueue.append((5,'trixie'))
		delayQueue.sort()
		delayQueue.append((1,'kc'))
		delayQueue.sort()
		delayQueue.append((2,'pythor'))
		delayQueue.sort()

	#print(str(newQ))

def	insertDeq(theDeq, theItem):

	count = len(theDeq)
	rCount = 0

	if count:
		elem = theDeq[0]
	else:
		theDeq.append(theItem)	# in case the deq is empty
		return

	while elem:
		if (elem[0] < theItem[0]):
			elem = theDeq.rotate(-1)
			rCount = rCount+1
		else:
			theDeq.appendleft(theItem)
			if rCount: theDeq.rotate(rCount)
			return
	theDeq.appendleft(theItem)	# in case we got to the end
	if rCount: theDeq.rotate(rCount)

def	sortDeq():
	for x in range(0,10000):
		delayQueue = deque()
		insertDeq(delayQueue,(3,'chance'))
		insertDeq(delayQueue,(6,'kc'))
		insertDeq(delayQueue,(5,'trixie'))
		insertDeq(delayQueue,(1,'kc'))
		insertDeq(delayQueue,(2,'pythor'))

	#print(str(delayQueue))

def runTests():

	# First Test
	theStartTime = time.clock()
	sortedList()
	newTime = time.clock()
	print("SortedList Time: " + str(newTime - theStartTime))

	# Next Test
	theStartTime = time.clock()
	sortList()
	newTime = time.clock()
	print("SortList Time: " + str(newTime - theStartTime))

	# Next Test
	theStartTime = time.clock()
	sortedList()
	newTime = time.clock()
	print("SortedList Time: " + str(newTime - theStartTime))

	# next Test
	theStartTime = time.clock()
	sortDeq()
	newTime = time.clock()
	print("SortDeq Time: " + str(newTime - theStartTime))


delayQueue = []
delayQueue.append((3,'chance'))
delayQueue.sort()
delayQueue.append((6,'kc'))
delayQueue.sort()
delayQueue.append((5,'trixie'))
delayQueue.sort()
delayQueue.append((1,'kc'))
delayQueue.sort()
delayQueue.append((2,'pythor'))
delayQueue.sort()

print(str(delayQueue))
#print(delayQueue.pop(0))
cancelDelayedAction(delayQueue, "kc")
print(str(delayQueue))
cancelDelayedAction(delayQueue, "pythor")
print(str(delayQueue))
cancelDelayedAction(delayQueue, "chance")
print(str(delayQueue))
cancelDelayedAction(delayQueue, "trixie")
print(str(delayQueue))
cancelDelayedAction(delayQueue, "kc")
print(str(delayQueue))


runTests()

#mmRunDelayedProcs(delayQueue)

#print(str(delayQueue))


exit()

