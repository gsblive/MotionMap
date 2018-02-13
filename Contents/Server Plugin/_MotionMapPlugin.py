##################################################################################
#
# MotionMap3 - Motion Sensor and Home Automation Control for Perceptive Indigo Home
# 				Automation Platform on MacOS
#
#	New version of MotionMap, converted from MotionMap2.
#	Now fully refactored with a new object architecture that maximizes flexibility and maintenance.
#	MotionMap3 is now much more easily extended to new device types and new protocols.
#
# Files
#
#	MotionMap3 is a multi file Indigo plug-in with file bundling as specified in:
#		http://wiki.indigodomo.com/doku.php?id=indigo_6_documentation:documents
#
# 	This file must be included in the plugin package (MotionMap3) in the following location:
#        /Library/Application\ Support/Perceptive\ Automation/Indigo\ 6/Plugins/
#
#
# Environment
#
#	MotionMap3 and Indigo Server are MacOS only.
# 	MotionMap3 was developed exclusively in the PyCharm CE IDE, using Python version 2.6.9 or better
#
# History
#   Date   		Version      Comment
#	mm.dd.2016	0.9.0		To do
#							x Integrate project with GitHub VCS
#							x Add tools to update plug-in from ActionGroup and a pycharm file to copy plug-in to icloud for deployment
#							Nest Thermostat doesnt support Status message
#							Nest Thermostat not staying updated by factoring in temps from all regions (probably a multisensor thing, not updating thermostat object)
#							x if the light switch does not have any associated motion sensors, use max on time instead of max non-motion time
#							x A max Occupancy timer of 0 means never turn off the device due to max occupancy time
#							x use delay timers for periodic status request
#							X improve delay timers for performance and added feature to pass command parameters
#							x added delay timer report for debugging
#							x use bisect for timer management
#							x no longer itterate through all devices when initializing multisensors' sub functions (a list is made first tiem through (10x speed increase in init)
#							x Obsolete Timer Queue, use Delay Queue
#							x Average on/off trasition times for multisensors to detect bouncing (a common problem with fibaro multisensors)
#							On companion brightness change, send new change to Master(but ignore change response for the companion)
#							Log all changes(button Pressing) by device
#							Link validation tool
#							Companion Switches should behave as follows: on Update... 100% should set Master to 100. 0% should set Master to 0.
# 								Anything in between should automatically take care of itself
#  							Uses Standardized CommandParameter based MM commands in all Logic Level objects (mmLogic_HVAC.py, mmLogic_Load.py)
# 							Added support for 'Notification' events that Email Message on certain events (Batt Low, Earthquake, Low/high Temp)
# 							Improve status on occupancy object to read minutes/seconds
#							Use Multifunction sensors as input to thermostat logic routines
#								(list of sensors per thermostat are considered if they are occupied and online)
#							Thermostat logic simplification... use occupancy lists to determine what temperatures to factor in
#							Level 2 heat support (Fireplaces and elec heaters localized in a single room)
#							Change Nest Thermostat processing so that commands we send it dont look like user intervention
#							Timestamp and log all commands going to each device (with calling routine name) for debugging mystery flashes
#							Clear and concise status report message for each object type
#							Allow Companions to have 2 masters
#							x Allow selective switching (on and off) in config file of device parseUpdate log messages
# 							x Add fileNames Procedure Names and line numbers to Log output
# 							x Fixed a bug where the config file wasnt catching bad device names (typos)
#							x Added universal variable to all objects that indicates if the object has successfully initialized
#  							x Improved status on Load object to read minutes/seconds
# 							x Improve discrimination of command completion events. We now identify our completions (even when our device shares
# 								an address or ID with another device) with nearly 100% accuracy
#							x Use timer functions for turning load devices off (and flashing). This gives a much more accurate timing prediction.
#							x Added event support for daytime/nighttime transitions as well as initComplete subscriptions.
#	3.26.2016	0.8.5		Fully Functional to MotionMap2 feature Set
#							Use variable for MM_Plugin Name so we can have universal Action Groups and Triggers.
#	3.7.2016	0.8.0		Move all File name assignments to this file and move config files into the new _Configurations folder
#							Support ZWave Load device completion commands
#							Rewrote Occupation Module for greater flexibility and consistency
#	2.15.2016	0.1.0		Initial Conversion from MotionMap2 v1.1.0
#							Rewrote and renamed Module object hierarchy for clarity and consistency
#							Added TestAndSampleCode folder to Project
#							Created MotionMap3 Object Layout.odg
#
##################################################################################

