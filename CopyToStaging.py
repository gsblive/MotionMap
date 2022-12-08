import distutils.core
import os
import subprocess
import os
import time

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#
#
# Copy the MotionMap Indigo Plugin to MotionMapStaging
#
#

def	doCopy(targetVolName, pluginName):

	if not os.access(targetVolName, os.W_OK):
		print("### Volume " + targetVolName + " does not exist or have write access ###")
		return 1

	print(str("### Copying " + pluginName + " to " + targetVolName))

	theCommand = "rsync -av --exclude .git --exclude Contents/.idea --exclude venv --exclude Contents/Server\ Plugin/_TestAndSampleCode --exclude Contents/Server\ Plugin/_Documentation " + str(pluginName) + " " + targetVolName + " 2>/dev/null"
	#print str(theCommand)
	#subprocess.call([theCommand])		# this is preferable (with try/except), but I couldnt get it to work right away... revisit.
	result = os.system(theCommand)
	if result:
		print(str(bcolors.FAIL + "###################################"))
		print(str(bcolors.FAIL + "### Copy failed with code " + str(result) + " ###"))
		print(str(bcolors.FAIL + "###################################"))
	else:
		print(str(bcolors.OKGREEN + "###################################"))

	return result


def copyToStaging(volList):
	myPath = os.path.realpath(__file__)
	indigoPlugin = os.path.abspath(os.path.join(myPath, os.pardir))
	#print str(indigoPlugin)
	indigoPlugin = indigoPlugin.replace(' ', '\\ ')
	for theVol in volList:
		print(str(""))
		# print str("### Attempting to copy to " + theVol)
		if not doCopy(theVol, indigoPlugin):
			print(str(""))
			print(str("**********************************"))
			print(str("****       Copy Success       ****"))
			theTimeString = time.strftime("%m/%d/%Y %I:%M:%S %p")
			print(str("****  " + theTimeString + "  ****"))
			print(str("**********************************"))
			break


