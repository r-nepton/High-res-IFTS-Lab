# The ReportController controls the report tab.
class @ReportController
	constructor: ->
		@dom_element = $("<div class='report'></div>").hide()
		$('.log').append @dom_element
		@dom_element.append $("<div id='visualization'></div>")
		@dom_element.append $("<div id='control'></div>")

		google.setOnLoadCallback =>
			@ready

	ready: ->
		debugger;
		console.log "I'm going to draw the report."
		@dashboard = new google.visualization.Dashboard @dom_element[0]

		@control = new google.visualization.ControlWrapper {
			controlType: 'ChartRangeFilter',
			containerId: 'control',
			options: {
				filterColumnIndex: 0,
				ui: {
					chartType: 'LineChart',
					chartOptions: { width: '90%' }
					hAxis: { 'baselineColor': 'none' }
				},
				chartView: {
					columns: [0, 1]
				}
				minRangeSize: 86400
			}
		}, {
			state: {
				range: {
					start: -10000, 
					end: 0
				}
			}
		}

		@chart = new google.visualization.ChartWrapper {
			chartType: 'ScatterChart',
			dataTable: [["test", "test"],[700, 800]],
			options: { title: 'Countries' },
			containerId: 'visualization'
		}

		@dashboard.bind @control, @chart
		@chart.draw()
		@dashboard.draw google.visualization.arrayToDataTable [["test", "test"],[700, 800],[600, 700],[500, 600]]

