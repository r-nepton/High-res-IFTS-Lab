# The ControlController is the controller which controls the control panel. 
class @ControlController
	constructor: (@dom_element) ->
		$('.log').append @dom_element

		# Set up the style of the element.
		@dom_element.html """
			<div class='regionbox'>
				<h1 class='regiontitle'>settings</h1>
				<div class='horizontal-field'>
					<div class='field regulation-temperature'><div class='slider'></div></div>
					<span>log data?</span>
				</div>
			</div>

			<div class='regionbox'>
				<h1 class='regiontitle'>cycle</h1>
				<div class='horizontal-field'>
					<div class='field cycle-time'><input type=text /><span class='units'>hours</span></div>
					<span>hold time</span>
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

		@log_data_slider = new UIToggleSlider @dom_element.find('.slider'), (state) =>
			@set_log_data(state)

		@update_log_data_state()
		@update_cycle_parameters()

		setInterval =>
		 	@update_log_data_state()
		 	@update_cycle_parameters()
		 , 30000

	set_log_data: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'set_data_logging_state', arguments: { state: state, password: password } }, (r) =>
				@update_log_data_state()

	# This function queries for the current log data state.
	update_log_data_state: -> 
		pycon.transaction { action: 'get_data_logging_state' }, (r) =>
			@log_data_slider.set_state( r.state )

	update_cycle_parameters: ->
		pycon.transaction { action: 'cycle_settings' }, (r) =>
			@set_cycle_time r.hold_time/3600
			@set_regulation_temperature r.regulation_temperature*1000

	get_cycle_time: ->
		$('.cycle-time').children('input').val()

	set_cycle_time: (value) ->
		$('.cycle-time').children('input').val value

	get_regulation_temperature: ->
		$('.regulation-temperature').children('input').val()

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
			hold_time = @get_cycle_time()*3600 # need to provide it in seconds.
			pycon.transaction { action: 'cycle_settings', arguments: { password: password, hold_time: hold_time } }, (r) =>
				@update_cycle_parameters()
	cycle_begin: ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: "begin_magnetization_cycle", arguments: { password: password } }

	update: ->
		yes
