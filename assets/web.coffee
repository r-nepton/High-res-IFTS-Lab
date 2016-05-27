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
# This controller handles the user interface of authentication. It presents
# the user with a password prompt, and calls a callback when the password
# has been selected.
class AuthenticationController
	constructor: (@dom_element) ->
		$('body').append @dom_element.hide()
		@dom_element.html """
			<div class='authentication-overlay'>
				<div class='authentication-dialog'>
					<h1>Enter the password.</h1>
					<input type=password class='password' />
				</div>
			</div>
		"""

		@callback = ->
			yes

		$('.password').keypress (e) =>
			if e.which == 13
				@submit()

	get_password: ->
		$('.password').val()

	submit: ->
		@hide()
		@callback( @get_password().toUpperCase() )

	show: ->
		$('.password').val('')
		$('.authentication-overlay').css {height: screen.height}
		@dom_element.show()
		$('.password').focus()

	hide: ->
		@dom_element.hide()

	begin: (callback) ->
		@show()
		@callback = callback
# The ControlController is the controller which controls the control panel. 
class @ControlController
	constructor: (@dom_element) ->
		$('.log').append @dom_element

		# Set up the style of the element.
		@dom_element.html """
			<div class='regionbox'>
				<h1 class='regiontitle'>settings</h1>
				<div class='horizontal-field'>
					<div class='field log-data'><div class='slider'></div></div>
					<span>log data?</span>
				</div>

				<div class='horizontal-field'>
					<div class='menubutton close-heatswitch' style="background-color: rgb(250, 42, 0); color: white;">close</div>
					<div class='menubutton open-heatswitch' style=" background-color: rgb(170,185,93); color: white;">open</div>
					<span>heat switch</span>
				</div>

				<div class='menubutton emergency-stop' style="background-color: black; color: white;">emergency stop</div>
				<div class="buttonspacer"></div>
			</div>

			<div class='regionbox'>
				<h1 class='regiontitle'>cycle</h1>

				<div class='horizontal-field'>
					<div class='field rampup-time'><input type=text /><span class='units'>minutes</span></div>
					<span>ramp-up time</span>
				</div>

				<div class='horizontal-field'>
					<div class='field cycle-current'><input type=text /><span class='units'>amps</span></div>
					<span>hold current</span>
				</div>

				<div class='horizontal-field'>
					<div class='field cycle-time'><input type=text /><span class='units'>hours  </span></div>
					<span>hold time</span>
				</div>

				<div class='horizontal-field'>
					<div class='field rampdown-time'><input type=text /><span class='units'>minutes</span></div>
					<span>ramp-down time</span>
				</div>

				<div class='menubutton cycle-save' style="background-color: black; color: white;">save</div>
				<div class='menubutton cycle-begin' style=" background-color: rgb(250, 42, 0); color: white;">cycle</div>
				

				<div class="buttonspacer"></div>
			</div>

			<div class='regionbox'>
				<h1 class='regiontitle'>regulation</h1>
				<div class='horizontal-field'>
					<div class='field regulation-temperature'><input type=text /><span class='units'>mK</span></div>
					<span>regulation temperature</span>
				</div>
				<div class='menubutton regulate-save' style="background-color: black; color: white;">save</div>
				<div class="buttonspacer"></div>
			</div>
		"""
		# Now setup callbacks for all of the various buttons.
		$('.regulate-save').click =>
			@regulate_save()

		$('.cycle-save').click =>
			@cycle_save()

		$('.cycle-begin').click =>
			@cycle_begin()

		$('.emergency-stop').click =>
			@emergency_stop()

		$('.open-heatswitch').click =>
			@open_heatswitch()

		$('.close-heatswitch').click =>
			@close_heatswitch()

		$('.manual-switch-to-regulate-mode').click =>
			@switch_to_regulate_mode()

		$('.switch_to_mag_cycle_mode').click =>
			@switch_to_mag_cycle_mode()

		@log_data_slider = new UIToggleSlider @dom_element.find('.slider'), (state) =>
			@set_log_data(state)

		@update_log_data_state()
		@update_cycle_parameters()

		setInterval =>
		 	@update_log_data_state()
		 	@update_cycle_parameters()
		 , 30000

	emergency_stop: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'emergency_stop', arguments: { password: password } }

	set_log_data: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'set_data_logging_state', arguments: { state: state, password: password } }, (r) =>
				@update_log_data_state()

	open_heatswitch: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'open_heatswitch', arguments: { password: password } }

	close_heatswitch: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'close_heatswitch', arguments: { password: password } }

	switch_to_regulate_mode: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'switch_to_regulate_mode', arguments: { password: password } }

	switch_to_mag_cycle_mode: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'switch_to_mag_cycle_mode', arguments: { password: password } }

	# This function queries for the current log data state.
	update_log_data_state: -> 
		pycon.transaction { action: 'get_data_logging_state' }, (r) =>
			@log_data_slider.set_state( r.state )

	update_cycle_parameters: ->
		pycon.transaction { action: 'cycle_settings' }, (r) =>
			@set_cycle_time r.hold_time/3600 #Display time in hours
			@set_cycle_current r.hold_current
			@set_ramp_up_time r.ramp_up_time/60 #Display time in minutes
			@set_ramp_down_time r.ramp_down_time/60 #Display time in minutes
			@set_regulation_temperature r.regulation_temperature*1000 #Display temperature in mK

	get_cycle_time: ->
		$('.cycle-time').children('input').val()

	get_cycle_current: ->
		$('.cycle-current').children('input').val()

	get_ramp_up_time: ->
		$('.rampup-time').children('input').val()

	get_ramp_down_time: ->
		$('.rampdown-time').children('input').val()

	get_regulation_temperature: ->
		$('.regulation-temperature').children('input').val()

	set_cycle_time: (value) ->
		$('.cycle-time').children('input').val value

	set_cycle_current: (value) ->
		$('.cycle-current').children('input').val value

	set_ramp_up_time: (value) ->
		$('.rampup-time').children('input').val value

	set_ramp_down_time: (value) ->
		$('.rampdown-time').children('input').val value

	set_regulation_temperature: (value) ->
		$('.regulation-temperature').children('input').val value

	regulate_save: ->
		authentication_controller.begin (password) =>
			regulation_temperature = @get_regulation_temperature() / 1000 # need to provide it in kelvin.
			pycon.transaction { action: 'cycle_settings', arguments: { password: password, regulation_temperature: regulation_temperature } }, (r) =>
				console.log r
				@update_cycle_parameters()

	cycle_save: ->
		authentication_controller.begin (password) =>
			#Until back emf can be monitored, restrict ramp up time to more then 20 minutes
			ramp_up_time = @get_ramp_up_time()*60 # need to provide it in seconds
			if ramp_up_time < 20*60
				ramp_up_time = 20*60			

			#Magnet current must be kept below 18amps
			hold_current = @get_cycle_current()
			if hold_current > 18
				hold_current = 18

			hold_time = @get_cycle_time()*3600 # need to provide it in seconds.

			#Until back emf can be monitored, restrict ramp down time to more then 20 minutes
			ramp_down_time = @get_ramp_down_time()*60 # need to provide it in seconds
			if ramp_down_time < 20*60
				ramp_down_time = 20*60

			pycon.transaction { action: 'cycle_settings', arguments: { password: password, ramp_up_time: ramp_up_time, hold_time: hold_time, hold_current: hold_current, ramp_down_time: ramp_down_time } }, (r) =>
				@update_cycle_parameters()
	cycle_begin: ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: "begin_magnetization_cycle", arguments: { password: password } }

	update: ->
		yes
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
			window.jevents[eventName] = [ eventAction ]class @ScatterPlot
	constructor: (@title, @element) ->
		@x = []
		@xtitle = "X"
		@y = []
		@ytitle = "Y"
		@options = { 
			title: @title, 
			legend: 'none',
			lineWidth: 1,
			hAxis: { title: @xtitle },
			vAxis: { title: @ytitle } 
		}

	plot: (x = @x, y = @y) ->
		@x = x; @y = y;
		# Only draw the plot if it's worth drawing.
		if !$('.graphs').is(':visible') or x.length == 0
			return

		drawChart = =>
			console.log "drawing chart..."
			table = []
			table.push [@xtitle, @ytitle]
			for i in [0..@x.length]
				table.push [ @x[i], @y[i] ]
			data = google.visualization.arrayToDataTable table

			xmax = Math.max.apply(Math, @x)
			xmin = Math.min.apply(Math, @x)
			xrange = xmax - xmin

			ymax = Math.max.apply(Math, @y)
			ymin = Math.min.apply(Math, @y)
			yrange = ymax - ymin

			@options.hAxis.title = @xtitle
			@options.vAxis.title = @ytitle
			@options.enableInteractivity = false

			@options.hAxis.minValue = xmin
			@options.hAxis.maxValue = xmax
			@options.vAxis.minValue = ymin
			@options.vAxis.maxValue = ymax

			chart = new google.visualization.ScatterChart(@element.get(0));
			chart.draw(data, @options)

		drawChart()

