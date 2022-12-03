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

import ntpath
import re
from datetime import datetime as dt
from tkinter.filedialog import askopenfilename

import mmComm_Indigo
import mmLib_Log
import mmLib_Low

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

		#if self.debugDevice: mmLib_Log.logForceAndMail(self.deviceName + " #### TestingForceAndMail", "Test Email", "greg@gsbrewer.com" )
		#if self.debugDevice: mmLib_Log.logForceAndMail(self.deviceName + " #### TestingForceAndMail", "Test Email", "9258727124@vtext.com" )

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
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### Could not find Lock Device \'" + str(aLock) + "\'.")
					continue

				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Found Lock Device \'" + str(aLock) + "\'.")

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

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " received command event from \'" + eventParameters['publisher'] + "\'.")

		return (0)

	#
	# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
	#
	def errorCommandEvent(self, eventID, eventParameters  ):
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " received error command event from \'" + eventParameters['publisher'] + "\'.")
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

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Entering completeInit." )

		mmLib_Low.registerDelayedAction({'theFunction': self.PeriodicTime,
											 'timeDeltaSeconds': 60*60,
											 'theDevice': self.deviceName,
											 'timerMessage': "PeriodicTime"})

		return 0

	#
	# PeriodicTime - we get called every once in a while for maintenance
	#
	def PeriodicTime(self, eventID, eventParameters):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Entering PeriodicTime." )

		return 0

	#
	# selectArrivalFile - Show a dialog box to find the file we want (if its not included in the command line)
	#
	# If we cant find the files, we may be able to ask the user to find them.
	# we will have to store the file path to a variable in indigo
	#
	def selectArrivalFile(self):
		self.ArrivalSchedule = askopenfilename()
		self.NewArrivals = self.ArrivalSchedule.replace("ArrivalSchedule","NewArrivals")
		if self.debugDevice: mmLib_Log.logForce("New Arrival Schedule is: " + self.ArrivalSchedule)
		return(0)

	#
	# makeScheduleDict - We manage the schedule through two files. We make a dict from those files for easy processing.
	# This routine is called twice... once for the primary schedule, and once for the new arrival additions
	#
	def makeScheduleDict(self, theFilePath, todayISO):

		self.currentHeader = 0

		#mmLib_Log.logTerse("Parsing file: " + ntpath.basename(theFilePath))			# For just file name
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Processing file: " + ntpath.basename(theFilePath))							# For just file name)

		try:
			f = open(theFilePath, 'r')
		except Exception as e:
			mmLib_Log.logForceAndMail(self.deviceName + "Error in parseOccupancySchedule(): " + str(e) + " Terminating session.")
			return(-1)

		for line in f:
			lineList = line.strip()
			lineList = lineList.split(",")

			# Process this line. If it is the first line, its the header
			if not self.currentHeader:
				self.currentHeader = lineList
				continue
			else:
				dictEntry = dict(list(zip(self.currentHeader, lineList)))

				lPin = len(dictEntry['Code'])

				if lPin < 4:

					if lPin == 1:
						dictEntry['Code'] = "000" + dictEntry['Code']
					elif lPin == 2:
						dictEntry['Code'] = "00" + dictEntry['Code']
					elif lPin == 3:
						dictEntry['Code'] = "0" + dictEntry['Code']
					lPin = 4
				# for the purposes of this module we only allow 4 digit pins, though the hardware supports many lengths. We are forcing 4 digit below.
				# if lPin not in [4,6,8,32]:

				if lPin != 4:
					mmLib_Log.logForceAndMail(self.deviceName + "WARNING This plugin only supports 4 digit DoorCodes. Please manually change this value for entry " + dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"] + "\'.", "SandCastle Automation Message", "9258727124@vtext.com")

				arrivalTimeISO = dt.isoformat(dt.strptime(dictEntry["ArrivalDate"], "%m/%d/%y"))
				departureTimeISO = dt.isoformat(dt.strptime(dictEntry["DepartureDate"], "%m/%d/%y"))


				if arrivalTimeISO == departureTimeISO:
					mmLib_Log.logForceAndMail(self.deviceName + " WARNING: ArrivalDate and Departure Date are the same for entry " + dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"] + "\'.", "SandCastle Automation Message", "9258727124@vtext.com")
				elif arrivalTimeISO > departureTimeISO:
					mmLib_Log.logForceAndMail( self.deviceName + " WARNING: ArrivalDate is after Departure Date for entry " + dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"] + "\'.", "SandCastle Automation Message", "9258727124@vtext.com")

				if todayISO > arrivalTimeISO:
					# Tennent arrived 1 or more days ago, but may be due to leave today
					if todayISO >= departureTimeISO:
						# Departure time is today, or in the past. Mark the code for deletion,
						self.scheduleDict["Delete"] = dictEntry
						if self.debugDevice: mmLib_Log.logForce(self.deviceName + " self.deviceName + Stay is over, marking entry \'" + dictEntry['GuestName'] + " " + dictEntry['ArrivalDate'] + "\' for deletion.")
					else:
						# the tennent is still here
						if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Preserving current tennent\'s entry \'" + dictEntry['GuestName'] + " " + dictEntry['ArrivalDate'] + "\'")
						self.scheduleDict[arrivalTimeISO] = dictEntry
				else:
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Adding entry \'" + dictEntry['GuestName'] + " " + dictEntry['ArrivalDate'] + "\'")
					self.scheduleDict[arrivalTimeISO] = dictEntry
		f.close()
		return(0)

	#
	# resetArrivalFile - After we process the arrival file, we reset it to include only the header
	#
	def resetArrivalFile(self, theFilePath):
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### Resetting Arrival File")

		try:
			f = open(theFilePath, 'r+')
		except Exception as e:
			mmLib_Log.logForce(self.deviceName + " Error in resetArrivalFile(): " + str(e) + " Terminating session.")
			return(-1)

		firstLine = f.readline()
		f.seek(0,0)
		f.truncate()
		# Add Header
		f.write(firstLine)
		f.close()
		return(0)

	#
	# writeScheduleDict - After we process new schedule dict, we write it back out to a file. All the unwanted lines have
	# been removed from the dict so the file is self pruning
	#
	def writeScheduleDict(self,theFilePath):


		#mmLib_Log.logTerse("Parsing file: " + ntpath.basename(theFilePath))			# For just file name
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Writing file: " + ntpath.basename(theFilePath))							# For just file name)

		try:
			f = open(theFilePath, 'w+')
		except Exception as e:
			mmLib_Log.logForceAndMail(self.deviceName + " Error in parseOccupancySchedule(): " + str(e) + " Terminating session.")
			return(-1)

		f.truncate()
		# Add Header
		string = str(self.currentHeader)
		string = re.sub('[\'\[\]\ ]', '', string)	# take out the brackets, spaces, and single quotes
		f.write(string + "\r\n")

		for anEvent in sorted(self.scheduleDict):
			eventDict = self.scheduleDict[anEvent]
			if anEvent == "Delete":
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Deleting " + eventDict['GuestName'] + " " + eventDict['ArrivalDate'] + " from arrival schedule. Event is complete")
				continue
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Writing EventDict: " + str(eventDict))
			ArrivalDate = eventDict['ArrivalDate']
			DepartureDate = eventDict['DepartureDate']
			GuestName = eventDict['GuestName']
			DoorCode = eventDict['Code']
			string = str(ArrivalDate + ',' + DepartureDate + ',' + GuestName + ',' + DoorCode)
			f.write(string + "\r\n")

		# Add the entries

		f.close()
		return(0)

	#
	# convertListToHexStr - Utility routine
	#
	def convertListToHexStr(self, bList):
		return ' '.join(["%02X" % byte for byte in bList])

	#
	# convertListToStr - Utility routine
	#
	def convertListToStr(self, bList):
		return ' '.join(["%02X" % byte for byte in bList])

	#
	# getPinStr - Format the pin string to send via raw command to the lock
	#
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

	#
	# setUserPin - Send a user code to the lock
	#
	def setUserPin(self, indigoDevID, userNo, userPin):

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " setUserPin action called")
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Indigo lock selected: " + str(indigoDevID))

		#Hardware supports supports 4,6,8,32 digit codes, but we only support 4 digits here.

		if len(userPin) not in [4,6,8,32]:
			mmLib_Log.logForceAndMail(self.deviceName + "WARNING This plugin only supports 4 digit DoorCodes. Please manually change this value.", "SandCastle Automation Message", "9258727124@vtext.com")
			return

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Setting PIN for user " + str(userNo) + " to: " + str(userPin))

		codeStr = [99, 0o1, int(userNo), 0o1] + self.getPinStr(userPin)
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### Got CodeString. Looking for " + indigoDevID)

		#mmLib_Log.logForce(self.deviceName + " Sending raw command: [" + self.convertListToStr(codeStr) + "] to device " + str(indigoDevID))
		indigo.zwave.sendRaw(device=indigo.devices[indigoDevID], cmdBytes=codeStr, sendMode=1, waitUntilAck=False)

	#
	# clearUserPin - Erase the user pin
	#
	def clearUserPin(self, indigoDevID, userNo):
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " clearUserPin action called")
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Indigo lock selected: " + str(indigoDevID))

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Clearing PIN for user " + userNo)

		codeStr = [99, 0o1, int(userNo), 0o0]

		#mmLib_Log.logForce(self.deviceName + " Sending raw command: [" + self.convertListToStr(codeStr) + "] to device " + str(indigoDevID))
		indigo.zwave.sendRaw(device=indigo.devices[indigoDevID],cmdBytes=codeStr,sendMode=1, waitUntilAck=False)

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
	# Load arrival schedule file, turning it to a dict
	# Then add New Arrivals to the dict
	#
	# Process the dict to set or clear door codes as needed
	#
	# Note processSchedule handles all access to ArrivalSchedule.csv. Do not open this file for write access remotely.

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

		deleteDict = self.scheduleDict.get("Delete",0)
		if deleteDict != 0:
			# delete the door code for this entry
			mmLib_Log.logForceAndMail(self.deviceName + " Deleting DoorCode for guest " + deleteDict['GuestName'] + " " + deleteDict['ArrivalDate'], "SandCastle Automation Message", "9258727124@vtext.com")
			for aLock in self.doorLocks:
				self.clearUserPin(aLock, self.userNo)

		#mmLib_Log.logForce(self.deviceName + self.scheduleDict)
		# Look for new DoorCodes to change today?
		changeDict = self.scheduleDict.get(todayISO, 0)

		if changeDict == 0:
			mmLib_Log.logForce(self.deviceName + " Today is " + todayString + ". Nothing to be done.")
		else:

			mmLib_Log.logForceAndMail(self.deviceName + " Setting DoorCode for guest " + changeDict["GuestName"] + " \'" + changeDict["ArrivalDate"] + "\'.", "SandCastle Automation Message", "9258727124@vtext.com")
			mmLib_Log.logForce(self.deviceName + "  DoorCode to be reset on " + changeDict["DepartureDate"])

			# Change Lock DoorCode
			for aLock in self.doorLocks:
				self.setUserPin(aLock, self.userNo, changeDict["Code"])

		# either way, rewrite the arrival schedule file
		if not localError: localError = self.writeScheduleDict(self.ArrivalSchedule)

		# Truncate the new arrivals file... We dont need to ptocess it again.
		if not localError: localError = self.resetArrivalFile(self.NewArrivals)

		return(localError)
