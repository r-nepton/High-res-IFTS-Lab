import threading
import Queue

# The cryo-delegate is a daemon-like thread which
# runs in parallel to the web server thread. It queries
# the cryostat periodically, records and manages the log
# of data of the status of the cryostat, and also responds
# to queries about the status of the whole system.
class CryoManager(object):
	def __init__(self):
		self.thread 	= CryoManagerThread(self)

	# This function is used to call a function on itself based
	# upon a string argument.
	def invoke(self, action):
		print "Attempted to invoke action %s" % action
		if hasattr(self, action):
			return getattr(self, action)()
		else:
			return "Invalid action: action %s is not implemented." % action

	# This function starts the thread, and lets the cryomanager loose.
	def start(self):
		self.thread.start()

	# I think this function will respond to queries in a queue-like
	# way, but it will also block until they respond. This function
	# should be called from whatever other thread, and should expect
	# a response object of some kind
	def ask(self, action, arguments):
		# The responder object will be edited by the thread.
		responder = {}
		# Now we put the request into the mailbox of the thread...
		self.thread.mailbox.put({ "action": action, "arguments":arguments, "responder": responder})
		# Wait for the queue to be completed.
		self.thread.mailbox.join()
		# Return the responder object.
		return responder

class CryoManagerThread(threading.Thread):
	def __init__(self, parent):
		threading.Thread.__init__(self)
		self.parent = parent
		self.mailbox = Queue.Queue()

	def run(self):
		while True:
			data = self.mailbox.get() 
			# The data received via this mailbox must be formatted in a specific way, 
			# including an action, arguments, and a responder hash.
			assert hasattr(data,"responder"), "Thread ask has no responder object! I can't respond to it."
			assert hasattr(data,"action"), "Thread ask has no action! I don't know what to do with it."
			response = self.parent.invoke( data.action, data.arguments )
			# Copy the response data into the responder object, which 
			# we received by reference. That way the other thread can
			# read it when we are done with the queue.
			for k,v in response:
				data.responder[k] = v
			# Mark the task as done (free up the queue).
			self.mailbox.task_done()
		
# The GenericCryoDataModel object is the base class of all
# data sources. It understands how to create its own database
# table, write its own log files, and perform queries upon itself.
class GenericCryoDataModel(object):
	pass