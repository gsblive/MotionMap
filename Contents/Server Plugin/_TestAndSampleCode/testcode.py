import os
import sys
import ntpath
from datetime import datetime as dt
from datetime import datetime as dt
from tkinter.filedialog import askopenfilename
import re

scheduleDict = {}
dateToday = 0
todayISO = ""
todayString = ""
currentHeader = 0

# Process NewArrivals and add them to the ArrivalSchedule
# Then, process ArrivalSchedule to change DoorCodes as needed

ArrivalSchedule = "/Users/gbrewer/Library/Mobile Documents/com~apple~CloudDocs/Documents/_Short Term Rentals/SandCastle:Oceanview/ArrivalSchedule.csv"
NewArrivals = "/Users/gbrewer/Library/Mobile Documents/com~apple~CloudDocs/Documents/_Short Term Rentals/SandCastle:Oceanview/NewArrivals.csv"
testSchedule = "/Users/gbrewer/Library/Mobile Documents/com~apple~CloudDocs/Documents/_Short Term Rentals/SandCastle:Oceanview/TestSchedule.csv"

# Note processOccupancySchedule handles all access to ArrivalSchedule. Do not open this file for write access remotely.

# If we cant find the files, we may be able to ask the user to find them.
# we will have to store the file path to a variable in indigo
def selectArrivalFile():
	global ArrivalSchedule
	global todayISO
	ArrivalSchedule = askopenfilename()
	print(ArrivalSchedule)
	return(0)

def makeScheduleDict(theFilePath):
	global scheduleDict
	global currentHeader

	currentHeader = 0

	#mmLib_Log.logTerse("Parsing file: " + ntpath.basename(theFilePath))			# For just file name
	print("Processing file: " + ntpath.basename(theFilePath))							# For just file name)

	try:
		f = open(theFilePath, 'r')
	except Exception as e:
		print("Error in parseOccupancySchedule(): " + str(e) + " Terminating session.")
		return(-1)

	for line in f:
		lineList = line.strip()
		lineList = lineList.split(",")
		#print(lineList[0])

		# Process this line. If it is the first line, its the header
		if not currentHeader:
			#print("Found Header " + line)
			currentHeader = lineList
			continue
		else:
			dictEntry = dict(zip(currentHeader, lineList))
			#print(dictEntry)
			key = dt.isoformat(dt.strptime(dictEntry["ArrivalDate"], "%m/%d/%y"))
			if todayISO > key:
				print("Abandoning expired entry " + key)
			else:
				#print("Adding entry " + key)
				scheduleDict[key] = dictEntry
	f.close()
	return(0)

def resetArrivalFile(theFilePath):

	try:
		f = open(theFilePath, 'r+')
	except Exception as e:
		print("Error in resetArrivalFile(): " + str(e) + " Terminating session.")
		return(-1)

	firstLine = f.readline()
	print(firstLine)
	f.seek(0,0)
	f.truncate()
	# Add Header
	f.write(firstLine)
	f.close()
	return(0)

def writeScheduleDict(theFilePath):
	global scheduleDict
	global currentHeader


	#mmLib_Log.logTerse("Parsing file: " + ntpath.basename(theFilePath))			# For just file name
	print("Writing file: " + ntpath.basename(theFilePath))							# For just file name)

	try:
		f = open(theFilePath, 'w+')
	except Exception as e:
		print("Error in parseOccupancySchedule(): " + str(e) + " Terminating session.")
		return(-1)

	f.truncate()
	# Add Header
	string = str(currentHeader)
	string = re.sub('[\'\[\]\ ]', '', string)	# take out the brackets, spaces, and single quotes
	f.write(string + "\r\n")

	for anEvent in sorted(scheduleDict):
		eventDict = scheduleDict[anEvent]
		print("EventDict: " + str(eventDict))
		ArrivalDate = eventDict['ArrivalDate']
		DepartureDate = eventDict['DepartureDate']
		GuestName = eventDict['GuestName']
		DoorCode = eventDict['Code']
		string = str(ArrivalDate + ',' + DepartureDate + ',' + GuestName + ',' + DoorCode)
		#print("Adding Entry " + string)
		f.write(string + "\r\n")

	# Add the entries

	f.close()
	return(0)

#
# Main
#
dateToday = dt.today()
dateToday = dt.today()
dateToday = dateToday.replace(hour=0, minute=0, second=0, microsecond=0)
todayString = dt.strftime(dateToday, "%m/%d/%y")
todayISO = dt.isoformat(dt.strptime(todayString, "%m/%d/%y"))

localError = makeScheduleDict(ArrivalSchedule)
if not localError: localError = makeScheduleDict(NewArrivals)

#print(scheduleDict)
# Any DoorCodes to change today?
changeDict = scheduleDict.get(todayISO, 0)

if changeDict == 0:
	print("Today is " + todayString + ". Nothing to be done.")
else:
	#print(changeDict)
	print("Changing DoorCode for guest " + changeDict["GuestName"] + " to DoorCode " + changeDict["Code"])
	print("  DoorCode to be reset on " + changeDict["DepartureDate"])

	# Change Lock DoorCode

	# Schedule Lock DoorCode Reset

# either way, rewrite the arrival schedule file
if not localError: localError = writeScheduleDict(ArrivalSchedule)

# Truncate the new arrivals file... We dont need to ptocess it again.
if not localError: localError = resetArrivalFile(NewArrivals)
