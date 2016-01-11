# This controller handles the user interface of authentication. It presents
# the user with a password prompt, and calls a callback when the password
# has been selected.
class AuthenticationController
	constructor: (@dom_element) ->
		$('body').append @dom_element.hide()
		@dom_element.html """
			<div class='authentication-overlay'>
				<div class='authentication-dialog'>
					<h1>Enter the password.</h1>
					<input type=password class='password' />
				</div>
			</div>
		"""

		@callback = ->
			yes

		$('.password').keypress (e) =>
			if e.which == 13
				@submit()

	get_password: ->
		$('.password').val()

	submit: ->
		@hide()
		@callback( @get_password().toUpperCase() )

	show: ->
		$('.password').val('')
		$('.authentication-overlay').css {height: screen.height}
		@dom_element.show()
		$('.password').focus()

	hide: ->
		@dom_element.hide()

	begin: (callback) ->
		@show()
		@callback = callback