class @TemperaturePlot
	constructor: ->
		element = $('<div id="temperature_plot" style="width: 650px; height: 250px;"></div>')
		element.appendTo('.graphs')
		@t = new ScatterPlot("FAA Temperature", element)
		@update()
		# Set a timer to constantly update the plot.
		setInterval( => 
			@update()
		, 15000)

	update: ->
		# Request historical data from the server.
		pycon.transaction { action: "sensor", arguments: {'sensor':'FAA_temperature','number':50} }, (r) =>
			@t.xtitle = "Time [minutes from now]"
			@t.ytitle = "Temperature [mK]"	
			@t.y = ( d.data.temperature*1000 for d in r.history )
			@t.x = ( Math.min(0,(d.time - Date.now()/1000)/60) for d in r.history )
			@t.plot()

class @TemperaturePlot2
	constructor: ->
		element = $('<div id="temperature_plot" style="width: 650px; height: 250px;"></div>')
		element.appendTo('.graphs')
		@t = new ScatterPlot("Pulse Tube Stage #2 Temperature", element)
		@update()
		# Set a timer to constantly update the plot.
		setInterval( => 
			@update()
		, 15000)

	update: ->
		# Request historical data from the server.
		pycon.transaction { action: "sensor", arguments: {'sensor':'pulse_tube_second_stage', 'number':50} }, (r) =>
			@t.xtitle = "Time [minutes from now]"
			@t.ytitle = "Temperature [Kelvin]"	
			#Multiplying the temperature by 1 prevents the plot from failing if the datapoint is a string "unknown" 
			@t.y = ( d.data.temperature*1 for d in r.history )
			@t.x = ( Math.min(0,(d.time - Date.now()/1000)/60) for d in r.history )
			@t.plot()

