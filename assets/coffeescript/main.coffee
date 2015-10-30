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
	window.graphs.push new TemperaturePlot3()
	window.graphs.push new TemperaturePlot4()
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
