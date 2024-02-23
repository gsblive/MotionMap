import CopyToStaging
import os

##############
#  Main
##############

print("*** CopyToStagingRegency ***")
if 0:
	theDirName = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Documents/MotionMap_Staging/Current/")
	print("Destination Directory: "+ theDirName)
	print(os.listdir(theDirName))
	CopyToStaging.copyToStaging([theDirName])
else:
	CopyToStaging.copyToStaging(["/Volumes/MotionMapStagingRegency"])
	quit()