class @PressurePlot
	constructor: ->
		@element = $('<div id="pressure_plot" style="width: 650px; height: 250px;"></div>')
		@element.appendTo('.graphs')
		@t = new ScatterPlot("Pressure", @element)
		@t.options.vAxis.format = '0.00E+0'
		@update() 
		# Set a timer to constantly update the plot.
		setInterval( => 
			@update()
		, 15000)

	update: ->
		# Request historical data from the server.
		pycon.transaction { action: "pressure", arguments: {'number':50} }, (r) =>
			@t.xtitle = "Time [minutes from now]"
			@t.ytitle = "Pressure [T]"	
			console.log "Received pressure update: ", r
			# Check results for errors.
			if r.history[0].data.error?
				@element.hide()
				return
			@t.y = ( d.data.pressure for d in r.history )
			
			@t.x = ( Math.min(0,(d.time - Date.now()/1000)/60) for d in r.history )
			@t.plot()

class @CurrentPlot
	constructor: ->
		@element = $('<div id="current_plot" style="width: 650px; height: 250px;"></div>')
		@element.appendTo('.graphs')
		@t = new ScatterPlot("Magnet Current", @element)
		@update() 
		# Set a timer to constantly update the plot.
		setInterval( => 
			@update()
		, 15000)

	update: ->
		# Request historical data from the server.
		pycon.transaction { action: "magnet_current", arguments: {'number':50} }, (r) =>
			@t.xtitle = "Time [minutes from now]"
			@t.ytitle = "Magnet Current [A]"	
			console.log "Received current update: ", r
			# Check results for errors.
			if r.history[0].data.error?
				@element.hide()
				return
			@t.y = ( (d.data.current) for d in r.history )
			
			@t.x = ( Math.min(0,(d.time - Date.now()/1000)/60) for d in r.history )
			@t.plot()

