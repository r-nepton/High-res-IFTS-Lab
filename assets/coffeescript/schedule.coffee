# The ScheduleController is the controller which controls the schedule panel. 
class @ScheduleController
	constructor: (@dom_element) ->
		$('.log').append @dom_element

		# Set up the style of the element.
		@dom_element.html """
			<div class='regionbox'>
				<h1 class='regiontitle'>schedule settings</h1>
				<div class='horizontal-field'>
					<div class='field schedule-cycles'><div class='slider'></div></div>
					<span>scheduling on</span>
				</div>

				<div class='horizontal-field'>
					<div class='field weekend-cycles'><div class='slider'></div></div>
					<span>cycle on weekends</span>
				</div>


				<div class='horizontal-field'>
					<div class='field number-days'><input type=text /><span class='units'>days</span></div>
					<span>scheduling duration</span>
				</div>

				<div class='horizontal-field'>
					<div class='field start-time'><input type=text /><span class='units'>HH:MM</span></div>
					<span>start time</span>
				</div>

				<div class='horizontal-field'>
					<div class='field end-time'><input type=text /><span class='units'>HH:MM</span></div>
					<span>end time</span>
				</div>

				<div class='menubutton schedule-save' style="background-color: black; color: white;">save</div>

				<div class="buttonspacer"></div>
			</div>
		"""

		##UP TO HERE ###
		# Now setup callbacks for all of the various buttons.
		$('.schedule-cycles').click =>
			@schedule_cycles()

		$('.weekend-cycles').click =>
			@weekend_cycles()

		$('.number-days').click =>
			@number_days()

		$('.start-time').click =>
			@start_time()

		$('.end-time').click =>
			@end_time()

		$('.schedule-save').click =>
			@schedule_save()


		@schedule_cycles_slider = new UIToggleSlider @dom_element.find('.slider'), (state) =>
			@set_schedule_cycles(state)
		
		@weekend_cycles_slider = new UIToggleSlider @dom_element.find('.slider'), (state) =>
			@set_weekend_cycles(state)

		@update_schedule_cycles_state()
		@update_weekend_cycles_state()
		@update_schedule_parameters()

		setInterval =>
		 	@update_schedule_cycles_state()
		 	@update_weekend_cycles_state()
		 	@update_schedule_parameters()
		 , 30000

	set_schedule_cycles: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'set_cycle_scheduling_state', arguments: { state: state, password: password } }, (r) =>
				@update_schedule_cycles_state()

	set_weekend_cycles: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'set_weekend_cycle_state', arguments: { state: state, password: password } }, (r) =>
				@update_weekend_cycles_state()

	schedule_save: (state) ->
		authentication_controller.begin (password) =>
			pycon.transaction { action: 'cycle_schedule_save', arguments: { password: password } }


	# This function queries for the current schedule cycles state.
	update_schedule_cycles_state: -> 
		pycon.transaction { action: 'get_cycle_scheduling_state' }, (r) =>
			@schedule_cycles_slider.set_state( r.state )


	# This function queries for the current weekend cycles state.
	update_weekend_cycles_state: -> 
		pycon.transaction { action: 'get_weekend_cycle_state' }, (r) =>
			@weekend_cycles_slider.set_state( r.state )


	update_schedule_parameters: ->
		pycon.transaction { action: 'schedule_settings' }, (r) =>
			@set_number_days r.number_days
			@set_start_time r.start_time
			@set_end_time r.end_time

	get_number_days: ->
		$('.number-days').children('input').val()

	get_start_time: ->
		$('.start-time').children('input').val()

	get_end_time: ->
		$('.end-time').children('input').val()

	set_number_days: (value) ->
		$('.number-days').children('input').val value

	set_start_time: (value) ->
		$('.start-time').children('input').val value

	set_end_time: (value) ->
		$('.end-time').children('input').val value


	schedule_save: ->
		authentication_controller.begin (password) =>

			number_days = @get_number_days()
			start_time = @get_start_time()
			end_time = @get_end_time()

			pycon.transaction { action: 'schedule_settings', arguments: { password: password, number_days: number_days, start_time: start_time, end_time: end_time} }, (r) =>
				@update_schedule_parameters()
	
	update: ->
		yes

