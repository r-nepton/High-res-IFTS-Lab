# This class handles communication with the Python
# WebSocket server that is running on the local
# machine, and interfaces communication between the two.

class @PyAPI
	constructor: (@socket = null) ->
		# In case the socket is null, we'll use the
		# globally-accessible socket.
		@socket = window.socket if !@socket?
		@response_handlers = []
		@event_responders = []

		# Connect this PyAPI class to the onmessage
		# event for the socket.
		me = @
		@socket.onmessage = (message) ->
			me.onmessage.call me, message

		# Verify the server version using this method.
		@transaction {action: 'validate_version' }, (response) ->
			console.log "Attempted version validation. Received response:"
			console.log response
			throw "VERSION_ERROR: Invalid reported server version #{response.version}. Expecting #{window.config.server_version}" if response.version != window.config.server_version
			log "v#{response.version} **#{response.git_hash}**, started at #{response.start_date}"
	

	# Register for an event using this function, to hear when the computer
	# tells you something global. But you can't respond to it.
	register_for_event: (eventName, response) ->
		if !@event_responders[eventName]?
			@event_responders[eventName] = []
		@event_responders[eventName].push response 

	# When an event comes in, this function executes all of the listeners.
	trigger_event: (eventName, data={}) ->
		if @event_responders[eventName]?
			for e in @event_responders[eventName]
				# If we are supposed to return their call, this method will do that.
				if data.callback_id? 
					response = e.call(window, data)
				else 
					e.call(window,data)

	# This function is called whenever a message is received
	# by the socket. It checks if the message matches the transaction
	# pattern, and if so, handles it appropriately.
	onmessage: (message) ->
		#window.message = JSON.parse message 
		#if !(typeof yourVariable === 'object')
		# If the mssage has a transaction ID, and there is a callback
		message = JSON.parse message.data
		if message.transaction_id? and @response_handlers[ message.transaction_id ]?
			# Call the response function.
			@response_handlers[ message.transaction_id ].call @, message.data
		else
			console.log 'Received invalid message: ', message

	# This function generates a transaction ID, based upon the current time.
	generate_transaction_id: (message) ->
		# For now, we just use a random number. But this introduces
		# random behavior - it might be better to use a hashing algorithm
		# in the future. Returns a string.
		return "T" + Math.random()

	# This function executes a transaction by transmitting a message, then waiting for 
	# a response, then executing the responder function on the response.
	transaction: (message, responder) ->
		# First, generate a transaction ID that we can use later when 
		# we receive a response from the system. 
		transaction_id = @generate_transaction_id(message)
		# Now register the responder as the next
		# response handler, using the transaction ID 
		if responder? 
			@response_handlers[ transaction_id ] = (response) ->
				responder.call( @, response )

		# Send out the actual data, and wait for the response! (actually this is 
		# asynchronous so we don't wait)
		@socket.send( JSON.stringify { data: message, transaction_id: transaction_id } )

