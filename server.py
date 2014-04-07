import tornado.ioloop
import tornado.web
import tornado.websocket
import time
import inspect
import json

# Configurable parameters for the server:
# -------------------------------------- #
# PORT: the operating port
PORT 		= 80
RUN_DATE 	= time.strftime( "%H:%M:%S on %B %d %Y" )
VERSION 	= 0
# -------------------------------------- #

RESPONSE 	= 1

# The JHandler handles WebSocket communication
# with the Javascript on the browser. It answers
# requests and so forth from the browser. Eventually,
# it will behave as a wrapper to another thing that
# will interface with measurement devices.
class JHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		print "Opening..."

	def on_message(self, message):
		print "Message received: %s " % message 
		data = json.loads( message )

		# The default response: it should be overwritten, or else some
		# kind of internal problem occured.
		response = "Transaction failed to handle: internal assertion failure occurred."

		# If the message is a transaction, it'll contain a 
		# transaction ID. Then we need to do whatever it is asking
		# for and then response using the same transaction ID.
		if 'transaction_id' in data:
			# The result is an actionable transaction. 
			if 'action' in data['data']:
				response = actionablerequesthandler.invoke( data['data']['action'] )
			else:
				response = "Invalid action: no action specified";
		else:
			response = "Invalid transaction: no transaction ID specified"

		# Need to respond with the correct format. The format must include
		# the actual data response under "data" and the transaction id that
		# it is responding to under "transaction_id" in order to be valid.
		self.write_message( json.dumps ( {'data': response, 'transaction_id': data['transaction_id'] } ) )

	def on_close(self):
		print "Closing..."

# The JActionableRequestHandler class basically completes actions that the browser
# asks of it. It should be spoken to through the "invoke" function, which basically
# searches to see if the actionablerequesthandler can handle that action, and if so,
# does whatever is necessary. You could also return a hash from the actionable
# functions, and then the system will JSON your return value.
class JActionableRequestHandler:
	def invoke(self, action):
		print "Attempted to invoke action %s" % action
		if hasattr(self, action):
			return getattr(self, action)()
		else:
			return "Invalid action: action %s is not implemented." % action

	# This function tells us some information about the current running version
	# of the server, etc. 
	def validate_version(self):
		return {
			'start_date'	: "Program started: %s " % RUN_DATE,
			'version'		: VERSION
		}

# The global actionablrequesthandler: there is only one instance of this, 
# even though there may be many instances of JHandlers for different clients.
# This means we can hog things like serial connections to thermometry devices, 
# etc. and not worry about having clashes, etc.
actionablerequesthandler = JActionableRequestHandler()

# This static file handler override class is used
# to force caching to be turned off for all static
# files, which is a debugging measure.
class DebugStaticFileHandler(tornado.web.StaticFileHandler):
	def set_extra_headers(self, path):
		# This is necessary to prevent Chrome from caching everything. Can be safely
		# removed when debugging is over.
		self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

application = tornado.web.Application( [
	(r"/json", JHandler),
	(r"/()", DebugStaticFileHandler, {'path': 'assets/web.html'} ),
	(r"/(.*)", DebugStaticFileHandler, {'path': 'assets/'}),
])

# This starts the application
application.listen(PORT)
# This: I have no idea what it does.
tornado.ioloop.IOLoop.instance().start()