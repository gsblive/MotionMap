__author__ = 'gbrewer'
############################################################################################
#
#	mmLib_Events
#
#		Event subscription and distribution functions for MotionMap.
#
#		All modules and devices in MotionMap communicate through a series of Events... This
#		allows for comprehensive debugging, logging, testing, expansion, and code consistency
# 		between modules.
#
# 		The following routines constitute the entire Event processing Library.
# 		This file must be imported by all modules that are to use events
#
#		Events can be used in in conjunction with the Command Queue and DelayedProcessing
#	 	functions of other MMLib modules where Dict based parameters are utilized
#
############################################################################################

############################################################################################
#
# Imported Definitions
#
############################################################################################

try:
	import indigo
except:
	pass

import mmLib_Log
from collections import deque
import time

#=============================================
#========== Event related Globals ============
#=============================================

eventPublishers = {'Indigo': {'DevUpdate':deque([]),'DevRcvCmd':deque([]),'DevCmdComplete':deque([]),'DevCmdErr':deque([])}, 'MMSys': {'XCmd':deque([])}}
targettedEvents = {}


#
# registerPublisher - All event publishers must first register before they can receive event subscriptions
#
#	Events:
#		a list of events that are published
#
#	Publisher:
#		Text string identifying the publisher of the event. For example..
#
#		'Indigo'	Hardware Sourced Event, like a light switch was turned on (Initialized by the system)
#		MMDevName	Any MM Device (this can create and use any custom event, for any purpose)
#		'Action'	an Indigo Action Script (Initialized by the system)
#
#		Example events supported (there are many others, MMDevices define their own):
#
#		EventID			Publisher					Description
#		'on'			MotionSensor (MMDevName)	The motion sensor is publishing on event
#		'off'			Indigo						An Off Event was detected form an indigo device
#		'occupied'		VirtualMotionSensor			A motion sensor generated an ON sigl\nal causing a group to be occupied
#		'stateChange'	Indigo						Indigo detected a statusUpdate from a device
#		'execute'		'MMSys'						executeMMCommand (all MMDevices register for this event at a minimum)
#
def registerPublisher(theEvents, thePublisher):

	global eventPublishers

	# Get Publisher's event Dict
	try:
		PublishersEventsDict = eventPublishers[thePublisher]
	except:
		eventPublishers[thePublisher] = {}
		PublishersEventsDict = eventPublishers[thePublisher]

	for theEvent in theEvents:

		# Get the Event deque for each event requested

		try:
			theQueue = PublishersEventsDict[theEvent]
		except:
			PublishersEventsDict[theEvent] = deque()
			theQueue = PublishersEventsDict[theEvent]

	return (0)

#
# distributeEvent - When a publisher has an event to publish... this is how its done
#
#	Calls the event handler registered in subscribeToEvents above for the event 'theEvent' given below
#
# The format of the event handler is
#
#		theHandler(eventID, eventParameters)
#
#	where eventParameters is a dict containing:
#
# thePublisher				The name of the Registered publisher (see above) who is sending the event
# theEvent					The text name of the event to be sent (see subscribeToEvents below)
# theSubscriber				The Text Name of the Subscriber to receive the event
# publisherDefinedData		Any data the publisher chooses to include with the event (for example, if it
# 								is an indigo command event, we might include the whole indigo command record here)
# timestamp					The time (in seconds) the event is being published/distributed
#
def distributeEvent(thePublisher, theEvent, theSubscriber, publisherDefinedData):

	global eventPublishers

	if theSubscriber:
		# load a deque with a single entry (no searching necessary) just go to deque the single handlerInfo entry
		theQueue = targettedEvents.get(thePublisher + "." + theEvent + "." + theSubscriber, 0)
	else:
		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			theQueue = 0

	if not theQueue or len(theQueue) == 0:
		#mmLib_Log.logWarning("No registrations for event " + theEvent + ".")
		return (0)

	publisherDefinedData['theEvent'] = theEvent
	publisherDefinedData['publisher'] = thePublisher
	publisherDefinedData['timestamp'] = time.mktime(time.localtime())

	for aSubscriber, theHandler, handlerDefinedData in theQueue:
		if (theSubscriber == 0) or (theSubscriber == aSubscriber):
			# Add event, timestamp, and publisher
			eventParameters = publisherDefinedData
			eventParameters.update(handlerDefinedData)
			theHandler(theEvent, eventParameters)
	return (0)



