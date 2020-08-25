__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

try:
	import indigo
except:
	pass

import mmLib_Log
import mmLib_Low
import mmLib_Events
import mmComm_Insteon
import mmObj_OccupationGroup
import mmComm_Indigo
from collections import deque
import os
import sys
import ntpath
from datetime import datetime as dt
from datetime import datetime as dt
from tkinter.filedialog import askopenfilename
import re

kLoadDeviceTimeSeconds = 60
kBlackOutTimeSecondsAfterOff = 10


######################################################
#
# mmZLockMgr - Z-Wave Lock Manager
#
######################################################
class mmZLockMgr(mmComm_Indigo.mmIndigo):

	def __init__(self, theDeviceParameters):
		self.ArrivalSchedule = ""
		self.NewArrivals = ""
		self.ourLockDevicesIndigo = []

		super(mmZLockMgr, self).__init__(theDeviceParameters)  # Initialize Base Class

		if self.initResult == 0:
			self.supportedCommandsDict.update({'processSchedule':self.processSchedule})

		if self.debugDevice: mmLib_Log.logForce("Initializing " + self.deviceName )
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.userNo = theDeviceParameters["userNumber"]
			self.doorLocks = theDeviceParameters["lockDeviceNames"].split(';')  # Can be a list, split by semicolons... normalize it into a proper list

			for aLock in self.doorLocks:
				try:
					theLockDevice = indigo.devices[aLock]
					self.ourLockDevicesIndigo.append(aLock)
				except:
					mmLib_Log.logForce( self.deviceName + " ### Could not find Lock Device \'" + str(aLock) + "\'.")
					continue

				mmLib_Log.logForce( self.deviceName + " Found Lock Device \'" + str(aLock) + "\'.")

		#mmLib_Log.logForce(self.deviceName + " Lock entries are: " + str(self.ourLockDevicesIndigo) )

	######################################################################################
	#
	#
	#	Plugin Entry points
	#
	#
	######################################################################################

	#
	# deviceUpdatedEvent -
	#
	#
	# deviceUpdatedEvent - tell the companions what to do
	#
	def deviceUpdatedEvent(self, eventID, eventParameters):

		return (0)

	#
	# completeCommand - we received a commandSent completion message from the server for this device.
	#
	def completeCommandEvent(self, eventID, eventParameters):
		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " received complete Command Event from \'" + eventParameters['publisher'] + "\'.")
		return (0)

	#
	# receivedCommand - we received a command from our device. The base object will do most of the work... we want to process special commands here, like bedtime mode
	#
	def receivedCommandEvent(self, eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce( self.deviceName + " received command event from \'" + eventParameters['publisher'] + "\'.")

		return (0)

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	def errorCommandEvent(self, eventID, eventParameters  ):
		if self.debugDevice: mmLib_Log.logForce( self.deviceName + " received error command event from \'" + eventParameters['publisher'] + "\'.")
		return (0)

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	# printLockInfo - turn bedtime mode on if its Nighttime
	#
	def printLockInfo(self, theCommandParameters):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Entering printLockInfo")
		return (0)

	#
	# 	devStatus - print the status of the device
	#
	def devStatus(self, theCommandParameters):

		return (0)

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################

	#
	# completeInit - Complete the initialization process for this device
	#
	def completeInit(self, eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Entering completeInit." )

		mmLib_Low.registerDelayedAction({'theFunction': self.PeriodicTime,
											 'timeDeltaSeconds': 60*60,
											 'theDevice': self.deviceName,
											 'timerMessage': "PeriodicTime"})

		return 0

	def PeriodicTime(self, eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Entering PeriodicTime." )

		return 0

	# If we cant find the files, we may be able to ask the user to find them.
	# we will have to store the file path to a variable in indigo
	def selectArrivalFile(self):
		self.ArrivalSchedule = askopenfilename()
		self.NewArrivals = self.ArrivalSchedule.replace("ArrivalSchedule","NewArrivals")
		mmLib_Log.logForce("New Arrival Schedule is: " + self.ArrivalSchedule)
		return(0)

	def makeScheduleDict(self, theFilePath, todayISO):

		self.currentHeader = 0

		#mmLib_Log.logTerse("Parsing file: " + ntpath.basename(theFilePath))			# For just file name
		mmLib_Log.logForce( self.deviceName + "Processing file: " + ntpath.basename(theFilePath))							# For just file name)

		try:
			f = open(theFilePath, 'r')
		except Exception as e:
			mmLib_Log.logForce(
			self.deviceName + "Error in parseOccupancySchedule(): " + str(e) + " Terminating session.")
			return(-1)

		for line in f:
			lineList = line.strip()
			lineList = lineList.split(",")
			#mmLib_Log.logForce( self.deviceName + lineList[0])

			# Process this line. If it is the first line, its the header
			if not self.currentHeader:
				#mmLib_Log.logForce( self.deviceName + "Found Header " + line)
				self.currentHeader = lineList
				continue
			else:
				dictEntry = dict(zip(self.currentHeader, lineList))
				#mmLib_Log.logForce( self.deviceName + dictEntry)
				key = dt.isoformat(dt.strptime(dictEntry["ArrivalDate"], "%m/%d/%y"))
				if todayISO > key:
					mmLib_Log.logForce(self.deviceName + "Abandoning expired entry " + key)
				else:
					mmLib_Log.logForce(self.deviceName + "Adding entry " + key)
					self.scheduleDict[key] = dictEntry
		f.close()
		return(0)

	def resetArrivalFile(self, theFilePath):
		mmLib_Log.logForce(self.deviceName + "### Resetting Arrival File")

		try:
			f = open(theFilePath, 'r+')
		except Exception as e:
			mmLib_Log.logForce(
			self.deviceName + "Error in resetArrivalFile(): " + str(e) + " Terminating session.")
			return(-1)

		firstLine = f.readline()
		#mmLib_Log.logForce(self.deviceName + firstLine)
		f.seek(0,0)
		f.truncate()
		# Add Header
		f.write(firstLine)
		f.close()
		return(0)

	def writeScheduleDict(self,theFilePath):


		#mmLib_Log.logTerse("Parsing file: " + ntpath.basename(theFilePath))			# For just file name
		mmLib_Log.logForce( self.deviceName + "Writing file: " + ntpath.basename(theFilePath))							# For just file name)

		try:
			f = open(theFilePath, 'w+')
		except Exception as e:
			mmLib_Log.logForce( self.deviceName + "Error in parseOccupancySchedule(): " + str(e) + " Terminating session.")
			return(-1)

		f.truncate()
		# Add Header
		string = str(self.currentHeader)
		string = re.sub('[\'\[\]\ ]', '', string)	# take out the brackets, spaces, and single quotes
		f.write(string + "\r\n")

		for anEvent in sorted(self.scheduleDict):
			eventDict = self.scheduleDict[anEvent]
			mmLib_Log.logForce(
			self.deviceName + "EventDict: " + str(eventDict))
			ArrivalDate = eventDict['ArrivalDate']
			DepartureDate = eventDict['DepartureDate']
			GuestName = eventDict['GuestName']
			DoorCode = eventDict['Code']
			string = str(ArrivalDate + ',' + DepartureDate + ',' + GuestName + ',' + DoorCode)
			#mmLib_Log.logForce( self.deviceName + "Adding Entry " + string)
			f.write(string + "\r\n")

		# Add the entries

		f.close()
		return(0)

	def convertListToHexStr(self, bList):
		return ' '.join(["%02X" % byte for byte in bList])

	def convertListToStr(self, bList):
		return ' '.join(["%02X" % byte for byte in bList])

	def getPinStr(self,inPin):
		if (len(inPin) == 4):
			d1 = int(ord(inPin[0:1]))
			d2 = int(ord(inPin[1:2]))
			d3 = int(ord(inPin[2:3]))
			d4 = int(ord(inPin[3:4]))
			return [d1,d2,d3,d4]
		elif (len(inPin) == 6):
			d1 = int(ord(inPin[0:1]))
			d2 = int(ord(inPin[1:2]))
			d3 = int(ord(inPin[2:3]))
			d4 = int(ord(inPin[3:4]))
			d5 = int(ord(inPin[4:5]))
			d6 = int(ord(inPin[5:6]))
			return [d1,d2,d3,d4,d5,d6]
		elif (len(inPin) == 8):
			d1 = int(ord(inPin[0:1]))
			d2 = int(ord(inPin[1:2]))
			d3 = int(ord(inPin[2:3]))
			d4 = int(ord(inPin[3:4]))
			d5 = int(ord(inPin[4:5]))
			d6 = int(ord(inPin[5:6]))
			d7 = int(ord(inPin[6:7]))
			d8 = int(ord(inPin[7:8]))
			return [d1,d2,d3,d4,d5,d6,d7,d8]
		elif (len(inPin) == 32):
			d1 = int(inPin[0:2],16)
			d2 = int(inPin[3:5],16)
			d3 = int(inPin[6:8],16)
			d4 = int(inPin[9:11],16)
			d5 = int(inPin[12:14],16)
			d6 = int(inPin[15:17],16)
			d7 = int(inPin[18:20],16)
			d8 = int(inPin[21:23],16)
			d9 = int(inPin[24:26],16)
			d10 = int(inPin[27:29],16)
			d11 = int(inPin[30:32],16)
			return [d1,d2,d3,d4,d5,d6,d7,d8,d9,d10,d11]
		else:
			return []

	def setUserPin(self, indigoDevID, userNo, userPin):

		mmLib_Log.logForce( self.deviceName + " setUserPin action called")
		mmLib_Log.logForce( self.deviceName + " Indigo lock selected: " + str(indigoDevID))

		if len(userPin) not in [4,6,8,32]:
			mmLib_Log.logForce( self.deviceName + "This plugin only supports 4, 6 or 8 digit PINs or 11 character RFID tags")
			return

		mmLib_Log.logForce( self.deviceName + " Setting PIN for user " + str(userNo) + " to: " + str(userPin))

		codeStr = [99, 0o1, int(userNo), 0o1] + self.getPinStr(userPin)
		mmLib_Log.logForce( self.deviceName + " ### Got CodeString. Looking for " + indigoDevID)

		indigo.zwave.sendRaw(device=indigo.devices[indigoDevID], cmdBytes=codeStr, sendMode=1, waitUntilAck = False)
		mmLib_Log.logForce(self.deviceName + "Sending raw command: [" + self.convertListToStr(codeStr) + "] to device " + str(indigoDevID))


	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	#
	#  processSchedule
	#
	# Process the CSV files and set lock codes
	#
	# Process NewArrivals and add them to the ArrivalSchedule
	# Then, process ArrivalSchedule to change DoorCodes as needed

	# Note processOccupancySchedule handles all access to ArrivalSchedule. Do not open this file for write access remotely.

	def processSchedule(self, theCommandParameters):

		self.ArrivalSchedule = theCommandParameters['ArrivalSchedule']
		self.NewArrivals = theCommandParameters['NewArrivals']
		
		self.scheduleDict = {}
		self.currentHeader = 0
		dateToday = dt.today()
		dateToday = dateToday.replace(hour=0, minute=0, second=0, microsecond=0)
		todayString = dt.strftime(dateToday, "%m/%d/%y")
		todayISO = dt.isoformat(dt.strptime(todayString, "%m/%d/%y"))

		localError = self.makeScheduleDict(self.ArrivalSchedule, todayISO)
		if not localError:
			localError = self.makeScheduleDict(self.NewArrivals, todayISO)

		#mmLib_Log.logForce( self.deviceName + self.scheduleDict)
		# Any DoorCodes to change today?
		changeDict = self.scheduleDict.get(todayISO, 0)

		if changeDict == 0:
			mmLib_Log.logForce(self.deviceName + "Today is " + todayString + ". Nothing to be done.")
		else:
			#mmLib_Log.logForce( self.deviceName + changeDict)
			mmLib_Log.logForce( self.deviceName + "Changing DoorCode for guest " + changeDict["GuestName"] + " to DoorCode " + changeDict["Code"])
			mmLib_Log.logForce( self.deviceName + "  DoorCode to be reset on " + changeDict["DepartureDate"])

			# Change Lock DoorCode
			for aLock in self.doorLocks:
				self.setUserPin(aLock, self.userNo, changeDict["Code"])

			# Schedule Lock DoorCode Reset

		# either way, rewrite the arrival schedule file
		if not localError: localError = self.writeScheduleDict(self.ArrivalSchedule)

		# Truncate the new arrivals file... We dont need to ptocess it again.
		if not localError: localError = self.resetArrivalFile(self.NewArrivals)

		return(localError)