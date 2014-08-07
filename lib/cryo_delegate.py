import threading
import Queue
import sqlite3, json, os, sys, numpy
from StringIO import StringIO
from dataconduits import *

database_connection = None

lib_path = os.path.abspath('./lib/sensors')
sys.path.append(lib_path)
lib_path = os.path.abspath('./lib/operations')
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
		self.operations 		= [ ]
		# Now, start the object which provokes the cryomanager every 30 seconds
		# via its "wake" method.
		self.stop_wake_thread = threading.Event()
		self.wakethread = WakeThread(self.stop_wake_thread, self)
		self.wakethread.start()
		self.password = True
		self.log_data = False # By default, the system starts up in a state where it doesn't log data.

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

	def thread_initialize(self, database_file='data/database.db'):
		global database_connection

		# First, we'll copy the file system database into a string, then load it into memory.
		print "Attempting to load database into memory..."
		if not isinstance(database_file, basestring):
			database_file = 'data/database.db'
		database_connection = sqlite3.connect(database_file)
		database_connection.execute("PRAGMA synchronous=OFF")
		database_connection.execute("PRAGMA cache_size=-512000")

		print "Database loaded."

		self.sensors_list = {
			'pulse_tube_first_stage': 	PulseTubeFirstStageTemperatureSensor(),
			'pulse_tube_second_stage': 	PulseTubeSecondStageTemperatureSensor(),
			'pressure':  				GenericPressureSensor(1),
			'FAA_temperature': 			FAATemperatureSensor(),
			'magnet_current':			MagnetCurrentSensor(),
			'compressor':				CompressorSensor(),
			'breakout':					BreakoutBoardSensor()
		} 
		self.PID_controller = PIDControllerInterface()
		self.user_log_writer   	= UserLogWriter()

		# Open up the password file to figure out which
		# password to trust. The passwords file is generated.
		if not os.path.isfile("etc/secret.passwords"):
			print "Hey! You need to generate a password. You can do that by running etc/generate_passwords.py"
			os._exit(0)
		f = open("etc/secret.passwords")
		password_database = json.loads( f.read() )
		self.password = password_database['password']

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

	def ramp_up(self, arguments):
		if 'current' in arguments and 'time' in arguments and 'authentication' in arguments:
			if arguments['authentication'] == "charlie":
				current = arguments['current']
				time = arguments['time']
		
				self.operations.append( MagUpOperation( time, current, self.PID_controller, self.sensors_list['magnet_current'].conduit ) )
				return { 'result': 'success' }

		return { 'result': 'failure' }

	def ramp_down(self, arguments):
		if 'time' in arguments and 'authentication' in arguments:
			if arguments['authentication'] == "charlie":
				time = arguments['time']
		
				self.operations.append( MagDownOperation( time, self.PID_controller, self.sensors_list['magnet_current'].conduit ) )
				return { 'result': 'success' }

		return { 'result': 'failure' }

	# This function is called every one second, and is used to step the current
	# process. A process is a class, which describes a long time-scale operation.
	def step(self, arguments):
		if len(self.operations) > 0:
			if self.operations[0].finished:
				# Instruct the operation that it is finished.
				self.operations[0].ended()
				# Remove the operation from the queue.
				self.operations.pop(0)
			else:
				# Run the operation.
				self.operations[0].step()

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
		# Only log data if we have data logging enabled.
		if self.log_data == True:
			print "Polling sensors..."
			for k,s in self.sensors_list.iteritems():
				s.poll()
			database_connection.commit()

		print "Going back to sleep."

	def ups_power_lost(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				print "UPS power lost!"		
			else:
				print "Illegal password sent for UPS shutdown."
		else:
			print "UPS shutdown attempted with no password."

	# When the program starts up, by default it doesn't take 
	# data. You have to enable data collection using the form
	# on the webpage, which requires a password.
	def set_data_logging_state(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				if 'state' in arguments:
					print "data logging set to: %s" % arguments['state']
					if arguments['state'] == True:
						self.log_data = True
					else:
						self.log_data = False
					return { "success": True }
				else:
					print "Data logging state change attempted with no state."
			else:
				print "Illegal password sent for data logging state change."
		else:
			print "Data logging state change attempted with no password."

	def shutdown_server(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				print "Server shutting down!"
				os._exit(0);
			else:
				print "Illegal password sent for shutdown_server command."
		else:
			print "Server shutdown attempted with no password."

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
		index = 0
		while not self.stopped.wait(1):
			index = index % 60
			if index % 20 == 0: 
				# Poll all sensors every 20 seconds.
				self.cryomanager.ask('wake', {})
			
			# If we are in the middle of a process, we want to call
			# the "step" function. 
			self.cryomanager.ask('step', {})
			index += 1

# Now, import all of the sensors.
from sensors import *
from operations import *
from log_writer import *