class @BackEmfPlot
	constructor: ->
		@element = $('<div id="current_plot" style="width: 650px; height: 250px;"></div>')
		@element.appendTo('.graphs')
		@t = new ScatterPlot("Magnet Back EMF", @element)
		@update() 
		# Set a timer to constantly update the plot.
		setInterval( => 
			@update()
		, 15000)

	update: ->
		# Request historical data from the server.
		pycon.transaction { action: "magnet_back_emf", arguments: {'number':50} }, (r) =>
			@t.xtitle = "Time [minutes from now]"
			@t.ytitle = "EMF [mV]"	
			console.log "Received current update: ", r
			# Check results for errors.
			if r.history[0].data.error?
				@element.hide()
				return
			@t.y = ( (d.data.voltage)*1000 for d in r.history )
			
			@t.x = ( Math.min(0,(d.time - Date.now()/1000)/60) for d in r.history )
			@t.plot()

class @Dashboard
	constructor: ->
		@element = $('<div id="dashboard"></div>')
		@element.appendTo('.log')
		@dashboardelements = []
		# Insert latest log item
		@latest_log = new LogElement()
		@latest_log.dom_element.appendTo @element
		# Insert temperature dashboard element.
		@dashboardelements.push new TemperatureFAADashboardElement()
		@dashboardelements.push new Temperature3KDashboardElement()
		@dashboardelements.push new Temperature50KDashboardElement()
		@dashboardelements.push new PressureDashboardElement()
		@dashboardelements.push new MagnetCurrentDashboardElement()
		@dashboardelements.push new MagnetBackEmfDashboardElement()
		@dashboardelements.push new UPSDashboardElement()
		@dashboardelements.push new WaterTemperatureDashboardElement()
		@dashboardelements.push new OilTemperatureDashboardElement()

		setInterval( => 
			@update_latest_log()
		, 30000)

		@update_latest_log()

		for d in @dashboardelements
			d.element.appendTo @element

	update_latest_log: ->
		pycon.transaction { action: "user_log" }, (r) =>
			@latest_log.message = r.data
			@latest_log.timestamp = r.time
			@latest_log.render()
		

class @DashboardElement
	constructor: ->
		@element = $('<div class="dashboard-element"></div>')
		@symbol = "T"
		@value = "195 K"
		@state_ok 	= yes
		@update()
		setInterval( => 
			@update()
		, 15000)

	render: ->
		string = "<div class='left'>#{@symbol}</div>"
		if @state_ok
			string +="<div class='right'>#{@value}</div>"
		else
			string +="<div class='right'>N/A</div>"
		@element.html string
	update: ->
		yes

class @Temperature3KDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol = "T<sub>3K</sub>"
		@element.addClass('h2o')
		@value 	= "U"

	update: ->
		pycon.transaction { action: "temperature" }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				if r.data.temperature < 1
					@value = (r.data.temperature*1000).toPrecision(3) + " mK"
				else
					@value = (r.data.temperature).toPrecision(3) + " K"
			@render()

class @Temperature50KDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol = "T<sub>50K</sub>"
		@element.addClass('h2o')
		@value 	= "U"

	update: ->
		pycon.transaction { action: "temperature_2" }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				if r.data.temperature < 1
					@value = (r.data.temperature*1000).toPrecision(3) + " mK"
				else
					@value = (r.data.temperature).toPrecision(3) + " K"
			@render()

class @TemperatureFAADashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol = "T<sub>FAA</sub>"
		@element.addClass('h2o')
		@value 	= "U"

	update: ->
		pycon.transaction { action: "sensor", arguments: { sensor: "FAA_temperature" } }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				if r.data.temperature < 1
					@value = (r.data.temperature*1000).toPrecision(3) + " mK"
				else
					@value = (r.data.temperature).toPrecision(3) + " K"
			@render()

class @PressureDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol 	= "P"
		@value 		= "U"

	update: ->
		pycon.transaction { action: "pressure" }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				@value = (r.data.pressure).toExponential(1) + " T"
			@render()