# NOTE: ENTRY POINT IS IN plugin.py

##################################################################################
#							Project Layout
##################################################################################
#
#	Object Model Layout:
#
#		Indigo System
#			^
#			|					Indigo API processing Messages and commands between indigo and MotionMap
#			v
#		Device Object			For each device we support. Translates Indigo in/out
#			^					messages and commands into Standardized CommandParameter based MM commands to pass to mmType below
#			|					Example: mmDev_InsteonLoad, mmDev_ZWaveLoad
#			v
#		Device Logic Object		Generic Logic processing for each device type (i.e. Motion Sensor, Load, etc)
#			^					Uses Standardized CommandParameter based MM commands, all functions here are externally addressable
#			|					Example: mmLogic_HVAC.py, mmLogic_Load.py
#			v
#	Command Dispatch Object		Instantiated mmObj. Translates mmCommands to outgoing indigo/insteon commands.
#								Files include:
#									mmComm_Indigo			Basic Indigo devices (Root)
#									mmComm_Insteon			Indigo Specific devices (subclass of mmComm_Indigo)
#									mmComm_HVACCommands		Commands that are specific to HVAC objects
#
#
#	mm Support functions		Library used by all objects. Includes Initialization,
# 								Config, logging, timers, Dispatchers, and mm command processing
#								Files Include:
# 									mmLib_Low.py		Low level functions used by system and objects (initialization,timers etc)
# 									mmLib_Log.py		Logger functions (used everywhere)
# 									mmLib_Config.py		Configuration parser (used by mmLib_Low.py when plugin.py calls init routine)
# 									mmLib_CommandQ.py	Command dispatcher functions (used my mmType objects to dispatch commands)
#
#
#
#	Additional Support files:
#
#		plugin.py			Entry point
#
#		::Info.plist		XML file to describe the plug-in to indigo
#
#		Actions.xml			Defines the commands that MM accepts from the indigo system
#
#		/TestAndSampleCode/Indigo.MotionMap.Action.Sample
#							Example of how to communicate with MotionMap devices from Indigo Actions
#
#		_MotionMapPlugin.py	- This File - Contains the name and version number of this plug-in
#
#		Device Statistics	Created and maintained by the system. Track the online/offline stats of all devices.
#								Persistent through power cycles.
#								Name: mmStat.<MMLocation>.p
#
#		Debugging Log		Created by the system. Contains Stack Crawl information provided by mmLib_Log.py
#								Name: MotionMap.log.txt
#
#		Configuration File	CSV file that dictates how MotionMap should be configured
#								Name: mmConfig.<MMLocation>.csv
#
#
#
#
#	Indigo Variables (Required for power cycle persistence):
#
#		MMLocation				The location of this instance of MotionMap (eg Oceanview, Gamay, Engineering)
#
#
#
##################################################################################

import sys
import os.path
import mmLib_Low
import socket
import indigo


############################################################################################
#
# Set Project Name and version number here
#
############################################################################################

#
#  Be sure to change the version number in Info.plist as well
#
MM_NAME = "MotionMap3"
MM_VERSION = "0.9.0"
MM_DEFAULT_LOG_FILE = "MotionMap.log.txt"
fullHost = socket.gethostname()
defaultHostname = fullHost.split('.', 1)[0]
indigo.server.log("Default Host Name is: " + defaultHostname )
MM_Location = mmLib_Low.initIndigoVariable("MMLocation", defaultHostname)# This is a default value. Set Indigo Variable named <MMLocation>
MM_DEFAULT_CONFIG_FILE = os.getcwd() + "/_Configurations/mmConfig." + str(MM_Location) + ".csv"	# this is reset in __Init__
nvFileName = str("mmNonVolatiles." + MM_Location)




############################################################################################
#
#  NOTE: ENTRY POINT IS IN plugin.py
#
# ############################################################################################
