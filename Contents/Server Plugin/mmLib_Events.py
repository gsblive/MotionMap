__author__ = 'gbrewer'
############################################################################################
#
#	mmLib_Events
#
#		Routines related to Event subscription and distribution functions for MotionMap.
#
#		All modules and devices in MotionMap communicate through a series of Events Including
#		System Events.
#		Even some Indigo Sourced Events are delivered through this mechanism through
#		plugin.py -> deliverFilteredEvents(), below.
#
#		This allows for comprehensive debugging, logging, testing, expansion, and code consistency
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

	# Initialize system event publishers... Indigo for Indigo events and MMSys for MM system events

	eventPublishers =	{	'Indigo': 	{
											'AttributeUpdate':deque([]),
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
#		'OccupiedAll'		VirtualMotionSensor		A motion sensor generated an ON sigl\nal causing a group to be fully occupied
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
#		'OccupiedAll'	VirtualMotionSensor			A motion sensor generated an ON sigl\nal causing a group to be fully occupied
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
# NOTE: If you are subscribing to event type 'AttributeUpdate', you must pass a monitoredAttributes Dict in handlerDefinedData
#
def subscribeToEvents(theEvents, thePublishers, theHandler, handlerDefinedData, subscriberName):

	global eventPublishers

	for thePublisher in thePublishers:
		for theEvent in theEvents:
			try:
				theQueue = eventPublishers[thePublisher][theEvent]
			except:
				if mmLib_Low.DebugDevices.get(subscriberName, 0): mmLib_Log.logWarning("Publisher " + str(thePublisher) + " is not publishing requested event \'" + theEvent + "\' as requested by " + subscriberName)
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




#
# distributeEvents - When a publisher has an event to publish... this is how its done
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
# theSubscriber				The Text Name of the Subscriber to receive the event, or 0 to indicate send to all subscribers who are registered
# publisherDefinedData		Any data the publisher chooses to include with the event (for example, if it
# 								is an indigo command event, we might include the whole indigo command record here)
# timestamp					The time (in seconds) the event is being published/distributed
#
def distributeEvents(thePublisher, theEvents, theSubscriber, publisherDefinedData):

	global eventPublishers

	#mmLib_Log.logForce("Publisher " + str(thePublisher) + "\'s event list: " + str(theEvents))

	for theEvent in theEvents:
		#mmLib_Log.logForce("    Distributing Event: " + str(theEvent))
		if theSubscriber:
			# load a deque with a single entry (no searching necessary) just go to deque the single handlerInfo entry
			theQueue = targettedEvents.get(thePublisher + "." + theEvent + "." + theSubscriber, 0)
		else:
			try:
				theQueue = eventPublishers[thePublisher][theEvent]
			except:
				mmLib_Log.logForce("#### Debugging Info... There were no subscibers for Event: " + str(theEvent) + ", initiating from Device: "+ thePublisher + ".")
				theQueue = 0

		if not theQueue or len(theQueue) == 0:
			#mmLib_Log.logWarning("      No registrations for event \'" + theEvent + "\'.")
			continue

		publisherDefinedData['theEvent'] = theEvent
		publisherDefinedData['publisher'] = thePublisher
		publisherDefinedData['timestamp'] = time.mktime(time.localtime())

		for aSubscriber, theHandler, handlerDefinedData in theQueue:
			#mmLib_Log.logForce("         Distributing Event: " + str(theEvent) + " to " + str(aSubscriber))
			# note that if a single subscriber was specified to be delivered to, the queue only has entries relevant to that subscriber (hopefully a single entry, for performance)
			# if (theSubscriber == 0) or (theSubscriber == aSubscriber): # Removed this because its unnecessary as per the note above
			# Add event, timestamp, and publisher
			eventParameters = publisherDefinedData
			eventParameters.update(handlerDefinedData)
			try:
				theHandler(theEvent, eventParameters)
			except:
				mmLib_Log.logError("Publisher " + str(thePublisher) + ". Distribution failure for event " + str(theEvent) + " to " + str(aSubscriber))
				pass

	return (0)

#
#
#	deliverFilteredEvents
#
#		This routine augments the Event delivery mechanism (publish/subscribe) at mmLib_Events.py. Clients that want to receive Indigo device update events
#		will subscribe to events of type 'AttributeUpdate' by publisher 'Indigo' similar to the line below:
#
#			mmLib_Events.subscribeToEvents(['AttributeUpdate'], ['Indigo'], self.deviceUpdatedEvent, {'monitoredAttributes': {'onState': 0}}, self.deviceName)
#
#		The purpose of this routine is to give the client more granular evaluatioin of update events from Indigo by comparing the before and after values of
#		the indigo device. Only events that have differences in the indigo device variables notated in the 'monitoredAttributes' field will be delivered
#		to the mmdevice handler. In the above example, 	the mmDevice subscriber will have its self.deviceUpdatedEvent called each time the associated indigo object
#		experiences a change in its onState value. Notice the {'onState': 0} section of the command above... the 0 indicates that the default event handler
#		self.deviceUpdatedEvent will be used for the delivery, however, you have the option of putting any handler you wish in this area in case you have a special
#		need for a specific variable change event that overrides the default handler self.deviceUpdatedEvent.
#		For example if you specify {'batteryLevel': self.BatteryLevelChanged}, your self.BatteryLevelChanged function will be called each time the battery
#		level changes in your device.
#
#		Note this routine is a service provided by the mm System and this routine is called by plugin.deviceUpdated. You should not need to call this function.
#
#
#	Parameter Description
#
#		object1					The object that changed (in its previous state). Usually an Indigo Device Object for the purposes of MM.
#		object2					The object that changed (in its new state). Usually an Indigo Device Object for the purposes of MM.
#		theSubscriber			The name of the mm device subscriber to this event
#
#	Other parameters set up at subscription time (accessed internally via subscription queue))
#
#		monitoredAttributes 	contains a dict that contains the names of the object values that are being monitored and
# 								proc pointers to be called when those values have indeed changed.
#								This is passed in to subscribeToEvents as described above
#		defaultAttributeUpdateHandler		A default handler for any monitoredAttributes with Null (0) handlers
#
def deliverFilteredEvents(object1, object2, theSubscriber):

	theQueue = targettedEvents.get("Indigo.AttributeUpdate." + theSubscriber, 0)

	if not theQueue or len(theQueue) == 0:
		# mmLib_Log.logWarning("Publisher \'Indigo\' is trying to deliver a \'AttributeUpdate\' event to unregistered subscriber " + theSubscriber + ".")
		return (0)

	aSubscriber, defaultAttributeUpdateHandler, handlerDefinedData = theQueue[0]
	monitoredAttributes = handlerDefinedData.get('monitoredAttributes', {})
	if monitoredAttributes == {}:
		mmLib_Log.logWarning("No monitoredAttributes Sub events declared for " + theSubscriber + ".  Queue Entry: " + str(theQueue[0]))
		return (0)

	#		monitoredAttributes 			contains a dict where keyNames is an attribute name from above object that indexes to event
	# 										handlers (proc pointers) in the associated value field
	#										This is passed in to subscribeToEvents as described above
	#		defaultAttributeUpdateHandler	Default handler for all requested events listed in monitoredAttributes with Null (0) handlers

	defaultAttributeUpdateHandlerDict = {}
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
				# A special handler for this particular event was requested at subscribeToEvents() time. 
				# Pass the name of the changed field and its new value to the requested handler
				# we will deliver all these "special" events one at a time inside the evaluation loop
				try:
					# Populate the changed value in teh event record
					eventParameters = publisherDefinedData
					eventParameters['theEvent'] = whichVal	# theEvent is the changed variable name
					eventParameters['whichVal'] = val2		# whichVal is the new value for that variable
					monitoredAttributes[whichVal](whichVal, eventParameters)	# Call the specialized handler
					# and mark the events delivered
					deliveredEventsDict[whichVal] = val2
				except:
					pass
					# message about undeliverable event
					mmLib_Log.logWarning("Event Delivery Failure. Event Type \'" + whichVal + "\' failed to be delivered to " + theSubscriber + ".")
			else:
				# No special handler for this particular event was requested at subscribeToEvents time. Use the default event handler Declared in 
				defaultAttributeUpdateHandlerDict[whichVal] = val2		# commemorate the variable difference for delivery below (after the loop)

	# now on to the remaining changes that need to be delivered (that were not processed by special handlers above)
	# Deliver events to defaultAttributeUpdateHandler as necessary. This is outside the for loop so all object1/object2 variable
	# changes will get delivered in one call to the defaultAttributeUpdateHandler and will include the defaultAttributeUpdateHandlerDict that was built above
	
	if defaultAttributeUpdateHandlerDict != {}:
		if defaultAttributeUpdateHandler:
			try:
				eventParameters = publisherDefinedData
				eventParameters['theEvent'] = 'AttributeUpdate'
				eventParameters.update(defaultAttributeUpdateHandlerDict)
				defaultAttributeUpdateHandler('AttributeUpdate', eventParameters)
				# and mark the events delivered
				deliveredEventsDict.update(defaultAttributeUpdateHandlerDict)	# All changed attributes get populated here
			except Exception as exception:
				mmLib_Log.logWarning( "Event Delivery Failure #1. Event Type \'defaultAttributeUpdateHandlerDict\': " + str(defaultAttributeUpdateHandlerDict) + ". ")
				mmLib_Log.logWarning( "Event Delivery Failure. Event Type \'AttributeUpdate\' failed to be delivered to " + theSubscriber + ". Exception: " + str(exception))
				pass
		else:
			# message that we have events targetted for master, but no master handler
			pass
			mmLib_Log.logWarning( "Event Delivery Failure. Event Type \'AttributeUpdate\' failed to be delivered to " + theSubscriber + ". No MasterEventHandler")

	return deliveredEventsDict

