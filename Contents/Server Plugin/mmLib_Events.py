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
import mmLib_Low

import sys
from collections import deque
import time

#=============================================
#========== Event related Globals ============
#=============================================

eventPublishers = {}
targettedEvents = {}

#=============================================
#========== Event related Routines ===========
#=============================================


#
# This initialization must be called before any other event routine is called. Call it only once near the begining of your code
#
def initializeEvents():

	global	eventPublishers
	global	targettedEvents


	eventPublishers =	{	'Indigo': 	{
											'AtributeUpdate':deque([]),
											'DevRcvCmd':deque([]),
											'DevCmdComplete':deque([]),
											'DevCmdErr':deque([])
										},
							'MMSys': 	{
											'XCmd':deque([]),
											'isDayTime':deque([]),
											'isNightTime':deque([]),
											'initComplete':deque([])
										}
						}

	targettedEvents = {}

	return 0


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
		# note that if a single subscriber was specified to be delivered to, the queue only has entries relevant to that subscriber (hopefully a single entry, for performance)
		# if (theSubscriber == 0) or (theSubscriber == aSubscriber): # Removed this because its unnecessary as per the note above
		# Add event, timestamp, and publisher
		eventParameters = publisherDefinedData
		eventParameters.update(handlerDefinedData)
		try:
			theHandler(theEvent, eventParameters)
		except Exception as exception:
			mmLib_Log.logForce("Publisher " + str(thePublisher) + ". Distribution failure for event " + theEvent + " to " + theSubscriber + " Error: " + str(exception))
			pass

	return (0)