#
# subscribeToEvents - add theHandler to be called when any of the events listed in 'theEvents' occur from thePublisher
#
#	Events:
#		a list of events to subscribe to
#
#	thePublishers:
#		A list of Text strings identifying the publisher of the event. For example..
#
#		'Indigo'	Hardware Sourced Event, like a light switch was turned on (Initialized by the system)
#		MMDevName	Any MM Device (this can create and use any custom event, for any purpose)
#		'Action'	an Indigo Action Script (Initialized by the system)
#
#	theHandler:
#		A proc pointer that handles the event. format must be
#		theHandler(eventID, eventParameters)
#
#  		where eventParameters is a dict containing: {theEvent, publisher, Time of Event (seconds), Plus "handlerDefinedData" Passed in at time of registration}
#
#		Example eventIDs supported (there are many others, MMDevices define their own):
#
#		EventID			Publisher					Description
#		'on'			MotionSensor (MMDevName)	The motion sensor is publishing on event
#		'off'			Indigo						An Off Event was detected form an indigo device
#		'occupied'		VirtualMotionSensor			A motion sensor generated an ON sigl\nal causing a group to be occupied
#		'stateChange'	Indigo						Indigo detected a statusUpdate from a device
#
def subscribeToEvents(theEvents, thePublishers, theHandler, handlerDefinedData, subscriberName):

	global eventPublishers

	for thePublisher in thePublishers:
		for theEvent in theEvents:
			try:
				theQueue = eventPublishers[thePublisher][theEvent]
			except:
				mmLib_Log.logWarning("Publisher " + str(thePublisher) + " is not publishing requested event " + theEvent + ".")
				continue

			theQueue.append([subscriberName, theHandler, handlerDefinedData])  # insert into appropriate deque
			# Now append to the targetted event list too
			try:
				theQueue = targettedEvents[thePublisher + "." + theEvent + "." + subscriberName]
				mmLib_Log.logWarning("Publisher " + str(thePublisher) + " is already publishing requested event \'" + theEvent + "\' to subscriber " + str(subscriberName))
			except:
				targettedEvents[thePublisher + "." + theEvent + "." + subscriberName] = deque()
				theQueue = targettedEvents[thePublisher + "." + theEvent + "." + subscriberName]

			theQueue.append([subscriberName, theHandler, handlerDefinedData])  # insert into appropriate deque

	return (0)


#
#	unsubscribeFromEvents
#		if theEvents == 0, unsubscribe all events for given subscriber
#		if subscriberName == 0, unsubscribe requested events for all subscribers
#		if theEvents and subscriberName are both 0, unsubscribe all events for all subscribers for given publisher
#		if the Handler is 0, unsubscribe all handlers that meet the other criteria
#
def unsubscribeFromEvents(theEvents, thePublisher, requestedHandler, subscriberName):

	global eventPublishers

	if not theEvents and not subscriberName:
		# short circuit a lot of processing for this rare occurance
		eventPublishers[thePublisher] = deque([])
		return(0)

	if not theEvents:
		try:
			theEvents = list(eventPublishers[thePublisher].keys())
		except:
			mmLib_Log.logWarning("Invalid publisher " + thePublisher + ".")
			return(0)

	for theEvent in theEvents:

		try:
			theQueue = eventPublishers[thePublisher][theEvent]
		except:
			continue

		theMax = len(theQueue)
		for index in range(theMax):
			aSubscriber, theHandler, handlerDefinedData = theQueue[0]
			if (subscriberName == 0 or subscriberName == aSubscriber) and (requestedHandler == 0 or requestedHandler == theHandler):
				theQueue.popleft()

				# find and delete the associated targettedEvent entry

				theTargettedQueue = targettedEvents.get(thePublisher + "." + theEvent + "." + aSubscriber, 0)
				if theTargettedQueue:
					theTargettedMax = len(theTargettedQueue)
					for targettedIndex in range(theTargettedMax):
						aTargettedSubscriber, theTargettedHandler, targettedHandlerDefinedData = theTargettedQueue[0]
						if (subscriberName == 0 or subscriberName == aTargettedSubscriber) and ( requestedHandler == 0 or requestedHandler == theTargettedHandler):
							theTargettedQueue.popleft()
						else:
							theTargettedQueue.rotate(-1)

			else:
				theQueue.rotate(-1)

	return (0)

