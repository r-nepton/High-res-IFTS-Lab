import threading
import Queue
import sqlite3, json, os, sys, numpy
from StringIO import StringIO
from dataconduits import *

database_connection = None

lib_path = os.path.abspath('./lib/sensors')
sys.path.append(lib_path)
# The cryo-delegate is a daemon-like thread which
# runs in parallel to the web server thread. It queries
# the cryostat periodically, records and manages the log
# of data of the status of the cryostat, and also responds
# to queries about the status of the whole system.
class CryoManager(object):
	def __init__(self):
		self.thread 	= CryoManagerThread(self)
		self.sensors_list = {}
		self.user_log_writer   	= None
		self.robot_log_writer   = None
		# Now, start the object which provokes the cryomanager every 30 seconds
		# via its "wake" method.
		self.stop_wake_thread = threading.Event()
		self.wakethread = WakeThread(self.stop_wake_thread, self)
		self.wakethread.start()

	# This function is used to call a function on itself based
	# upon a string argument.
	def invoke(self, action, arguments):
		if hasattr(self, action):
			return getattr(self, action)(arguments) 
		else:
			error = {"error": "Invalid action: the requested action '%s' is not implemented." % action}
			print error
			return error

	# This function starts the thread, and lets the cryomanager loose.
	def start(self):
		self.thread.start() 

	def thread_initialize(self, args=None):
		global database_connection

		# First, we'll copy the file system database into a string, then load it into memory.
		print "Attempting to load database into memory..."
		database_connection = sqlite3.connect('data/database.db')
		tempfile = StringIO()
		for line in database_connection.iterdump():
			tempfile.write('%s\n' % line)
		database_connection.close()
		tempfile.seek(0)

		# Now we'll load the script into memory...
		print "Database loaded. Now converting to memory database..."
		database_connection = sqlite3.connect(':memory:')
		database_connection.cursor().executescript( tempfile.read() )
		database_connection.commit()

		print "Database loaded."

		self.sensors_list = {
			'pulse_tube_first_stage': 	PulseTubeFirstStageTemperatureSensor(),
			'pulse_tube_second_stage': 	PulseTubeSecondStageTemperatureSensor(),
			'pressure':  				GenericPressureSensor(1),
			'FAA_temperature': 			FAATemperatureSensor(),
			'magnet_current':			MagnetCurrentSensor(),
			'compressor':				CompressorSensor()
		} 
		self.user_log_writer   	= UserLogWriter()

	# This function saves the memory database back to disk.
	def save_to_disk(self, arguments):
		# Collect together all of the information.
		tempfile = StringIO()
		for line in database_connection.iterdump():
			tempfile.write('%s\n' % line)
		tempfile.seek(0)

		# Now write the archive database to disk.
		archive_database = sqlite3.connect('data/database.db')
		archive_database.cursor().executescript( tempfile.read() )
		archive_database.commit()
		archive_database.close()

	def __del__(self):
		self.save_to_disk()
		database_connection.close()

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

	def pressure(self, arguments):
		if 'number' in arguments:
			return {'history': self.sensors_list['pressure'].tail(arguments[u'number']) }
		data = self.sensors_list['pressure'].tail(1)
		if len(data) == 0:
			return { "error":"unknown" }
		else:
			return data[0]

	def magnet_current(self, arguments):
		if 'number' in arguments:
			return {'history': self.sensors_list['magnet_current'].tail(arguments[u'number']) }
		data = self.sensors_list['magnet_current'].tail(1)
		if len(data) == 0:
			return { "error":"unknown" }
		else:
			return data[0]

	def write_log(self, arguments):
		if 'log' in arguments:
			self.user_log_writer.write_log(arguments['log'])
		return {'result': 'success'}

	def user_log(self, arguments):
		if 'number' in arguments:
			return {'history': self.user_log_writer.tail(arguments[u'number']) }
		data = self.user_log_writer.tail(1)
		if len(data) == 0:
			return { "error":"unknown" }
		else:
			return data[0]

	def sensor(self, arguments):
		if 'sensor' in arguments:
			s = self.sensors_list[arguments[u'sensor']]
		else: 
			return { "error": "sensor unspecified" }

		if 'number' in arguments:
			return {'history': s.tail(arguments[u'number']) }
		
		data = s.tail(1)
		if len(data) == 0:
			return { "error":"unknown" }
		else:
			return data[0]

	def temperature(self, arguments):
		if 'number' in arguments:
			return {'history': self.sensors_list['pulse_tube_second_stage'].tail(arguments[u'number']) }
		data = self.sensors_list['pulse_tube_second_stage'].tail(1)
		if len(data) == 0:
			return { "error":"unknown" }
		else:
			return data[0]

	def temperature_2(self, arguments):
		if 'number' in arguments:
			return {'history': self.sensors_list['pulse_tube_first_stage'].tail(arguments[u'number']) }
		data = self.sensors_list['pulse_tube_first_stage'].tail(1)
		if len(data) == 0:
			return { "error":"unknown" }
		else:
			return data[0]

	def sensors(self, arguments):
		return { 'sensors': [ {'title':s.name, 'units':s.units } for k,s in self.sensors_list.iteritems() ] }

	# This function is called periodically by a timer thread (e.g. every 30 seconds) via the
	# CryoManagerThread object. It does regular housekeeping things, checks on temperatures
	# and so on.
	def wake(self, args=None):
		print "Waking up for maintenance."
		print "Polling sensors..."
		for k,s in self.sensors_list.iteritems():
			s.poll()
		database_connection.commit()
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
				if response != None:
					for k,v in response.iteritems():
						data['responder'][k] = v
				# Mark the task as done (free up the queue).
			except Exception:
				print "Error: invalid command."
				data['responder']['error'] = { "error": "invalid command" }
				raise
			self.mailbox.task_done()

class WakeThread(threading.Thread):
	def __init__(self, event, cryomanager):
		threading.Thread.__init__(self)
		self.cryomanager = cryomanager
		# Connect to the SQLite database.
		self.stopped = event

	def run(self):
		self.cryomanager.ask('thread_initialize',{})
		iteration = 0
		while not self.stopped.wait(10):
			iteration += 1
			self.cryomanager.ask('wake', {})
			if iteration%1 == 0:
				self.cryomanager.ask('save_to_disk', {})

# Now, import all of the sensors.
from sensors import *
from log_writer import *