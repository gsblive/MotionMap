__author__ = 'gbrewer'

############################################################################################
#
# Imported Definitions
#
############################################################################################

import mmLogic_Load
import mmLib_Log
import mmLib_Low

######################################################
#
# mmInsteonLoad - Insteon, this is the default behavior, so just call the base class
#
######################################################
class mmILoad(mmLogic_Load.mmLoad):


	def __init__(self, theDeviceParameters):

		super(mmILoad, self).__init__(theDeviceParameters)  # Initialize Base Class
	#	if self.initResult == 0:
	#	Continue Init

	######################################################################################
	#
	# End Externally Addessable Routines
	#
	######################################################################################


	def parseUpdate(self, origDev, newDev):
		if self.debugDevice != 0:
			#mmLib_Log.logForce("Parsing Update for mmILoad: " + self.deviceName + " with Value of: " + str(newDev))
			diff = mmLib_Low._only_diff(unicode(origDev).encode('ascii', 'ignore'), unicode(newDev).encode('ascii', 'ignore'))
			mmLib_Log.logForce("Parsing Update for mmILoad: " + self.deviceName + " with Value of: " + str(diff))
		return 0	#0 means did not process

	def parseCommand(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Command for mmILoad: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

	def parseCompletion(self, theInsteonCommand):
		if self.debugDevice != 0: mmLib_Log.logForce("Parsing Completion for mmILoad: " + self.deviceName + " with Value of " + str(theInsteonCommand))
		return 0	#0 means did not process

