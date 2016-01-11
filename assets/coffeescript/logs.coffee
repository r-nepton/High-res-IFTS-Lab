class @LogsController
	constructor: (@dom_element) ->
		# Add our DOM element to the page.
		$('.log').append @dom_element
		# Create the interface for the logs.
		@textbox = $("<input type=text class=log_textbox />")
		@textbox.keydown (e) =>
			if e.keyCode == 13
				e.preventDefault()
				@submit()

		@dom_element.append @textbox
		@dom_element.append $("<p></p>")

		@latest_log = new LogElement()
		@dom_element.append @latest_log.dom_element

		@past_logs_list = $("<div class='past_logs_list'></div>").hide()
		@dom_element.append @past_logs_list

		@update()

		setInterval( => 
			@update()
		, 30000)

	focus: ->
		@textbox.focus()

	submit: ->
		# Detect if the box is just whitespace.
		if $.trim(@textbox.val()).length > 0
			pycon.transaction { action: "write_log", arguments: { 'log': @textbox.val() }}, =>
				# Update the panel
				@update()
				# Clear out the textbox
				@textbox.val('')

	update: ->
		pycon.transaction { action: "user_log", arguments: {'number':5} }, (r) =>
			console.log "Received update:", r
			if r.history.length >= 1
				@latest_log.message = r.history[0].data
				@latest_log.timestamp = r.history[0].time
				@latest_log.render()
			else
				@latest_log.message = "There are no logs yet!"
				@latest_log.timestamp = 0
				@latest_log.render()

			# Clear out the old list of logs.
			@past_logs_list.html ""
			@past_logs_list.append $("<p>&nbsp;</p>")
			for h in r.history[1..]
				f = new LogElement()
				f.message = h.data
				f.timestamp = h.time
				@past_logs_list.append f.dom_element
				f.render()

			if r.history.length > 1
				@past_logs_list.show()



# The log element is a visual representation of a log.
class @LogElement
	@basic_element: ->
		return $("<div class='log_element'></div>")

	constructor: (@dom_element) ->
		if !@dom_element? 
			@dom_element = LogElement.basic_element()
		@dom_message = $("<div class='log_element_message'></div>")
		@dom_timestamp = $("<div class='log_element_timestamp'></div>")

		# Default values.
		@message = ""
		@timestamp = 0

		@dom_element.append @dom_timestamp
		@dom_element.append @dom_message

	format_time: ->
		
		sdt = (new Date().getTime())/1000 - @timestamp
		dt = Math.abs(sdt)

		#If the log was created more then an hour ago, we just want a plain timestamp
		if dt >= 60*60

			date_ob = new Date(@timestamp*1000)
			time_string_options = {
				timezone: "UTC", month: "short", day: "numeric", 
				hour: "2-digit", hour12: false, minute: "2-digit", second: "2-digit"}
			datestamp = date_ob.toLocaleString('en-US',time_string_options)

			log_time = "#{datestamp}"

		else

			units = switch
				when dt < 60 				then { unit: 'second', 	amount: 1}
				when dt < 60*60 			then { unit: 'minute', 	amount: 60}

			if sdt > 0
				postfix = "ago"
			else
				postfix = "from now"

			quantity = Math.ceil(dt / units.amount)

			if quantity > 1
				unit_postfix = "s"
			else
				unit_postfix = ""

			log_time = "#{quantity} #{units.unit}#{unit_postfix} #{postfix}"

		#The 0th log doesn't need a timestamp
		if @timestamp == 0
			log_time = ""

		return log_time

	render: ->
		@dom_message.html @message
		@dom_timestamp.html @format_time()

