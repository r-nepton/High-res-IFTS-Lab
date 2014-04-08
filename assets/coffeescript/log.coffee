window.log = (text) ->
	t = marked.parse text
	$('.log').append t