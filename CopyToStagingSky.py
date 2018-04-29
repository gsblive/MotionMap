import distutils.core
import os
import subprocess

#
#
# Copy the MotionMap Indigo Plugin to MotionMapStaging
#
#

def	doCopy(targetVolName, pluginName):

	theCommand = "rsync -av --exclude .git --exclude Contents/Server\ Plugin/_TestAndSampleCode --exclude Contents/Server\ Plugin/_Documentation " + str(pluginName) + " " + targetVolName
	print str(theCommand)
	#subprocess.call([theCommand])		# this is preferable (with try/except), but I couldnt get it to work right away... revisit.
	result = os.system(theCommand)
	if result: print str("### Copying to " + targetVolName + " failed ###")

	return result


##############
#  Main
##############

myPath = os.path.realpath(__file__)
indigoPlugin = os.path.abspath(os.path.join(myPath, os.pardir))
print str(indigoPlugin)
indigoPlugin = indigoPlugin.replace(' ', '\\ ')

if doCopy("/Volumes/MotionMapStagingSkyCastle", indigoPlugin):
	print str("   trying /Volumes/MotionMapStagingSkyCastle-1")
	doCopy("/Volumes/MotionMapStagingSkyCastle-1", indigoPlugin)

quit()

