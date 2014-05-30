class @ScatterPlot
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
		element.appendTo('.log')
		@t = new ScatterPlot("Temperature", element)
		@update()
		# Set a timer to constantly update the plot.
		setInterval( => 
			@update
		, 30000)

	update: ->
		# Request historical data from the server.
		pycon.transaction { action: "temperature", arguments: {'number':50} }, (r) =>
			@t.xtitle = "Time [minutes from now]"
			@t.ytitle = "Temperature [Kelvin]"	
			@t.y = ( d.data.temperature for d in r.history )
			@t.x = ( (d.time - Date.now()/1000)/60 for d in r.history )
			@t.plot()

class @PressurePlot
	constructor: ->
		element = $('<div id="pressure_plot" style="width: 650px; height: 250px;"></div>')
		element.appendTo('.log')
		@t = new ScatterPlot("Pressure", element)
		@t.options.vAxis.format = "22E"
		@update()
		# Set a timer to constantly update the plot.
		setInterval( => 
			@update
		, 30000)

	update: ->
		# Request historical data from the server.
		pycon.transaction { action: "pressure", arguments: {'number':50} }, (r) =>
			@t.xtitle = "Time [minutes from now]"
			@t.ytitle = "Pressure [T]"	
			@t.y = ( d.data.pressure for d in r.history )
			@t.x = ( (d.time - Date.now()/1000)/60 for d in r.history )
			@t.plot()

class @Dashboard
	constructor: ->
		@element = $('<div id="dashboard"></div>')
		@element.appendTo('.log')
		@dashboardelements = []
		# Insert temperature dashboard element.
		@dashboardelements.push new TemperatureDashboardElement()
		@dashboardelements.push new PressureDashboardElement()

		for d in @dashboardelements
			d.element.appendTo @element

class @DashboardElement
	constructor: ->
		@element = $('<div class="dashboard-element"></div>')
		@symbol = "T"
		@value = "195 K"
		@update()
		setInterval( => 
			@update
		, 30000)

	render: ->
		string = "<div class='left'>#{@symbol}</div>"
		string +="<div class='right'>#{@value}</div>"
		@element.html string

	update: ->
		yes

class @TemperatureDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol = "T"
		@value 	= "U"

	update: ->
		pycon.transaction { action: "temperature" }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			if r.data.temperature < 1
				@value = (r.data.temperature*1000).toPrecision(3) + " mK"
			else
				@value = (r.data.temperature).toPrecision(3) + " K"
			@render()

class @PressureDashboardElement extends DashboardElement
	constructor: ->
		super()
		@symbol = "P"
		@value 	= "U"

	update: ->
		pycon.transaction { action: "pressure" }, (r) =>
			# Now try to format the number appropriately. Support mK and K as units.
			@value = (r.data.pressure).toExponential(1) + " T"
			@render()