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
		@state