from datetime import datetime,timedelta
import os
import shutil

#Replace mmLib_Log.logForce with print
#Replace deviceName with "TestConsole"
#Replace mmLib_Log.logForceAndMail with print
#self.currentHeader with self.currentHeader
#self.debugDevice with debugDevice

# "self," with ""
import shutil

def checkASCIIContent(filename):
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
		if(newFileLength != originalFileLength):
			fileLengthDelta = originalFileLength - newFileLength
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + "### Non-ASCII characters found in file. Count: ", fileLengthDelta, " They have been removed.")

		# Write the ASCII-only content back to the file
		with open(filename, 'w', encoding='ascii', errors='ignore') as file:
			file.write(ascii_content)

	except Exception as e:
		# Restore the backup in case of any error
		shutil.copyfile(backup_filename, filename)
		mmLib_Log.logForce(self.deviceName + "# An error occurred: {e}. The original file has been restored from {backup_filename}.")


def checkPinIntegrity(dictEntry):
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
		if self.debugDevice: mmLib_Log.logForceAndMail(self.deviceName + " ### WARNING This plugin only supports 4 digit DoorCodes. Replacing given code (" + priorCode + ") with " + dictEntry['Code'] + " for " +
			dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"]+ "\'.",
			"SandCastle Automation Message", "9258727124@vtext.com")

	return (dictEntry)

def getISOTime( dictEntry, dateName):
	try:
		theTimeISO = datetime.isoformat(datetime.strptime(dictEntry[dateName], "%m/%d/%y"))
	except Exception as e:
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + dateName + " Time format Error " + dictEntry["GuestName"])
		theTimeISO = 0

	return (theTimeISO)


