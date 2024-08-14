import os
import subprocess

theFilePath = "/Users/gbrewer/Library/Mobile Documents/com~apple~CloudDocs/Documents/_Short Term Rentals/SandCastle/ArrivalSchedule.csv"
f = open(theFilePath, 'r')
rawLineList = f.readlines()
print(" ### File Intake Done.")
for userEntry in rawLineList:
	print(userEntry)
exit(0)


