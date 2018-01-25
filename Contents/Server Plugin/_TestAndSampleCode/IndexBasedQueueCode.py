
import os
import sys
import mmap
from collections import deque
from timeit import default_timer as timer

commandQueue = deque()

validCommands = ['theDevice','theCommand','theValue','retry','repeat','qDeviceIndex']

kDeviceNameIndex = validCommands.index('theDevice')
kCommandNameIndex = validCommands.index('theCommand')
kValueIndex = validCommands.index('theValue')
kRetryIndex = validCommands.index('retry')
kRepeatIndex = validCommands.index('repeat')
kqDeviceIndex = validCommands.index('qDeviceIndex')



def qPrint(theQ):
	for elem in theQ:                   # iterate over the deque's elements
		print elem


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
		if qEntry[directive] != theCommandParameters[directive]: return(0)
	return(1)	# aha it matches!

############################################################################################
# findCommandQ = does not look into first queue element, its already being processed
############################################################################################
def findCommandQ(theDevice, theCommandParameters, findDirective):

	n=0
	for qEntry in commandQueue:						# iterate over the deque's elements
		# theDevice is already implied
		if n and qEntry[kqDeviceIndex] == theDevice:	# gbfixme should be theDevice.devIndex:
			if qMatch(qEntry,theCommandParameters, findDirective):
				return(n)
		n=n+1

	return(0)                                   	# we dont care about elem 0, its already being processed


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

	indexedCommands = convertCommandListToIndexList(theCommandParameters)
	indexedCommands[kqDeviceIndex] = int(theDevice)	# gbfixme should be theDevice.devIndex

	if flushDirective: flushCommandQ(theDevice, indexedCommands, convertFlushDirectiveToIndexList(flushDirective))    # Get rid of the old ones if asked

	commandQueue.append(indexedCommands)

	if startTheQueue:
		pass	# gbfixme startCommandQ() # Start Command Queue Processing


############################################################################################
#
# convertCommandListToIndexList
#
############################################################################################
def convertCommandListToIndexList(commandParameters):

	newCommandList = [0] * len(validCommands)

	for key, value in commandParameters.iteritems():
		try:
			commandIndex = validCommands.index(key)
		except:
			print " unknown command parameter given " + str(key)
			return(0)

		newCommandList[commandIndex] = value

	return(newCommandList)




############################################################################################
#
# convertFlushDirectiveToIndexList
#
############################################################################################
def convertFlushDirectiveToIndexList(flushDirective):

	newDirectiveList = []

	for key in flushDirective:
		try:
			directiveIndex = validCommands.index(key)
		except:
			print " unknown directive parameter given" + key
			return(0)

		newDirectiveList.append(directiveIndex)

	return(newDirectiveList)

