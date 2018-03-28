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


