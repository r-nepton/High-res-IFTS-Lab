import matplotlib.pyplot as plot
import matplotlib, numpy, datetime, time, matplotlib.dates as mdates

# To make a sensor plot, you need to provide the start and end date strings
# in the following format: "15:30 16 June 2014", for example.
def make_sensor_plot(sensor, fields, start, end, data_processor=lambda x: x):
	# Define the data collection interval.
	start = time.mktime( time.strptime(start, "%H:%M %d %B %Y") )
	end   = time.mktime( time.strptime(end, "%H:%M %d %B %Y") )
	# Collect the averaged data between the specified time interval.
	data = sensor.range( int(start), int(end) , 200)

	# We could support a list of fields, if we want to plot them together.
	if isinstance(fields, basestring):
		fields = [ fields ]

	t = []
	c = []
	
	for f in fields:
		c.append( [] )

	for d in data:
		# If the data is of type string, we won't include it in the plot.
		# Mostly, those strings are just errors, e.g. "unknown"
		valid = True
		for f in fields:
			if f not in d['data'] or isinstance(d['data'][f], basestring):
				valid = False
				break

		if not valid:
			continue
		# We don't actually plot unix timestamps, so get dates.
		t.append( datetime.datetime.fromtimestamp(d['time'])  )
		for i,f in enumerate(fields): 
			c[i].append( data_processor( d['data'][f] ) )
	        
	# Convert the dates into special numbers (??)
	dates = mdates.date2num(t)

	fig, ax = plot.subplots()
	fig.set_size_inches(15,4)
	for x in c:
		ax.plot( t, x, 'k.')
	ax.xaxis.set_major_locator( mdates.DayLocator() )
	ax.xaxis.set_major_formatter( mdates.DateFormatter("%B %d") )
	                             
	ax.xaxis.set_minor_locator( matplotlib.ticker.LinearLocator(10) )
	ax.xaxis.set_minor_formatter( mdates.DateFormatter("%H:%M") )

	xax = ax.get_xaxis()
	xax.set_tick_params(which='major', pad=15)
	xax.grid(True, which='major')

	plot.xlabel("Time")
	plot.title(sensor.name)