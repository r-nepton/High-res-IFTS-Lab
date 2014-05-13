class @ScatterPlot
	constructor: (@title, @element) ->
		@title = "Untitled graph"
		@x = []
		@xtitle = "X"
		@y = []
		@ytitle = "Y"

	plot: ->
		google.load("visualization", "1", {packages:["corechart"]});
		google.setOnLoadCallback =>
			table = []
			table.push [@xtitle, @ytitle]
			for i in [1..@x.length]
				table.push [ @x[i], @y[i] ]
			data = google.visualization.arrayToDataTable table

			xmax = Math.max.apply(Math, @x)
			xmin = Math.min.apply(Math, @x)
			xrange = xmax - xmin

			ymax = Math.max.apply(Math, @y)
			ymin = Math.min.apply(Math, @y)
			yrange = ymax - ymin

			options = {
				title: @title,
				hAxis: {title: @xtitle, minValue: xmin, minValue: xmax},
				vAxis: {title: @ytitle, minValue: ymin, minValue: ymax},
				legend: 'none'
			}

			chart = new google.visualization.ScatterChart(@element.get());