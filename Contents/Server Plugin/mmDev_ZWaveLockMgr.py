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
from datetime import datetime, timedelta
from tkinter.filedialog import askopenfilename

import mmComm_Indigo
import mmLib_Log
import mmLib_Low
import shutil

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

		# if self.debugDevice: mmLib_Log.logForceAndMail(self.deviceName + " #### TestingForceAndMail", "Test Email", "greg@gsbrewer.com" )
		# if self.debugDevice: mmLib_Log.logForceAndMail(self.deviceName + " #### TestingForceAndMail", "Test Email", "9258727124@vtext.com" )

		if self.initResult == 0:
			self.supportedCommandsDict.update({'processSchedule': self.processSchedule})

		if self.debugDevice: mmLib_Log.logForce("Initializing " + self.deviceName)
		if self.initResult == 0:
			#
			# Set object variables
			#
			self.userNo = theDeviceParameters["userNumber"]
			self.doorLocks = theDeviceParameters["lockDeviceNames"].split(
				';')  # Can be a list, split by semicolons... normalize it into a proper list

			for aLock in self.doorLocks:
				try:
					theLockDevice = indigo.devices[aLock]
					self.ourLockDevicesIndigo.append(aLock)
				except:
					if self.debugDevice: mmLib_Log.logForce(
						self.deviceName + " ### Could not find Lock Device \'" + str(aLock) + "\'.")
					continue
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Found Lock Device \'" + str(aLock) + "\'.")

		return

	def deviceUpdatedEvent(self, eventID, eventParameters):
		#
		# deviceUpdatedEvent - we received a commandSent completion message from the server for this device.
		#
		return 0

	def completeCommandEvent(self, eventID, eventParameters):
		#
		# completeCommand - we received a commandSent completion message from the server for this device.
		#
		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " complete command event from \'" + eventParameters['publisher'] + "\'.")

		return (0)

	def receivedCommandEvent(self, eventID, eventParameters):
		#
		# receivedCommand - we received a command from our device. The base object will do most of the work... we want to process special commands here, like bedtime mode
		#

		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " received command event from \'" + eventParameters['publisher'] + "\'.")

		return (0)

	def errorCommandEvent(self, eventID, eventParameters):
		#
		# errorCommand - we received a commandSent completion message from the server for this device, but it is flagged with an error.
		#
		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " received error command event from \'" + eventParameters['publisher'] + "\'.")

		return (0)

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	def printLockInfo(self, theCommandParameters):
		#
		# printLockInfo - turn bedtime mode on if its Nighttime
		#

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Entering printLockInfo")
		return (0)

	def devStatus(self, theCommandParameters):
		#
		# 	devStatus - print the status of the device
		#
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Entering devStatus")

		return (0)

	def completeInit(self, eventID, eventParameters):
		#
		# completeInit - Complete the initialization process for this device
		#

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Entering completeInit.")

		mmLib_Low.registerDelayedAction({'theFunction': self.PeriodicTime,
										 'timeDeltaSeconds': 60 * 60,
										 'theDevice': self.deviceName,
										 'timerMessage': "PeriodicTime"})

		return 0

	def PeriodicTime(self, eventID, eventParameters):
		#
		# PeriodicTime - we get called every once in a while for maintenance
		#

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Entering PeriodicTime.")

		return 0

	def selectArrivalFile(self):
		#
		# selectArrivalFile - Show a dialog box to find the file we want (if its not included in the command line)
		#
		# If we cant find the files, we may be able to ask the user to find them.
		# we will have to store the file path to a variable in indigo
		#
		self.ArrivalSchedule = askopenfilename()
		self.NewArrivals = self.ArrivalSchedule.replace("ArrivalSchedule", "NewArrivals")
		if self.debugDevice: mmLib_Log.logForce("New Arrival Schedule is: " + self.ArrivalSchedule)
		return (0)

	################### New Code ###################

	def checkASCIIContent(self, filename):
		# Note and Delete any non-ASCII characters in the file
		backup_filename = f"{filename}.bak"
		shutil.copyfile(filename, backup_filename)
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + "*** Processing checkDataIntegrity ***")

		try:
			# Read the content from the file
			with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + "Processing: " + filename)
				content = file.read()
				originalFileLength = len(content)
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + "Count: ", originalFileLength)

			# Strip non-ASCII characters
			ascii_content = ''.join(char for char in content if ord(char) < 128)
			newFileLength = len(ascii_content)
			if (newFileLength != originalFileLength):
				fileLengthDelta = originalFileLength - newFileLength
				if self.debugDevice: mmLib_Log.logForce(
					self.deviceName + "### Non-ASCII characters found in file. Count: ", fileLengthDelta,
					" They have been removed.")

			# Write the ASCII-only content back to the file
			with open(filename, 'w', encoding='ascii', errors='ignore') as file:
				file.write(ascii_content)

		except Exception as e:
			# Restore the backup in case of any error
			shutil.copyfile(backup_filename, filename)
			mmLib_Log.logForce(
				self.deviceName + "# An error occurred: {e}. The original file has been restored from {backup_filename}.")

	def checkPinIntegrity(self, dictEntry):
		#
		# check pim integrity
		#
		lPin = len(dictEntry['Code'])

		# for the purposes of this module we only allow 4 digit pins, though the hardware supports many lengths. We are forcing 4 digit below.
		# if lPin not in [4,6,8,32]:

		if lPin != 4:
			priorCode = dictEntry['Code']
			if lPin < 4:
				dictEntry['Code'] = dictEntry['Code'].zfill(4)
			else:
				# Must be greeter than 4
				dictEntry['Code'] = dictEntry['Code'][:4]
			if self.debugDevice: mmLib_Log.logForceAndMail(
				self.deviceName + " ### WARNING This plugin only supports 4 digit DoorCodes. Replacing given code (" + priorCode + ") with " +
				dictEntry['Code'] + " for " +
				dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"] + "\'.",
				"SandCastle Automation Message", "9258727124@vtext.com")

		return (dictEntry)

	def getISOTime(self, dictEntry, dateName):

		try:
			theTimeISO = datetime.isoformat(datetime.strptime(dictEntry[dateName], "%m/%d/%y"))
		except Exception as e:
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Time format Error " + dictEntry["GuestName"])
			theTimeISO = 0

		return (theTimeISO)

	def checkDateIntegrity(self, dictEntry):
		#
		# checkDateIntegrity - vsarious date tests with current list entry
		#
		if self.debugDevice: mmLib_Log.logForce("##### In checkDateIntegrity")

		if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Converting ISO Times " + dictEntry["GuestName"])

		arrivalTimeISO = self.getISOTime(dictEntry, "ArrivalDate")
		departureTimeISO = self.getISOTime(dictEntry, "DepartureDate")

		if arrivalTimeISO >= departureTimeISO:
			if self.debugDevice: mmLib_Log.logForceAndMail(
				self.deviceName + " WARNING: Arrival Date is >= Departure. Set to arrival + 2 Days. " +
				dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"] + "\'.",
				"SandCastle Automation Message", "9258727124@vtext.com")
			parsed_date = datetime.fromisoformat(arrivalTimeISO)
			new_datetime = parsed_date + timedelta(days=2)

			# Convert the new datetime object back to an ISO 8601 formatted string

			departureTimeISO = new_datetime.isoformat()
			parsed_date = datetime.fromisoformat(departureTimeISO)
			mdy_date_str = parsed_date.strftime("%m/%d/%y")

			# Get rid of leading zeros in date
			month, day, year = mdy_date_str.split("/")

			# Convert the components to integers to remove leading zeros
			month = int(month)
			day = int(day)
			year = int(year)

			# Format back into "m/d/y"
			mdy_date_str = f"{month}/{day}/{year}"

			# print("## New Departure Time: " + str(mdy_date_str))
			dictEntry["DepartureDate"] = mdy_date_str
			if self.debugDevice: mmLib_Log.logForceAndMail(
				self.deviceName + "   New Departure Date is " + dictEntry["DepartureDate"] + " for " +
				dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"] + "\'.",
				"SandCastle Automation Message", "9258727124@vtext.com")

		return (dictEntry)

	def makeScheduleDict(self, theFilePath, todayISO, ignoreDates):
		#
		# makeScheduleDict - We manage the schedule through two files. We make a dict from those files for easy processing.
		# This routine is called twice... once for the primary schedule, and once for the new arrival additions
		#
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### File Open ###")

		fResult = 0
		self.currentHeader = 0

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Processing file: " + theFilePath)

		self.checkASCIIContent(theFilePath)

		try:
			f = open(theFilePath, 'r', encoding='utf-8')
		# f = open(theFilePath, 'r')
		except Exception as e:
			mmLib_Log.logForce(self.deviceName + " Error opening file in parseOccupancySchedule(): " + str(
				e) + " Terminating session.")
			# Sometimes we cant find a file, or in the icloud repository is not available
			return (-1)

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### File Open ###")
		try:
			rawLineList = f.readlines()
		except Exception as e:
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### File Readline Error ###")
			if self.debugDevice: mmLib_Log.logForce(
				self.deviceName + " Error with f.readlines() in parseOccupancySchedule(): " + str(
					e) + " Terminating session.")
			# sometimes the file cant be read or has an illegal character
			return (-1)

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Read Complete")

		# Now go through every line in the file to make a new dict

		for line in rawLineList:
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " " + line)

			lineList = line.strip()
			lineList = lineList.split(",")

			# Process this line. If it is the first line, its the header
			if not self.currentHeader:
				self.currentHeader = lineList
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Have Header")
				continue
			else:
				try:
					dictEntry = dict(list(zip(self.currentHeader, lineList)))
				except Exception as e:
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Failure to make dictionary")
					if self.debugDevice: mmLib_Log.logForce(
						self.deviceName + " Processing Schedule Failure to make dictionary: " + str(
							e) + " Terminating session.")
					break

				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Have dict entry: " + str(dictEntry))

				dictEntry = self.checkPinIntegrity(dictEntry)

				try:
					arrivalTimeISO = datetime.isoformat(datetime.strptime(dictEntry["ArrivalDate"], "%m/%d/%y"))
				except Exception as e:
					mmLib_Log.logForce(self.deviceName + " Arrival Time format Error " + dictEntry["GuestName"])
					continue
				if self.debugDevice: mmLib_Log.logForce(
					self.deviceName + " Arrival TimeISO = " + str(arrivalTimeISO))

				try:
					departureTimeISO = datetime.isoformat(datetime.strptime(dictEntry["DepartureDate"], "%m/%d/%y"))
				except Exception as e:
					mmLib_Log.logForceAndMail(self.deviceName + + " WARNING: Departure Time format Error.",
											  "SandCastle Automation Message", "9258727124@vtext.com")
					continue

				dictEntry = self.checkDateIntegrity(dictEntry)
				if self.debugDevice: mmLib_Log.logForce( self.deviceName + " Date Integrity Done")

				arrivalTimeISO = self.getISOTime(dictEntry, "ArrivalDate")
				departureTimeISO = self.getISOTime(dictEntry, "DepartureDate")

				if todayISO > arrivalTimeISO:
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " todayISO > arrivalTimeISO")
					# Tennant arrived 1 or more days ago, but may be due to leave today
					if not ignoreDates and todayISO >= departureTimeISO:
						# Departure time is today, or in the past. Mark the code for deletion,
						self.scheduleDict["Delete"] = dictEntry
						if self.debugDevice: mmLib_Log.logForce(
							self.deviceName + " Stay is over, marking entry \'" + dictEntry['GuestName'] + " " +
							dictEntry['ArrivalDate'] + "\' for deletion.")
					else:
						# the tenant is still here
						if self.debugDevice: mmLib_Log.logForce(
							self.deviceName + " Preserving current tenant\'s entry \'" + dictEntry[
								'GuestName'] + " " +
							dictEntry['ArrivalDate'] + "\'")
						self.scheduleDict[arrivalTimeISO] = dictEntry
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + "### Finished todayISO > arrivalTimeISO")
				else:
					#
					# Finally... Schedule item looks good and is in the future, add it to the schedule dict
					#
					if dictEntry['GuestName'] == "": mmLib_Log.logForceAndMail(
						self.deviceName + " WARNING: No GuestName for arrival Date: " + " \'" + dictEntry[
							"ArrivalDate"] + "\'.", "SandCastle Automation Message", "9258727124@vtext.com")
					if self.debugDevice: mmLib_Log.logForce(
						self.deviceName + " Adding entry \'" + dictEntry['GuestName'] + " " + dictEntry[
							'ArrivalDate'] + "\'")
					self.scheduleDict[arrivalTimeISO] = dictEntry

		f.close()

		return (fResult)

	####################### END NEW CODE ######################

	def resetArrivalFile(self, theFilePath):
		#
		# resetArrivalFile - After we process the arrival file, we reset it to include only the header
		#
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### Resetting Arrival File")

		try:
			f = open(theFilePath, 'r+')
		except Exception as e:
			mmLib_Log.logForce(
				self.deviceName + " Error in resetArrivalFile(): " + str(e) + " Terminating session.")
			return (-1)

		firstLine = f.readline()
		f.seek(0, 0)
		f.truncate()
		# Add Header
		f.write(firstLine)
		f.close()
		return (0)

	def writeScheduleDict(self, theFilePath):
		#
		# writeScheduleDict - After we process new schedule dict, we write it back out to a file. All the unwanted lines have
		# been removed from the dict so the file is self pruning
		#

		# mmLib_Log.logTerse("Parsing file: " + ntpath.basename(theFilePath))			# For just file name
		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " Writing file: " + ntpath.basename(theFilePath))  # For just file name)

		try:
			f = open(theFilePath, 'w+')
		except Exception as e:
			mmLib_Log.logForceAndMail(
				self.deviceName + " Error in parseOccupancySchedule(): " + str(e) + " Terminating session.")
			return (-1)

		f.truncate()
		# Add Header
		string = str(self.currentHeader)
		string = re.sub('[\'\[\]\ ]', '', string)  # take out the brackets, spaces, and single quotes
		f.write(string + "\r\n")

		for anEvent in sorted(self.scheduleDict):
			eventDict = self.scheduleDict[anEvent]
			if anEvent == "Delete":
				if self.debugDevice: mmLib_Log.logForce(
					self.deviceName + " Deleting " + eventDict['GuestName'] + " " + eventDict[
						'ArrivalDate'] + " from arrival schedule. Event is complete")
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
		return (0)

	def convertListToHexStr(self, bList):
		#
		# convertListToHexStr - Utility routine
		#
		return ' '.join(["%02X" % byte for byte in bList])

	def convertListToStr(self, bList):
		#
		# convertListToStr - Utility routine
		#
		return ' '.join(["%02X" % byte for byte in bList])

	def getPinStr(self, inPin):
		#
		# getPinStr - Format the pin string to send via raw command to the lock
		#
		if (len(inPin) == 4):
			d1 = int(ord(inPin[0:1]))
			d2 = int(ord(inPin[1:2]))
			d3 = int(ord(inPin[2:3]))
			d4 = int(ord(inPin[3:4]))
			return [d1, d2, d3, d4]
		elif (len(inPin) == 6):
			d1 = int(ord(inPin[0:1]))
			d2 = int(ord(inPin[1:2]))
			d3 = int(ord(inPin[2:3]))
			d4 = int(ord(inPin[3:4]))
			d5 = int(ord(inPin[4:5]))
			d6 = int(ord(inPin[5:6]))
			return [d1, d2, d3, d4, d5, d6]
		elif (len(inPin) == 8):
			d1 = int(ord(inPin[0:1]))
			d2 = int(ord(inPin[1:2]))
			d3 = int(ord(inPin[2:3]))
			d4 = int(ord(inPin[3:4]))
			d5 = int(ord(inPin[4:5]))
			d6 = int(ord(inPin[5:6]))
			d7 = int(ord(inPin[6:7]))
			d8 = int(ord(inPin[7:8]))
			return [d1, d2, d3, d4, d5, d6, d7, d8]
		elif (len(inPin) == 32):
			d1 = int(inPin[0:2], 16)
			d2 = int(inPin[3:5], 16)
			d3 = int(inPin[6:8], 16)
			d4 = int(inPin[9:11], 16)
			d5 = int(inPin[12:14], 16)
			d6 = int(inPin[15:17], 16)
			d7 = int(inPin[18:20], 16)
			d8 = int(inPin[21:23], 16)
			d9 = int(inPin[24:26], 16)
			d10 = int(inPin[27:29], 16)
			d11 = int(inPin[30:32], 16)
			return [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11]
		else:
			return []

	def setUserPin(self, indigoDevID, userNo, userPin):
		#
		# setUserPin - Send a user code to the lock
		#

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " setUserPin action called")
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Indigo lock selected: " + str(indigoDevID))

		# Hardware supports 4,6,8,32 digit codes, but we only support 4 digits here.

		# if len(userPin) not in [4,6,8,32]:  # commented out.. we only support 4 digit pins
		if len(userPin) != 4:
			mmLib_Log.logForceAndMail(
				self.deviceName + "WARNING This plugin only supports 4 digit DoorCodes. Please manually change this value.",
				"SandCastle Automation Message", "9258727124@vtext.com")
			return

		newPin = ""
		for c in userPin:
			if c in "0123456789":
				newPin = newPin + c
			else:
				newPin = newPin + '0'

		if userPin != newPin:
			mmLib_Log.logForce(
				self.deviceName + " WARNING new User Pin contained non-numeric digits. Substituting " + newPin + " for " + userPin + ".")
			mmLib_Log.logForceAndMail(
				self.deviceName + " WARNING new User Pin contained non-numeric digits. Substituting 0 for each.",
				"SandCastle Automation Message", "9258727124@vtext.com")
			userPin = newPin

		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " Setting PIN for user " + str(userNo) + " to: " + str(userPin))

		codeStr = [99, 0o1, int(userNo), 0o1] + self.getPinStr(userPin)
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### Got CodeString. Looking for " + indigoDevID)

		# mmLib_Log.logForce(self.deviceName + " Sending raw command: [" + self.convertListToStr(codeStr) + "] to device " + str(indigoDevID))
		indigo.zwave.sendRaw(device=indigo.devices[indigoDevID], cmdBytes=codeStr, sendMode=1, waitUntilAck=False)

	def clearUserPin(self, indigoDevID, userNo):
		#
		# clearUserPin - Erase the user pin
		#
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " clearUserPin action called")
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Indigo lock selected: " + str(indigoDevID))

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Clearing PIN for user " + userNo)

		codeStr = [99, 0o1, int(userNo), 0o0]

		# mmLib_Log.logForce(self.deviceName + " Sending raw command: [" + self.convertListToStr(codeStr) + "] to device " + str(indigoDevID))
		indigo.zwave.sendRaw(device=indigo.devices[indigoDevID], cmdBytes=codeStr, sendMode=1, waitUntilAck=False)

	######################################################################################
	#
	# Externally Addessable Routines, must have a single parameter - theCommandParameters
	#
	######################################################################################

	def processSchedule(self, theCommandParameters):
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

		self.ArrivalSchedule = theCommandParameters['ArrivalSchedule']
		self.NewArrivals = theCommandParameters['NewArrivals']
		self.HistoricalArrivals = theCommandParameters['HistoricalArrivals']

		self.scheduleDict = {}
		self.currentHeader = 0
		dateToday = datetime.today()
		dateToday = dateToday.replace(hour=0, minute=0, second=0, microsecond=0)
		todayString = datetime.strftime(dateToday, "%m/%d/%y")
		todayISO = datetime.isoformat(datetime.strptime(todayString, "%m/%d/%y"))

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Making Arrival Dict.")
		# this is a test
		localError = self.makeScheduleDict(self.ArrivalSchedule, todayISO, 0)
		if not localError:
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Finished Arrival Dict. OK")
			localError = self.makeScheduleDict(self.NewArrivals, todayISO, 0)
			if not localError:
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Finished NewArrival Dict. OK")
			else:
				mmLib_Log.logForceAndMail(self.deviceName + " ERROR: Cannot Parse NewArrival Dict",
										  "SandCastle Automation Message", "9258727124@vtext.com")
				return (-1)
		else:
			mmLib_Log.logForceAndMail(self.deviceName + " ERROR: Cannot Parse ArrivalSchedule Dict",
									  "SandCastle Automation Message", "9258727124@vtext.com")
			return (-1)

		deleteDict = self.scheduleDict.get("Delete", 0)
		if deleteDict != 0:
			# delete the door code for this entry
			mmLib_Log.logForceAndMail(
				self.deviceName + " Deleting DoorCode for guest " + deleteDict['GuestName'] + " " + deleteDict[
					'ArrivalDate'], "SandCastle Automation Message", "9258727124@vtext.com")
			for aLock in self.doorLocks:
				self.clearUserPin(aLock, self.userNo)

		# mmLib_Log.logForce(self.deviceName + self.scheduleDict)
		# Look for new DoorCodes to change today?
		changeDict = self.scheduleDict.get(todayISO, 0)

		if changeDict == 0:
			mmLib_Log.logForce(self.deviceName + " Today is " + todayString + ". Nothing to be done.")
		else:

			mmLib_Log.logForceAndMail(" Guest " + changeDict["GuestName"] + " \'" + changeDict["ArrivalDate"] + "\'- \'" + changeDict["DepartureDate"] + "\'. [" + changeDict["Code"] + "]", "SandCastle Message", "9258727124@vtext.com")
			#mmLib_Log.logForce(self.deviceName + "  DoorCode to be reset on " + changeDict["DepartureDate"])

			# Change Lock DoorCode
			for aLock in self.doorLocks:
				mmLib_Log.logForce(self.deviceName + " ### Setting User Pin: " + changeDict["Code"])
				self.setUserPin(aLock, self.userNo, changeDict["Code"])

		# either way, rewrite the arrival schedule file
		localError = self.writeScheduleDict(self.ArrivalSchedule)

		if localError:
			mmLib_Log.logForce(
				self.deviceName + "### Warning ###: Failure writing ArrivalSchedule. Not processing History File.")
		else:
			# Note History, then Truncate the newArrivals file... We don't need to process it again.
			# Add NewArrivals to ArrivalHistory
			self.scheduleDict = {}
			self.currentHeader = 0
			localError = self.makeScheduleDict(self.HistoricalArrivals, todayISO, 1)
			if localError:
				mmLib_Log.logForce(self.deviceName + "### Warning ###: Cannot access History File.")
				localError = self.makeScheduleDict(self.HistoricalArrivals, todayISO, 0)
			else:
				localError = self.makeScheduleDict(self.NewArrivals, todayISO, 0)
				if localError:
					mmLib_Log.logForce(self.deviceName + "### Warning ###: Cannot add newArrivals to History File.")
				else:
					localError = self.writeScheduleDict(self.HistoricalArrivals)
					if localError:
						mmLib_Log.logForce(
							self.deviceName + "### Warning ###: Cannot Write HistoricalArrivals file.")

		if not localError:
			# And Finally delete info from newArrivals
			localError = self.resetArrivalFile(self.NewArrivals)
		else:
			mmLib_Log.logForce(self.deviceName + "### Warning ###: Errors resulted in not resetting Arrival file.")

		return (localError)
