class @ControlController
	constructor: (@dom_element) ->
		$('.log').append @dom_element

		@dom_element.html """
			<div class='regionbox'>
				<h1 class='regiontitle'>cycle</h1>
				<div class='horizontal-field'>
					<div class='field'><input type=text /><span class='units'>hours</span></div>
					<span>hold time</span>
				</div>

				<div class='menubutton' style="background-color: black; color: white;">save</div>
				<div class='menubutton' style="background-color: rgb(170, 185, 93); color: white;">cycle</div>
				

				<div class="buttonspacer"></div>
			</div>

			<div class='regionbox'>
				<h1 class='regiontitle'>regulation</h1>
				<div class='horizontal-field'>
					<div class='field'><input type=text /><span class='units'>mK</span></div>
					<span>regulation temperature</span>
				</div>
				<div class='menubutton' style="background-color: black; color: white;">save</div>
				<div class='menubutton' style="background-color: rgb(51, 102, 204); color: white;">regulate</div>
				<div class="buttonspacer"></div>
			</div>
		"""