import distutils.core
import os
import subprocess
import os
import datetime
import time

#
# NOTE: MM development has an automatic reload function that needs to be kept up to date.
#		If you change the project name, you may need to edit the path in an indigo Action Group called _ReinstallMotionMap3
#		That action group looks for a copy of MotionMap in a specific location in ICloud to execute a live replacement routine.
#			The replacement routine is accessed by a shell script in the file named RunReplaceMotionMap.txt (built into the MotionMap Bundle)
#			That shell script executes an OSA script called ReplaceMotionMap.scpt (also built into the bundle)
#			This OSA file will halt MotionMap plugin, move the new version of MotionMap into place (in the indigo plugin folder) and restart It.
#
#		There is a support action group in Indigo that runs the ShellScript mentioned above. the Action group is called _ReInstallMotionMap3
#
#		This is all true for another action Group called _RollbackMotionMap3 Which does all the same things, but installs a previous version of MotionmMap
#
#		Directory Structure that Indigo Action groups are expecting these motionmap versions are:
#		New Install of MotionMap:
#			/Users/gbrewer/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/_MotionMapStaging/Current/MotionMap\ 3.IndigoPlugin
#			The path above will be used to execute /RunReplaceMotionMap.txt as described above.
#			Set the variable in _ReInstallMotionMap 3 action group to the full pathname of the .txt file...
#			/Users/gbrewer/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/_MotionMapStaging/Current/MotionMap\ 3.IndigoPlugin/RunReplaceMotionMap.txt
#
#		New Rollback of MotionMap:
#			/Users/gbrewer/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/_MotionMapStaging/RollBack/MotionMap\ 3.IndigoPlugin
#			The path above will be used to execute /RunReplaceMotionMap.txt as described above.
#			Set the variable in _ReInstallMotionMap 3 action group to the full pathname of the .txt file...
#			/Users/gbrewer/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/_MotionMapStaging/RollBack/MotionMap\ 3.IndigoPlugin/RunReplaceMotionMap.txt
#
#	As you can see these files are kept in an iCloud directory.. this is because it allows the development environment to be remote and the MotionMap binary Bundle
#	to be replaced from anywhere in the world (by simply copying the MM bundle into the iCloud drive in the location described above), then remote control
#	into the Indigo automation server to execute the ReInstall or Rollback action groups as needed.

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
# Copy the MotionMap Indigo Plugin to _MotionMapStaging
#
#

def	doCopy(targetVolName, pluginName):
	#print("volName = " + targetVolName)
	#print("pluginName = " + pluginName)

	#print(str("### Copying " + pluginName + " to " + targetVolName))

	theCommand = "rsync -av --exclude .git --exclude Contents/.idea --exclude venv --exclude Contents/Server\ Plugin/_TestAndSampleCode --exclude Contents/Server\ Plugin/_Documentation " + str(pluginName) + " " + targetVolName + " 2>/dev/null"

	print(str(theCommand))
	#subprocess.call([theCommand])		# this is preferable (with try/except), but I couldnt get it to work right away... revisit.
	result = os.system(theCommand)
	if result:
		print(str(bcolors.FAIL + "###################################"))
		print(str(bcolors.FAIL + "### Copy failed with code " + str(result) + " ###"))
		print(str(bcolors.FAIL + "###################################"))
	else:
		print(str(bcolors.OKGREEN + "###################################"))

	return result


def copyToVolList(volList):
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


print("*** CopyToStaging ***")
myPath = os.path.realpath(__file__)


theStatDir = os.path.expanduser(str("~/Library/Mobile Documents/com~apple~CloudDocs/Documents/_MotionMapStaging/Current/"))
theCopyDir = theStatDir.replace(" ","\ ")	# because os.access doesnt like escape characters before spaces

indigoPlugin = os.path.abspath(os.path.join(myPath, os.pardir))
indigoPlugin = indigoPlugin.replace(' ', '\\ ')

################# Update the MM_VersionInfo.py file
#
# Should initially read:
#
# MM_UploadTime = "currentTime"
# MM_UploadTime above must be first line as it is processed during upload routine (CopyToStaging)
# Etc...
# MM_Name =
#####################################

# First update the upload time field in MM_VersionInfo

VIFile = os.path.abspath(os.path.join(myPath, os.pardir) + "/Contents/Server Plugin/MM_VersionInfo.py")
theTimeString = time.strftime("%m/%d/%Y %I:%M:%S %p")
newFirstLine = "MM_UploadTime = " + '\"' + theTimeString + '\"'	# Inject the necessary quotes around the date/time assignment
newFirstLine = newFirstLine.replace('/', '\/')		# excape the date slashes
print("#### Updating first line of MM_VersionInfo to: " + "'" + newFirstLine + "'")
cmd = ['sed', '-i', '-e', '1,1s/.*/' + newFirstLine + '/g', VIFile]
subprocess.call(cmd)
quit()
###########################################################

theResult = os.access(theStatDir, os.W_OK)
if not theResult:
	print("### Volume " + theStatDir + " does not exist or have write access ###")
	exit()

#print(" Plugin Name: " + indigoPlugin)
#print(" theCopyDir Name: " + theCopyDir)

if not doCopy(theCopyDir, indigoPlugin):
	print(str(""))
	print(str("**********************************"))
	print(str("****       Copy Success       ****"))
	theTimeString = time.strftime("%m/%d/%Y %I:%M:%S %p")
	print(str("****  " + theTimeString + "  ****"))
	print(str("**********************************"))



quit()

