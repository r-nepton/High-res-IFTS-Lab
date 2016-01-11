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

