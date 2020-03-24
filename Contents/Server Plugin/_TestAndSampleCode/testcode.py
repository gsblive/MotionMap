import os
import sys



os.system("Terminal")

exit()
print os.getcwd()
pathname = str(os.path.expanduser("~") + "/MotionMap3 Logs/")
#os.mkdir(pathname)

try:
	os.mkdir(pathname)
except Exception as err:
	if err.args[0] != 17:
		print ("Creation of the directory %s failed" % pathname)