def checkDateIntegrity(dictEntry):
	#
	# checkDateIntegrity - vsarious date tests with current list entry
	#
	arrivalTimeISO = getISOTime(dictEntry, "ArrivalDate")
	departureTimeISO = getISOTime(dictEntry, "DepartureDate")

	if arrivalTimeISO >= departureTimeISO:
		if self.debugDevice: mmLib_Log.logForceAndMail(self.deviceName + " WARNING: Arrival Date is >= Departure. Set to arrival + 2 Days. " +
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
		if self.debugDevice: mmLib_Log.logForceAndMail(self.deviceName + "   New Departure Date is " + dictEntry["DepartureDate"] + " for " +
			dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"] + "\'.",
			"SandCastle Automation Message", "9258727124@vtext.com")

	return (dictEntry)



def makeScheduleDict( theFilePath, todayISO, ignoreDates):
	#
	# makeScheduleDict - We manage the schedule through two files. We make a dict from those files for easy processing.
	# This routine is called twice... once for the primary schedule, and once for the new arrival additions
	#

	fResult = 0
	self.currentHeader = 0

	if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Processing file: " + theFilePath)

	checkASCIIContent(theFilePath)

	try:
		f = open(theFilePath, 'r', encoding='utf-8')
		#f = open(theFilePath, 'r')
	except Exception as e:
		mmLib_Log.logForce(self.deviceName + " Error opening file in parseOccupancySchedule(): " + str(e) + " Terminating session.")
		# Sometimes we cant find a file, or in the icloud repository is not available
		return (-1)

	if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### File Open ###")
	try:
		rawLineList = f.readlines()
	except Exception as e:
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### File Readline Error ###")
		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Error with f.readlines() in parseOccupancySchedule(): " + str(
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
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Processing Schedule Failure to make dictionary: " + str(e) + " Terminating session.")
				break

			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Have dict entry: " + str(dictEntry))

			dictEntry = checkPinIntegrity(dictEntry)

			try:
				arrivalTimeISO = datetime.isoformat(datetime.strptime(dictEntry["ArrivalDate"], "%m/%d/%y"))
			except Exception as e:
				mmLib_Log.logForce(self.deviceName + " Arrival Time format Error " + dictEntry["GuestName"])
				continue
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Arrival TimeISO = " + str(arrivalTimeISO))

			try:
				departureTimeISO = datetime.isoformat(datetime.strptime(dictEntry["DepartureDate"], "%m/%d/%y"))
			except Exception as e:
				if mmLib_Log.logForceAndMail(self.deviceName + + " WARNING: Departure Time format Error.",
				                          "SandCastle Automation Message", "9258727124@vtext.com")
				continue

			dictEntry = checkDateIntegrity(dictEntry)

			arrivalTimeISO = getISOTime(dictEntry, "ArrivalDate")
			departureTimeISO = getISOTime(dictEntry, "DepartureDate")

			if todayISO > arrivalTimeISO:
				# Tennant arrived 1 or more days ago, but may be due to leave today
				if not ignoreDates and todayISO >= departureTimeISO:
					# Departure time is today, or in the past. Mark the code for deletion,
					scheduleDict["Delete"] = dictEntry
					if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Stay is over, marking entry \'" + dictEntry['GuestName'] + " " + dictEntry['ArrivalDate'] + "\' for deletion.")
				else:
					# the tenant is still here
					if self.debugDevice: mmLib_Log.logForce(
						self.deviceName + " Preserving current tenant\'s entry \'" + dictEntry[
							'GuestName'] + " " +
						dictEntry['ArrivalDate'] + "\'")
					scheduleDict[arrivalTimeISO] = dictEntry
			else:
				#
				# Finally... Schedule item looks good and is in the future, add it to the schedule dict
				#
				if dictEntry['GuestName'] == "": mmLib_Log.logForceAndMail(self.deviceName + " WARNING: No GuestName for arrival Date: " + " \'" + dictEntry[
						"ArrivalDate"] + "\'.", "SandCastle Automation Message", "9258727124@vtext.com")
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Adding entry \'" + dictEntry['GuestName'] + " " + dictEntry['ArrivalDate'] + "\'")
				scheduleDict[arrivalTimeISO] = dictEntry

	f.close()

	return (fResult)

debugDevice = 1
scheduleDict = {}
dateToday = datetime.today()
dateToday = dateToday.replace(hour=0, minute=0, second=0, microsecond=0)
todayString = datetime.strftime(dateToday, "%m/%d/%y")
todayISO = datetime.isoformat(datetime.strptime(todayString, "%m/%d/%y"))
theFilePath = '/Users/gbrewer/Library/Mobile Documents/com~apple~CloudDocs/Documents/_Short Term Rentals/SandCastle/ArrivalSchedule.csv'
if self.debugDevice: mmLib_Log.logForce(self.deviceName + "Opening Schedule CSV file")
makeScheduleDict( theFilePath, todayISO, 0)


#exit()

	####################### OLD CODE ######################
	def checkPinIntegrity(dictEntry):
		#
		# check pim integrity
		#
		lPin = len(dictEntry['Code'])

		# for the purposes of this module we only allow 4 digit pins, though the hardware supports many lengths. We are forcing 4 digit below.
		# if lPin not in [4,6,8,32]:

		if lPin < 4:
			dictEntry['Code'] = dictEntry['Code'].zfill(4)
			lPin = 4
		elif lPin != 4:
			dictEntry['Code'] = dictEntry['Code'][:4]
			mmLib_Log.logForceAndMail(
				self.deviceName + " ### WARNING This plugin only supports 4 digit DoorCodes. Only using the first 4 digits" +
				dictEntry["GuestName"] + " \'" + dictEntry["ArrivalDate"] + "\'" + dictEntry['Code'] + "\'.",
				"SandCastle Automation Message", "9258727124@vtext.com")

		return(dictEntry)

	def checkDateIntegrity(dictEntry,arrivalTimeISO,departureTimeISO):
		#
		# checkDateIntegrity - vsarious date tests with current list entry
		#
		if arrivalTimeISO >= departureTimeISO:
			mmLib_Log.logForceAndMail(
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

		return(dictEntry)

	def getISOTime(self, dictEntry, dateName):
		try:
			theTimeISO = datetime.isoformat(datetime.strptime(dictEntry[dateName], "%m/%d/%y"))
		except Exception as e:
			mmLib_Log.logForce(self.deviceName + dateName + " Time format Error " + dictEntry["GuestName"])
			theTimeISO = 0

		return(theTimeISO)

	def makeScheduleDict(self, theFilePath, todayISO, ignoreDates):
		#
		# makeScheduleDict - We manage the schedule through two files. We make a dict from those files for easy processing.
		# This routine is called twice... once for the primary schedule, and once for the new arrival additions
		#

		fResult = 0
		self.currentHeader = 0

		if self.debugDevice: mmLib_Log.logForce(
			self.deviceName + " Processing file: " + theFilePath)  # For just file name

		try:
			f = open(theFilePath, 'r', encoding='utf-8')
		except Exception as e:
			mmLib_Log.logForceAndMail(self.deviceName + "Error opening file in parseOccupancySchedule(): " + str(e) + " Terminating session.")
			# Sometimes we cant find a file, or in the icloud repository is not available
			return (-1)

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### File Open ###")
		try:
			rawLineList = f.readlines()
		except Exception as e:
			if self.debugDevice: mmLib_Log.logForce(self.deviceName + " ### File Readline Error ###")
			mmLib_Log.logForceAndMail(
				self.deviceName + "Error with f.readlines() in parseOccupancySchedule(): " + str(e) + " Terminating session.")
			# sometimes the file cant be read or has an illegal character
			return (-1)

		if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Read Complete")

		# Now go through every line in the file to make a new dict

		for line in rawLineList:
			if self.debugDevice: mmLib_Log.logForce(line)

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
					mmLib_Log.logForce(self.deviceName + " Failure to make dictionary")
					mmLib_Log.logForceAndMail(self.deviceName + "Processing Schedule Failure to make dictionary: " + str(e) + " Terminating session.")
					break

				if self.debugDevice: mmLib_Log.logForce(self.deviceName + " Have dict entry: " + str(dictEntry))

				dictEntry = self.checkPinIntegrity(dictEntry)

				try:
					arrivalTimeISO = datetime.isoformat(datetime.strptime(dictEntry["ArrivalDate"], "%m/%d/%y"))
				except Exception as e:
					mmLib_Log.logForce(self.deviceName + "Arrival Time format Error " + dictEntry["GuestName"])
					continue
				if self.debugDevice: mmLib_Log.logForce(self.deviceName + "Arrival TimeISO = " + str(arrivalTimeISO))

				try:
					departureTimeISO = datetime.isoformat(datetime.strptime(dictEntry["DepartureDate"], "%m/%d/%y"))
				except Exception as e:
					mmLib_Log.logForceAndMail(self.deviceName + " WARNING: Departure Time format Error.",
											  "SandCastle Automation Message", "9258727124@vtext.com")
					continue

				dictEntry = self.checkDateIntegrity(dictEntry,arrivalTimeISO,departureTimeISO)

				if todayISO > arrivalTimeISO:
					# Tennent arrived 1 or more days ago, but may be due to leave today
					if not ignoreDates and todayISO >= departureTimeISO:
						# Departure time is today, or in the past. Mark the code for deletion,
						self.scheduleDict["Delete"] = dictEntry
						if self.debugDevice: mmLib_Log.logForce(
							self.deviceName + " self.deviceName + Stay is over, marking entry \'" + dictEntry[
								'GuestName'] + " " + dictEntry['ArrivalDate'] + "\' for deletion.")
					else:
						# the tenant is still here
						if self.debugDevice: mmLib_Log.logForce(
							self.deviceName + " Preserving current tenant\'s entry \'" + dictEntry[
								'GuestName'] + " " +
							dictEntry['ArrivalDate'] + "\'")
						self.scheduleDict[arrivalTimeISO] = dictEntry
				else:
					#
					# Finally... Schedule item looks good and is is in the future, add it to the schedule dict
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

###################### END OLD CODE #####################