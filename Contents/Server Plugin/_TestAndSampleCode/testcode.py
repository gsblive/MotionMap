import os
import subprocess

theStatDir = str("~/Library/Mobile Documents/com~apple~CloudDocs/Documents/MotionMapStaging/Current/")
targetDir = os.path.expanduser(theStatDir)

theResult = os.access(targetDir, os.W_OK)
if not theResult:
	print("### Volume " + targetDir + " does not exist or have write access ###")
else:
	print(str("os.access result is: " + str(theResult)))

quit()

sourceFile = "/Users/gbrewer/PycharmProjects/MotionMap\ 3.indigoPlugin"

myPath = os.path.realpath(__file__)
#indigoPlugin = os.path.abspath(os.path.join(myPath, os.pardir))
indigoPlugin = os.path.abspath(os.path.join(myPath))
print("##PluginFile to Copy: " + str(indigoPlugin))
indigoPlugin = indigoPlugin.replace(' ', '\\ ')

print(sourceFile)
print(indigoPlugin)

targetDir = os.path.expanduser("~/Library/Mobile\ Documents/com~apple~CloudDocs/Documents/MotionMapStaging/Current")
theCommand = "rsync -av --exclude .git --exclude Contents/.idea --exclude venv --exclude Contents/Server\ Plugin/_TestAndSampleCode --exclude Contents/Server\ Plugin/_Documentation " + sourceFile + " " + targetDir
result = os.system(theCommand)
