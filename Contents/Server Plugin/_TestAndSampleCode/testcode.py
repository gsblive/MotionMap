import os
import sys
import ntpath
from datetime import datetime
from tkinter.filedialog import askopenfilename
import re
import time
import platform
import datetime


RESET_LOG_SIZE = int(512*1024)
def trimFile(theFileName,resetSize):

	# the log File got unusually large, rename it as an archive so a new file can be created.

	#indigo.server.log("Trimming Log File to: " + str(resetSize) + " @ mmLib_Log.py.trimFile")

	oldFileName = theFileName[:-4]
	oldFileSuffix = theFileName[-4:]
	theDateTime = datetime.datetime.now().strftime("%I:%M:%S %p")
	newFileName = oldFileName + " Overflow Archive " + str(theDateTime) + oldFileSuffix
	print(str(newFileName))
	os.rename(theFileName,newFileName)


print(platform.python_version())
fName = os.path.join(os.path.expanduser("~"), "Files/2022-12-01 Events.txt")
print(fName)

#trimFile(fName, RESET_LOG_SIZE)