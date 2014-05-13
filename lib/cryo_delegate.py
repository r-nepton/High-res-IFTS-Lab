import threading
import Queue
import sqlite3, json
from dataconduits import *

database_connection = sqlite3.connect('data/database.db')

# The cryo-delegate is a daemon-like thread which
# runs in parallel to the web server thread. It queries
# the cryostat periodically, records and manages the log
# of data of the status of the cryostat, and also responds
# to queries about the status of the whole system.
class CryoManager(object):
	def __init__(self):
		self.thread 	= CryoManagerThread(self)
		# Now, start the object which provokes the cryomanager every 30 seconds
		# via its "wake" method.
		self.stop_wake_thread = threading.Event()
		self.wakethread = WakeThread(self.stop_wake_thread, self)
		self.wakethread.start()

	# This function is used to call a function on itself based
	# upon a string argument.
	def invoke(self, action, arguments):
		print "Attempted to invoke action %s" % action
		if hasattr(self, action):
			return getattr(self, action)(arguments) 
		else:
			error = {"error": "Invalid action: the requested action '%s' is not implemented." % action}
			print error
			return error

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
		message = { "action": action, "arguments":arguments, "responder": responder}
		self.thread.mailbox.put(message)
		# Wait for the queue to be completed.
		self.thread.mailbox.join()
		# Return the responder object.
		return responder

	# This function is called periodically by a timer thread (e.g. every 30 seconds) via the
	# CryoManagerThread object. It does regular housekeeping things, checks on temperatures
	# and so on.
	def wake(self):
		print "Waking up for maintenance."
		print "Going back to sleep."

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
			assert "responder" in data, "Thread ask has no responder object! I can't respond to it."
			try: 
				assert "action" in data, "Thread ask has no action! I don't know what to do with it."
				response = self.parent.invoke( data['action'], data['arguments'] )
				# Copy the response data into the responder object, which 
				# we received by reference. That way the other thread can
				# read it when we are done with the queue.
				print "The response is: ", response
				for k,v in response.iteritems():
					data['responder'][k] = v
				# Mark the task as done (free up the queue).
			except Exception:
				print "Error: invalid command."
				data['responder']['error'] = { "error": "invalid command" }
				raise
			self.mailbox.task_done()
		
# The GenericCryoDataModel object is the base class of all
# data sources. It understands how to create its own database
# table, write its own log files, and perform queries upon itself.
class GenericCryoDataModel(object):
	def __init__(self, name):
		self.name 			= name
		self.conduit 		= GenericDataConduit()
		self.database_name 	= self.name
		self.db 	 	 	= database_connection.cursor() # database connection.
		self.initialize()
		
	def __del__(self):
		database_connection.commit()

	# This function returns the database configuration. It should almost always
	# be the same.
	def database_configuration(self):
		q 	= "CREATE TABLE IF NOT EXISTS %s (" % self.database_name
		q 	+= "id INTEGER PRIMARY KEY,\n"
		q 	+= "time 	timestamp(14) not null,"
		q 	+= "value 	varchar(512) null"
		q 	+= ")"
		return q

	# Inser the data value (a python hash) into the database
	# using the current time.
	def insert_data(self, value):
		q 	= "INSERT INTO %s (time, value) VALUES (CURRENT_TIMESTAMP, ?)" % self.database_name
		self.db.execute(q, [json.dumps(value)]) 

	# Get the last X number of entries into the database.
	def tail(self, number=10):
		q 	= "SELECT value,CAST(strftime('%%s',time) as INT) FROM %s ORDER BY time DESC LIMIT ?" % self.database_name
		self.db.execute(q, [number])
		return [ { 'time': f[1], 'data': json.loads(f[0]) }  for f in self.db.fetchall() ]

	def initialize(self):
		# Set up the databsae.
		self.db.execute( self.database_configuration() )


class WakeThread(threading.Thread):
	def __init__(self, event, cryomanager):
		threading.Thread.__init__(self)
		self.cryomanager = cryomanager
		self.stopped = event

	def run(self):
		while not self.stopped.wait(10):
			self.cryomanager.wake()