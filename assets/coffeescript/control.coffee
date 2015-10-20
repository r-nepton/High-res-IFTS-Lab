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