class @WaterTemperatureDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol 	= "H<sub>2</sub>O"
		@value 		= "U"
		# H2O is a long word, so we'll reduce the font size
		@element.addClass('h2o')

	update: ->
		pycon.transaction { action: "sensor", arguments: {'sensor':'compressor'} }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				@value = "#{r.data.inlet_temperature} &deg;C"
			@render()

class @OilTemperatureDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol 	= "Oil"
		@value 		= "U"
		# H2O is a long word, so we'll reduce the font size
		@element.addClass('h2o')

	update: ->
		pycon.transaction { action: "sensor", arguments: {'sensor':'compressor'} }, (r) =>
			# Now try to format the number appropriately.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				@value = "#{r.data.oil_temperature} &deg;C"
			@render()

class @MagnetCurrentDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol 	= "I<sub>M</sub>"
		@value 		= "U"
		# H2O is a long word, so we'll reduce the font size
		@element.addClass('h2o')

	update: ->
		pycon.transaction { action: "sensor", arguments: {'sensor':'magnet_current'} }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				if r.data.current < 0.001
					@value = "#{(r.data.current*1000).toFixed(2)} mA"
				else if r.data.current < 0.1
					@value = "#{(r.data.current*1000).toFixed(1)} mA"
				else if r.data.current < 1
					@value = "#{r.data.current.toFixed(2)} A"
				else 
					@value = "#{r.data.current.toFixed(1)} A"

			@render()

class @MagnetBackEmfDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol		= "EMF"
		@value		= "U"
		@element.addClass('h2o')

	update: ->
		pycon.transaction { action: "sensor", arguments: {'sensor':'magnet_back_emf'} }, (r) =>
			# Now try to format the number appropriately.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				if r.data.voltage < 0.001
					@value = "#{(r.data.voltage*1000).toFixed(2)} mV"
				else if r.data.voltage < 0.1
					@value = "#{(r.data.voltage*1000).toFixed(1)} mV"
				else if r.data.voltage < 1
					@value = "#{r.data.voltage.toFixed(2)} V"
				else
					@value = "#{r.data.voltage.toFixed(1)} V"

			@render()
		

class @UPSDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol 	= "UPS"
		@value 		= "?"
		@element.addClass('h2o')

	update: ->
		pycon.transaction { action: "sensor", arguments: {'sensor':'ups'} }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			if r.data.error?
				@state_ok = no
			else
				@state_ok = yes
				@value = "#{(r.data.battery_capacity)}%"
				if r.data.line_power == no
					@element.addClass('warn')
				else
					@element.removeClass('warn')


			@render()
class @MenuButton
	constructor: ->
		if !@text? 
			@text = "Generic Menu Button"
		if !@background_color?
			@background_color = "#000000"
		if !@text_color?
			@text_color = "#FFFFFF"
		@element = $("<div class='menubutton'></div>")
		@element.on('click', @action)
		@element.on('tap', @action)
		@element.appendTo $('.menu')
		@render()

	action: ->
		yes

	render: ->
		@element.css('background-color', @background_color)
		@element.css('color', @text_color)
		@element.html @text

class @OverviewMenuButton extends MenuButton
	constructor: ->
		@text = "overview"
		super()

	action: ->
		$('.graphs').hide()
		$('.logs').hide()
		$('#dashboard').show()
		$('.report').hide()
		$('.control').hide()

class @GraphsMenuButton extends MenuButton
	constructor: ->
		@text = "graphs"
		@background_color = "#3366cc"
		super()

	action: ->
		$('.graphs').show()
		for g in window.graphs
			g.t.plot()
		$('#dashboard').hide()
		$('.logs').hide()
		$('.report').hide()
		$('.control').hide()

class @LogMenuButton extends MenuButton
	constructor: ->
		@text = "log"
		@background_color = "#AAB95D"
		super()

	action: ->
		$('.logs').show()
		$('#dashboard').hide()
		$('.graphs').hide()
		$('.report').hide()
		$('.control').hide()

		window.logs_controller.focus()

