import distutils.core
import os

#Copy the MotionMap Indigo Plugin to MotionMapStaging

myPath = os.path.realpath(__file__)
indigoPlugin = os.path.abspath(os.path.join(myPath, os.pardir))
#indigoPlugin = indigoPlugin + '/'
print str(indigoPlugin)
indigoPlugin = indigoPlugin.replace(' ', '\\ ')
theCommand = "rsync -av --exclude .git --exclude Contents/Server\ Plugin/_TestAndSampleCode --exclude Contents/Server\ Plugin/_Documentation " + str(indigoPlugin) + " /Volumes/MotionMapStagingSkyCastle-2"
#theCommand = "ditto -v " + str(indigoPlugin) + " /Volumes/MotionMapStagingSkyCastle-2/MotionMap\ 3.IndigoPlugin"
print str(theCommand)
os.system(theCommand)
#os.system("rsync -av indigoPlugin /Volumes/MotionMapStagingSkyCastle-2")
#os.system("rsync -av /MotionMap\ 3.indigoPlugin /Volumes/MotionMapStagingSkyCastle-2")
quit()

# Main Code
#targetPath = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') + "/MotionMapStaging/MotionMap 3.indigoPlugin"
targetPath = "/Volumes/MotionMapStagingSkyCastle/MotionMap 3.indigoPlugin"
myPath = os.path.realpath(__file__)
indigoPlugin = os.path.abspath(os.path.join(myPath, os.pardir))

print "copy " + indigoPlugin + " to " + targetPath
distutils.dir_util.copy_tree(indigoPlugin, targetPath)