#
#
#	deliverUpdateEvents
#
#		Update events are a special brand of events that are triggered by differences between two similar objects' values.
#		You must subscribe for event type 'AtributeUpdate', and pass a monitoredAttributes dict in during the subscription process.
#		This dict will be preserved and utilized whenever an object1/object2 is detected elsewhere resulting in a call to this function.
#
#  		This routine should be called whenever the condition object1 != object2 is detected. DeliverUpdateEvents will use
#		the monitoredAttributes dict to parse the given objects to determine if the changes are interesting enough to dispatch an event.
#		If the object change matches an event of interest, an event represented by the name of the the attribute that has changed will
# 		be dispatched as directed by monitoredAttributes dict.
#
# 		When you subscribe to update events with subscribeToEvents, your monitoredAttributes is a dict that must be passed in through as an entry
# 		in handlerDefinedData (i.e. , handlerDefinedData = {'monitoredAttributes': {}, 'otherStuff':"whatever"}). When you construct your
# 		monitoredAttributes dict, you must have an entry for every single object attribute you are interested in (for the object type you are
# 		planning on supporting).
#
# 		NOTE Currently we support only one type of object at a time - Meaning you can only get updateEvents for one type of object. This may
# 		change in the future. This is because different objects may have the same attribute names and have a potential to cause unexpected results.
#
#  		Also wen constructing your monitoredAttributes dict, you may specify a wildcard event handler of value 0. This means you
#		are choosing to process the event through a masterEventHandler defined in the theHandler parameter sent to subscribeToEvents.
# 		In practice, if you supply a handler in monitoredAttributes, you will get your update event there with the name of the attributeName
# 		you requested in the associated entry of the monitoredAttributes dict. Otherwise, it will come to you as a generic 'AtributeUpdate'
#		event to the masterEventHandler along with all other change events.
#
#		Similarly, yiou can choose to not have a masterEventHandler and process every event individually based on the handlers in
# 		your monitoredAttributes dict.
#
#		Lastly, You can mix and match the above methodologies, for example If you wanted the bulk of your change events to be
# 		handled by a master handler, but a single event to be handled by a specialized handler, you could do this:
#
#			deliverUpdateEvents(self, object1, object2, {'valueName1': 0,'valueName2': targettedHandler, 'valueName3': 0} masterHandler)
#				All changes detected in object1/object2.'valueName2' will be dispatched to targettedHandler and all changes
# 				in 'valueName1' and 'valueName3' will be dispatched to masterHandler (if nonZero)
#
#		NOTE: Dont pass a 0 masterHandler and a monitoredAttributes dict will any 0s in the handler fields... you will get no events for
#		every monitoredAttributes dict with 0 handler. However, if you pass a nonzero in both of these locations, only the 
# 		monitoredAttributes event handler will be called as it has priority.
#
#	Parameter Description
#
#		object1				The object that changed (in its previous state) (This code exclusively uses IndigoObjects here)
#		object2				The object that changed (in its new state) (This code exclusively uses IndigoObjects here)
#		monitoredAttributes 	contains a dict where keyNames is an attribute name from above object that indexes to event
# 							handlers (proc pointers) in the associated value field
#							This is passed in to subscribeToEvents as described above
#		masterHandler		Wildcard handler for all events listed in monitoredAttributes with Null (0) handlers
#
def deliverUpdateEvents(object1, object2, theSubscriber):

	theQueue = targettedEvents.get("Indigo.AtributeUpdate." + theSubscriber, 0)

	if not theQueue or len(theQueue) == 0:
		# mmLib_Log.logWarning("Publisher \'Indigo\' is trying to deliver a \'AtributeUpdate\' event to unregistered subscriber " + theSubscriber + ".")
		return (0)

	aSubscriber, masterHandler, handlerDefinedData = theQueue[0]
	monitoredAttributes = handlerDefinedData.get('monitoredAttributes', {})
	if monitoredAttributes == {}:
		mmLib_Log.logWarning("No monitoredAttributes Sub events declared for " + theSubscriber + ".  Queue Entry: " + str(theQueue[0]))
		return (0)

	#		monitoredAttributes 	contains a dict where keyNames is an attribute name from above object that indexes to event
	# 							handlers (proc pointers) in the associated value field
	#							This is passed in to subscribeToEvents as described above
	#		masterHandler		Wildcard handler for all events listed in monitoredAttributes with Null (0) handlers

	masterEventDict = {}
	deliveredEventsDict = {}
	publisherDefinedData = {'publisher':'Indigo','timestamp':time.mktime(time.localtime()) }

	for whichVal in monitoredAttributes:
		try:
			val1 = getattr(object1, whichVal)
			val2 = getattr(object2, whichVal)
		except:
			pass
			continue

		if val1 != val2:
			# does this event have a special handler?
			if monitoredAttributes[whichVal]:
				try:
					eventParameters = publisherDefinedData
					eventParameters['theEvent'] = whichVal
					eventParameters['whichVal'] = val2
					monitoredAttributes[whichVal](whichVal, eventParameters)
					# and mark the events delivered
					deliveredEventsDict[whichVal] = val2
				except:
					pass
					# message about undeliverable event
					mmLib_Log.logWarning("Event Delivery Failure. Event Type \'" + whichVal + "\' failed to be delivered to " + theSubscriber + ".")
			else:
				# theHandler was 0, commemorate the undelivered event for the masterHandler
				masterEventDict[whichVal] = val2

	# Deliver the master events as necessary
	
	if masterEventDict != {}:
		if masterHandler:
			try:
				eventParameters = publisherDefinedData
				eventParameters['theEvent'] = 'AtributeUpdate'
				eventParameters.update(masterEventDict)
				masterHandler('AtributeUpdate', eventParameters)
				# and mark the events delivered
				deliveredEventsDict.update(masterEventDict)
			except Exception as exception:
				mmLib_Log.logWarning( "Event Delivery Failure. Event Type \'AtributeUpdate\' failed to be delivered to " + theSubscriber + ". Exception: " + str(exception))
				pass
		else:
			# message that we have events targetted for master, but no master handler
			pass
			mmLib_Log.logWarning( "Event Delivery Failure. Event Type \'AtributeUpdate\' failed to be delivered to " + theSubscriber + ". No MasterEventHandler")

	#if len(deliveredEventsDict) != 0:
	#	mmLib_Log.logForce( "Event delivery was attempted: " + theSubscriber + ": " + str(deliveredEventsDict))
	#else:
	#	mmLib_Log.logForce( "NO Event delivery was attempted: " + theSubscriber + ": " + str(deliveredEventsDict))

	return deliveredEventsDict


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
#		theHandler(eventID, eventParameters) or if subscribing from an object... theHandler(self, eventID, eventParameters)
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
#	NOTE: FOR BEST RESULTS, EACH OBJECT SHOULD ONLY REGISTER ONE HANDLER FOR ANY PARTICULAR TYPE OF EVENT. For example, if you have two or more
#	subscriptions for an indigo command event, the whole list of subscriptions must be processed for each event at delivery time. Thats inefficient.
# 	Just make a singler handler to handle all related processes to any specific event.. there is no need to have multiple handlers. By All means,
# 	make different handler for different types event types.. that is, after all what this set of routines is for and has been performance tuned to do just that.
#
#
#	For performance, we maintain two queues here:
#		eventPublishers[publisher][event][list of all subscriber tuples for this event type]	- This is used when we are delivering events to wildcard subscriptions (everyone subscribed to this event)
#		targettedEvents[publisher.event.subscriber]												- This is used to deliver events to a specific subscriber (and avoiding inefficiencies of processing the whole list above)
#																										this would be used to deliver indigo command events from a lightswitch to its mmDevice (the other indigo
#																										event subscribers dont have to be processed for those events - it is not their event)
#
# NOTE: If you are subscribing to event type 'AtributeUpdate', you must pass a monitoredAttributes Dict in handlerDefinedData
#
def subscribeToEvents(theEvents, thePublishers, theHandler, handlerDefinedData, subscriberName):

	global eventPublishers

	for thePublisher in thePublishers:
		for theEvent in theEvents:
			try:
				theQueue = eventPublishers[thePublisher][theEvent]
			except:
				if mmLib_Low.DebugDevices.get(subscriberName, 0): mmLib_Log.logWarning("Publisher " + str(thePublisher) + " is not publishing requested event " + theEvent + " as requested by " + subscriberName)
				continue

			try:
				#if subscriberName == "AeonMultisensorTest1": mmLib_Log.logForce(subscriberName + " Is Subscribing to events " + str(theEvents) + " from publisher " + str(thePublishers) + " with handlerDefinedData of " + str(handlerDefinedData))
				theQueue.append([subscriberName, theHandler, handlerDefinedData])  # insert into appropriate publishers deque
			except:
				mmLib_Log.logForce("Publisher " + str(thePublisher) + " could not append event \'" + theEvent + "\' to subscriber " + str(subscriberName))

			# Now append to the targetted event list too
			try:
				theQueue = targettedEvents[thePublisher + "." + theEvent + "." + subscriberName]
				mmLib_Log.logForce("Publisher " + str(thePublisher) + " is already publishing requested event \'" + theEvent + "\' to subscriber " + str(subscriberName))
			except:
				targettedEvents[thePublisher + "." + theEvent + "." + subscriberName] = deque()
				theQueue = targettedEvents[thePublisher + "." + theEvent + "." + subscriberName]

			try:
				theQueue.append([subscriberName, theHandler, handlerDefinedData])  # insert into appropriate targetted event deque
			except:
				mmLib_Log.logForce("Publisher " + str(thePublisher) + " failed to append targeted event \'" + theEvent + "\' to subscriber " + str(subscriberName))

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
							theTargettedQueue.rotate(-1)	# index to the next publisher.event.subscriber entry

			else:
				theQueue.rotate(-1)		# index to the next publisher.event entry

	return (0)