class @ReportMenuButton extends MenuButton
	constructor: ->
		@text = "report"
		@background_color = "#FA2A00"
		super()

	action: ->
		$('.logs').hide()
		$('#dashboard').hide()
		$('.graphs').hide()
		$('.report').show()
		$('.control').hide()

class @ControlMenuButton extends MenuButton
	constructor: ->
		@text = "control"
		@background_color = "#FA2A00"
		super()

	action: ->
		$('.logs').hide()
		$('#dashboard').hide()
		$('.graphs').hide()
		$('.control').show()

class @UIToggleSlider
	# The UI slider is a yes/no toggle slider/
	constructor: (@dom_element, @state_change_callback) ->
		@dom_element.html """<div class='slider-state'></div><div class='spacer'>&nbsp;</div>"""
		@state = false
		@dom_element.click =>
			@state_change_callback !@get_state()
		@set_state no

	set_state: (state) ->
		if state == no
			@dom_element.children('.slider-state').css("float",'left').css('background-color','gray').html "no"
			@state = no
		else
			@dom_element.children('.slider-state').css("float",'right').css('background-color','rgb(170, 185, 93)').html "yes"
			@state = yes

	toggle_state: ->
		@set_state !@state

	get_state: ->
		@statewindow.log = (text) ->
	t = marked.parse text
	$('.log').append tclass @LogsController
	constructor: (@dom_element) ->
		# Add our DOM element to the page.
		$('.log').append @dom_element
		# Create the interface for the logs.
		@textbox = $("<input type=text class=log_textbox />")
		@textbox.keydown (e) =>
			if e.keyCode == 13
				e.preventDefault()
				@submit()

		@dom_element.append @textbox
		@dom_element.append $("<p></p>")

		@latest_log = new LogElement()
		@dom_element.append @latest_log.dom_element

		@past_logs_list = $("<div class='past_logs_list'></div>").hide()
		@dom_element.append @past_logs_list

		@update()

		setInterval( => 
			@update()
		, 30000)

	focus: ->
		@textbox.focus()

	submit: ->
		# Detect if the box is just whitespace.
		if $.trim(@textbox.val()).length > 0
			pycon.transaction { action: "write_log", arguments: { 'log': @textbox.val() }}, =>
				# Update the panel
				@update()
				# Clear out the textbox
				@textbox.val('')

	update: ->
		pycon.transaction { action: "user_log", arguments: {'number':5} }, (r) =>
			console.log "Received update:", r
			if r.history.length >= 1
				@latest_log.message = r.history[0].data
				@latest_log.timestamp = r.history[0].time
				@latest_log.render()
			else
				@latest_log.message = "There are no logs yet!"
				@latest_log.timestamp = 0
				@latest_log.render()

			# Clear out the old list of logs.
			@past_logs_list.html ""
			@past_logs_list.append $("<p>&nbsp;</p>")
			for h in r.history[1..]
				f = new LogElement()
				f.message = h.data
				f.timestamp = h.time
				@past_logs_list.append f.dom_element
				f.render()

			if r.history.length > 1
				@past_logs_list.show()



# The log element is a visual representation of a log.
class @LogElement
	@basic_element: ->
		return $("<div class='log_element'></div>")

	constructor: (@dom_element) ->
		if !@dom_element? 
			@dom_element = LogElement.basic_element()
		@dom_message = $("<div class='log_element_message'></div>")
		@dom_timestamp = $("<div class='log_element_timestamp'></div>")

		# Default values.
		@message = ""
		@timestamp = 0

		@dom_element.append @dom_timestamp
		@dom_element.append @dom_message

	format_time: ->
		
		sdt = (new Date().getTime())/1000 - @timestamp
		dt = Math.abs(sdt)

		#If the log was created more then an hour ago, we just want a plain timestamp
		if dt >= 60*60

			date_ob = new Date(@timestamp*1000)
			time_string_options = {
				timezone: "UTC", month: "short", day: "numeric", 
				hour: "2-digit", hour12: false, minute: "2-digit", second: "2-digit"}
			datestamp = date_ob.toLocaleString('en-US',time_string_options)

			log_time = "#{datestamp}"

		else

			units = switch
				when dt < 60 				then { unit: 'second', 	amount: 1}
				when dt < 60*60 			then { unit: 'minute', 	amount: 60}

			if sdt > 0
				postfix = "ago"
			else
				postfix = "from now"

			quantity = Math.ceil(dt / units.amount)

			if quantity > 1
				unit_postfix = "s"
			else
				unit_postfix = ""

			log_time = "#{quantity} #{units.unit}#{unit_postfix} #{postfix}"

		#The 0th log doesn't need a timestamp
		if @timestamp == 0
			log_time = ""

		return log_time

	render: ->
		@dom_message.html @message
		@dom_timestamp.html @format_time()
