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
	socket.onclose = ->
		console.log "Socket connection was closed, unexpectedly."
		console.log "I don't know why, but the socket was closed (!)"

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

	# Create the logs.
	window.logs_controller = new LogsController( $('<div class="logs"></div>').hide() )

	# Create the report.
	#window.report_controller = new ReportController()

	# Create the control panel.
	window.control_controller = new ControlController $("<div class='control'></div>").hide()