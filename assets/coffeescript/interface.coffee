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
		$('#dashboard').show()

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