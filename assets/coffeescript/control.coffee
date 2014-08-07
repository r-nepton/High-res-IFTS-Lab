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
				<div class='menubutton regulate-begin' style="background-color: rgb(51, 102, 204); color: white;">regulate</div>
				<div class="buttonspacer"></div>
			</div>
		"""
		# Now setup callbacks for all of the various buttons.
		$('.regulate-save').click =>
			@regulate_save()

		$('.regulate-begin').click =>
			@regulate_begin()

		$('.cycle-save').click =>
			@cycle_save()

		$('.cycle-begin').click =>
			@cycle_begin()

		@log_data_slider = new UIToggleSlider @dom_element.find('.slider'), (state) =>
			@set_log_data(state)

	set_log_data: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'set_data_logging_state', arguments: { state: state, password: password } }, (r) =>
				if r.success
					@log_data_slider.set_state( state )


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
			console.log "attempted w/ password: ", password
		yes

	regulate_begin: ->
		yes

	cycle_save: ->
		yes

	cycle_begin: ->
		yes

	update: ->
		yes
