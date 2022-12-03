
import os
import sys
import mmap
from collections import deque
from timeit import default_timer as timer

commandQueue = deque()

def qPrint(theQ):
	for elem in theQ:                   # iterate over the deque's elements
		print(elem)


def qDelete(theQ, n):
	theQ.rotate(-n)
	theQ.popleft()
	theQ.rotate(n)

############################################################################################
# qMatch - compare given entry to deque (deck) entry
############################################################################################
def qMatch(qEntry, theCommandParameters, findDirective):

	if not findDirective: return(0)					# no find directive, no match

	for directive in findDirective:
		try:
			passedDirectiveValue = theCommandParameters[directive]
			queuedDirectiveValue = qEntry[directive]
		except:
			return(0)	# if the directive isnt found in theCommandParameters, or qEntry, no match

		if queuedDirectiveValue != passedDirectiveValue:
			return(0)	# values were found, but they dont match

	return(1)	# aha it matches!

############################################################################################
# findCommandQ = does not look into first queue element, its already being processed
# even if there is no findDirectives, do the search anyway, just looking for device match
############################################################################################
def findCommandQ(theDevice, theCommandParameters, findDirective):

	n=0
	for qEntry in commandQueue:                   # iterate over the deque's elements
		# theDevice is already implied
		if n and qEntry['qDevice'] == theDevice:	# gbfixme should be theDevice.devIndex:
			if findDirective != 0 and qMatch(qEntry,theCommandParameters, findDirective):
				return(n)
		n=n+1

	return(0)                                   # we dont care about elem 0, its already being processed


############################################################################################
#
# flushCommandQ - note we only look for a single entry because we only support 1 queue entry per command type per device
#
############################################################################################
def flushCommandQ(theDevice, theCommandParameters, matchingEntries):

	n=findCommandQ(theDevice, theCommandParameters, matchingEntries)
	if n:
		qDelete(commandQueue, n)



############################################################################################
#
# enqueCommandQ
#
############################################################################################
def enqueCommandQ(theDevice, theCommandParameters, flushDirective ): # theCommandParameters is a dictionary

	startTheQueue = not commandQueue
	if flushDirective: flushCommandQ(theDevice, theCommandParameters, flushDirective)    # Get rid of the old ones if asked
	qEntry = theCommandParameters
	qEntry["qDevice"] = theDevice	# gbfixme should be theDevice.devIndex

	commandQueue.append(qEntry)

	if startTheQueue:
		pass	# gbfixme startCommandQ() # Start Command Queue Processing

