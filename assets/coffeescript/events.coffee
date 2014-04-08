# This function helps handle global events. Using this 
# global system, you can register for an event and receive
# a notification when it occurs, or you can fire the event. 

window.jevents = []

window.jevent = ( eventName, eventAction = null ) ->
	# If there is no eventAction, then that means
	# we are "triggering" the event.
	if eventAction == null 
		if window.jevents[eventName]?
			# For every registered event, call it.
			f.call for f in window.jevents[eventName]

	else 
		# Now, register the function with the event
		# If there are already registered actions with 
		# that event name, just add to the list.
		if window.jevents[eventName]?
			window.jevents[eventName].push eventAction
		# Otherwise, we'll have to create the list.
		else 
			window.jevents[eventName] = [ eventAction ]