# Configuration parameters:
# -------------------------------------- #
window.config = []
window.config.websocket_url = "ws://#{window.location.host}/json"
window.config.server_version = "0.1"
# -------------------------------------- #

$ ->
	# First step: connect to the specified WebSocket
	# server.
	# Start the log file.
	window.retryinterval = null
	log "#cryo-server"
	window.socket = new WebSocket( window.config.websocket_url )
	# Get ready for when the socket opens
	window.jevent 'SocketOpened', ->
	console.log 'The socket was opened.'
	# This function is called only when the socket is opened. 
	socket.onopen = ->
		console.log "Socket connection opened successfully."
		window.pycon = new PyAPI window.socket
		setTimeout window.connection_ready, 200

	# Since the socket should never close, this is always unexpected.
	socket.onclose = =>
		retryinterval = setInterval(=>
			try 
				console.log "Trying to connect again..."
				window.socket = new WebSocket( window.config.websocket_url )
				retryinterval = null
			catch e
				yes
		,120)

window.connection_ready = ->
	console.log "Window ready."
	# Create the menu region
	$('.log').append $('<div class="menu"></div>')
	window.overview_button = new OverviewMenuButton()
	window.graphs_button = new GraphsMenuButton()
	window.log_button = new LogMenuButton()
	window.control_button = new ControlMenuButton()
	#window.log_button = new ReportMenuButton()
	# Create the dashboard elements.
	window.dashboard = new Dashboard()
	# Create the graphs.
	$('.log').append('<div class="graphs"></div>')
	$('.graphs').hide()
	window.graphs = []
	window.graphs.push new TemperaturePlot2()
	window.graphs.push new TemperaturePlot()
	window.graphs.push new PressurePlot()
	window.graphs.push new CurrentPlot()
	window.graphs.push new BackEmfPlot()

	# Create the logs.
	window.logs_controller = new LogsController( $('<div class="logs"></div>').hide() )

	# Create the report.
	#window.report_controller = new ReportController()

	# Create the authentication controller.
	window.authentication_controller = new AuthenticationController( $('<div class="authentication"></div>') )

	# Create the control panel.
	window.control_controller = new ControlController $("<div class='control'></div>").hide()
# The ReportController controls the report tab.
class @ReportController
	constructor: ->
		@dom_element = $("<div class='report'></div>").hide()
		$('.log').append @dom_element
		@dom_element.append $("<div id='visualization'></div>")
		@dom_element.append $("<div id='control'></div>")

		google.setOnLoadCallback =>
			@ready

	ready: ->
		debugger;
		console.log "I'm going to draw the report."
		@dashboard = new google.visualization.Dashboard @dom_element[0]

		@control = new google.visualization.ControlWrapper {
			controlType: 'ChartRangeFilter',
			containerId: 'control',
			options: {
				filterColumnIndex: 0,
				ui: {
					chartType: 'LineChart',
					chartOptions: { width: '90%' }
					hAxis: { 'baselineColor': 'none' }
				},
				chartView: {
					columns: [0, 1]
				}
				minRangeSize: 86400
			}
		}, {
			state: {
				range: {
					start: -10000, 
					end: 0
				}
			}
		}

		@chart = new google.visualization.ChartWrapper {
			chartType: 'ScatterChart',
			dataTable: [["test", "test"],[700, 800]],
			options: { title: 'Countries' },
			containerId: 'visualization'
		}

		@dashboard.bind @control, @chart
		@chart.draw()
		@dashboard.draw google.visualization.arrayToDataTable [["test", "test"],[700, 800],[600, 700],[500, 600]]