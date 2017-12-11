import distutils.core
import os

# Main Code
targetPath = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') + "/MotionMapStaging/MotionMap 3.indigoPlugin"
myPath = os.path.realpath(__file__)
indigoPlugin = os.path.abspath(os.path.join(myPath, os.pardir))

print "copy " + indigoPlugin + " to " + targetPath
distutils.dir_util.copy_tree(indigoPlugin, targetPath)
