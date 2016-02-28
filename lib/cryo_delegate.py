import threading
import Queue
import sqlite3, json, os, sys, numpy, datetime
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
		self.log_data = True # By default, the system starts up in a state where it does log data.

		# Cycle settings
		self.magnetization_hold_current = 10 # Amps
		self.magnetization_hold_time = 1200 # seconds
		self.ramp_up_time = 1200 # seconds
		self.ramp_down_time = 1200 # seconds
		self.regulation_temperature  = 0.25 #  Kelvin
		self.inductor_relax_time = 480 # seconds

		# Schedule settings
		self.schedule_cycles = False # By default, the system does not schedule any mag cycles
		#self.sched_run_on_weekend = False # By default, no cycles will run on weekends
		self.sched_number_days = 5 # Number of days to schedule cyce for
		self.sched_magnetization_hold_current = self.magnetization_hold_current # Amps
		self.sched_magnetization_hold_time = self.magnetization_hold_time # seconds
		self.sched_ramp_up_time = self.ramp_up_time # seconds
		self.sched_ramp_down_time = self.ramp_down_time # seconds
		self.sched_regulation_temperature = self.regulation_temperature # Kelvin
		self.sched_estimated_time = self.sched_magnetization_hold_time + self.sched_ramp_up_time + self.sched_ramp_down_time + self.inductor_relax_time # seconds
		self.sched_start_time = datetime.datetime.strptime('04:00','%H:%M') # Start time
		self.sched_end_time = self.sched_start_time + datetime.timedelta(0,self.sched_estimated_time) # End time, will be calculated from start time and estimated run time


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
			'pressure':  			GenericPressureSensor(1),
			'FAA_temperature': 		FAATemperatureSensor(),
			'magnet_current':		MagnetCurrentSensor(),
			'magnet_back_emf':		MagnetBackEmfSensor(),
			'compressor':			CompressorSensor(),
			'breakout':			BreakoutBoardSensor(),
			'ups':				UPSSensor() # <-- you can uncomment this when you plug in the UPS
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

		# The server has started sucessfully.
		print " -- Cryostat server started -- "
		self.print_log("Server startup completed.")

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

	# This function is called in order to immediately stop all operations.
	def emergency_stop(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log("Emergency stop issued.")
				self.user_log_writer.write_log("Emergency stop issued.")
				self.operations = []
			else:
				self.print_log("Incorrect password issued for emergency stop.")

	# This function is called in order to immediately stop all operations and ramp down current.
	def emergency_shutdown(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log("Emergency shutdown issued.")
				self.user_log_writer.write_log("Emergency shutdown issued.")
				self.operations = []
				self.operations.append( EmergencyShutdown(self.PID_controller) )
			else:
				self.print_log("Incorrect password issued for emergency shutdown.")

	# This function is called to open the heatswitch.
	def open_heatswitch(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log("Heat switch opened.")
				self.user_log_writer.write_log("Heat switch opened.")
				self.sensors_list["breakout"].conduit.open_heat_switch()
				self.sensors_list["breakout"].conduit.heat_switch_open = True
			else:
				self.print_log("Incorrect password issued for opening heat switch.")

	# This function is called to close the heatswitch.
	def close_heatswitch(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log("Heat switch closed.")
				self.user_log_writer.write_log("Heat switch closed.")
				self.sensors_list["breakout"].conduit.close_heat_switch()
				self.sensors_list["breakout"].conduit.heat_switch_open = False
			else:
				self.print_log("Incorrect password issued for closing heat switch.")

	def cycle_settings(self, arguments):
		# Authenticate first, in case we are doing a "set" operation.
		if 'password' in arguments:
			if arguments['password'] == self.password:
				# Now check if we are setting or getting.
				if 'hold_time' in arguments:
					try:
						self.ramp_up_time = float(arguments['ramp_up_time'])
						self.print_log("Updated ramp-up time to %s seconds" % self.ramp_up_time)
						self.magnetization_hold_current = float(arguments['hold_current'])
						self.print_log("Updated hold current to %s amps" % self.magnetization_hold_current)
						self.magnetization_hold_time = float(arguments['hold_time'])
						self.print_log("Updated hold time to %s seconds" % self.magnetization_hold_time)
						self.ramp_down_time = float(arguments['ramp_down_time'])
						self.print_log("Updated ramp-down time to %s seconds" % self.ramp_down_time)
						return { 'result': 'success' }
					except Exception:
						return { 'error': 'invalid parameters specified.' }

				# Now check if we are setting or getting.
				if 'regulation_temperature' in arguments:
					try:
						self.regulation_temperature = float(arguments['regulation_temperature'])
						self.print_log("Updated regulation temperature to %s K" % self.regulation_temperature) 
						# If the computer is actually in the process of regulating,
						# then let's try to actually change the regulation setpoint.
						if self.PID_controller.is_in_PID_mode():
							if len(self.operations) == 0:
								self.print_log("Starting operation to change regulation setpoint.")
								#print "operations = %s" % self.operations
								try:
									self.operations.append( ChangeRegulationOperation( self.regulation_temperature, self.PID_controller) )
								except Exception as e:
									print e
						else:
							if len(self.operations) > 0:
								# Inform the BeginRegulation operation about the change, if necessary.
								# But just send this message to the future operations, not the one in 
								# progress right now.
								self.print_log("Updating setpoint for future regulation operation.")
								for o in self.operations[1:]:
									if isinstance(o, BeginRegulationOperation):
										o.update_regulation_temperature( self.regulation_temperature )
							else:
								self.print_log("A change to the operation is not necessary.")


						return { 'result': 'success' }
					except Exception:
						return { 'error': 'invalid regulation temperature specified.' }

		# Well, if we didn't set anything,it must be just a get request.
		return { 'hold_time': self.magnetization_hold_time, 'hold_current': self.magnetization_hold_current, 'ramp_up_time': self.ramp_up_time, 'ramp_down_time': self.ramp_down_time, 'regulation_temperature': self.regulation_temperature, 'inductor_relax_time': self.inductor_relax_time }

	def schedule_settings(self, arguments):
		# Authenticate first, in case we are doing a "set operation.
		if 'password' in arguments:
			if arguments['password'] == self.password:
				# Now check if we are setting or getting
				if 'number_days' in arguments:
					try:
						# Update the scheduled cycle parameters using the current saved cycle parameters
						self.sched_magnetization_hold_current = self.magnetization_hold_current # Amps
						self.sched_magnetization_hold_time = self.magnetization_hold_time # seconds
						self.sched_ramp_up_time = self.ramp_up_time # seconds
						self.sched_ramp_down_time = self.ramp_down_time # seconds
						self.sched_regulation_temperature = self.regulation_temperature # Kelvin
						self.sched_estimated_time = self.sched_magnetization_hold_time + self.sched_ramp_up_time + self.sched_ramp_down_time + self.inductor_relax_time # seconds
						self.print_log("Updated scheduled ramp-up time to %s seconds" % self.sched_ramp_up_time)
						self.print_log("Updated scheduled hold current to %s amps" % self.sched_magnetization_hold_current)
						self.print_log("Updated scheduled hold time to %s seconds" % self.sched_magnetization_hold_time)
						self.print_log("Updated scheduled ramp-down time to %s seconds" % self.sched_ramp_down_time)
						self.print_log("Updated scheduled regulation temperatur to %s K" % self.sched_regulation_temperature)					
	
						# Update the start time and end time from the webpage
						self.sched_number_days = int(arguments['number_days'])
						self.print_log("Updated scheduling run time to %d days" % self.sched_number_days)
						self.sched_start_time = datetime.datetime.strptime((arguments['start_time']),'%H:%M')
						self.print_log("Updated scheduling start time to %s" % self.sched_start_time.strftime('%H:%M'))
						
						# Calculate the end time from the estimated duration
						self.sched_end_time = self.sched_start_time + datetime.timedelta(0,self.sched_estimated_time) # End time, will be calculated from start time and estimated run time
						self.print_log("Updated estimated end time to %s" % self.sched_end_time.strftime('%H:%M'))
						return { 'result': 'success' }
					except Exception:
						return { 'error': 'invalid parameters specified.' }

		# If nothing was set, it must be a get request.
		return { 'number_days': self.sched_number_days, 'start_time': self.sched_start_time.strftime('%H:%M'), 'end_time': self.sched_end_time.strftime('%H:%M')}


	# This function begins a full magnetization cycle. It's a dangerous
	# operation to run, so it has a lot of self-checks built in.
	def begin_magnetization_cycle(self, arguments):
		# The user needs to authenticate first.
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log( "Magnetization cycle started." )
				ramp_up_time = self.ramp_up_time # seconds
				ramp_down_time = self.ramp_down_time # seconds
				current = self.magnetization_hold_current # amperes (max 18.5)
				hold_time = self.magnetization_hold_time # seconds
				regulation_temperature = self.regulation_temperature # seconds
				inductor_relax_time = self.inductor_relax_time # seconds

				# Start by setting up manual mode, switching to mag cycle, etc.
				self.operations.append( BeginMagnetizationOperation( PID_interface=self.PID_controller, temperature_3K_sensor=self.sensors_list['pulse_tube_second_stage'], temperature_FAA_sensor=self.sensors_list['FAA_temperature'], breakout_board=self.sensors_list['breakout'], back_emf_sensor=self.sensors_list['magnet_back_emf'] ) )
				# Wait for 30 seconds before beginning the next stage to allow for
				# fluctuations from the mag cycle switch throw.
				self.operations.append( SleepOperation( 30 ) )
				# Now begin magnetization
				self.operations.append( MagUpOperation( ramp_up_time, current, PID_interface=self.PID_controller, current_sensor=self.sensors_list['magnet_current'], temperature_FAA_sensor=self.sensors_list['FAA_temperature'], temperature_3K_sensor=self.sensors_list['pulse_tube_second_stage'], breakout_board=self.sensors_list['breakout'], back_emf_sensor=self.sensors_list['magnet_back_emf'] ) )
				# Now we must soak (for the hold time).
				self.operations.append( MagnetizationHoldOperation( hold_time ))
				# Now we need to demagnetize
				self.operations.append( MagDownOperation( ramp_down_time, PID_interface=self.PID_controller, breakout_board=self.sensors_list['breakout'], current_sensor=self.sensors_list['magnet_current'], back_emf_sensor=self.sensors_list['magnet_back_emf'] ) )
				# Now we need to wait 8 minutes to let the inductor relax
				self.operations.append( InductorRelaxOperation( inductor_relax_time ) )
				# Finally, begin regulation.
				self.operations.append( BeginRegulationOperation( regulation_temperature, PID_interface=self.PID_controller, current_sensor=self.sensors_list['magnet_current'], temperature_FAA_sensor=self.sensors_list['FAA_temperature'], breakout_board=self.sensors_list['breakout'], back_emf_sensor=self.sensors_list['magnet_back_emf'] ) )
			else:
				self.print_log( "Attempted to start magnetization cycle with incorrect password." )
		else:
			self.print_log( "Attempted to start magnetization cycle with no password." )

	# This function begins a manual mag-down cycle. Ideally used if the cryo-server
	# fails while performing a regular magnetization cycle with current still in the coil
	def manual_magdown(self, arguments):
		# The user needs to authenticate first.
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log( "Manual mag-down started." )
				ramp_down_time = self.ramp_down_time # seconds

				# We need to demagnetize
				self.operations.append( MagDownOperation( ramp_down_time, PID_interface=self.PID_controller, breakout_board=self.sensors_list['breakout'], current_sensor=self.sensors_list['magnet_current'], back_emf_sensor=self.sensors_list['magnet_back_emf'] ) )
			else:
				self.print_log( "Attempted to start manual mag-down with incorrect password." )
		else:
			self.print_log( "Attempted to start manual mag-down with no password." )

	# This function manually starts regulation mode. Ideally used if the cryo-server
	# fails while starting to regulate, with the stage temperature below the setpoint
	def manual_regulate(self, arguments):
		# The user needs to authenticate first.
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log( "Manual regulate started." )
				regulation_temperature = self.regulation_temperature #seconds

				# Begin regulation.
				self.operations.append( BeginRegulationOperation( regulation_temperature, PID_interface=self.PID_controller, current_sensor=self.sensors_list['magnet_current'], temperature_FAA_sensor=self.sensors_list['FAA_temperature'], breakout_board=self.sensors_list['breakout'], back_emf_sensor=self.sensors_list['magnet_back_emf'] ) )
			else:
				self.print_log( "Attempted to start manual regulate with incorrect password." )
		else:
			self.print_log( "Attempted to start manual regulate with no password." )

	# This function is called every one second, and is used to step the current
	# process. A process is a class, which describes a long time-scale operation.
	def step(self, arguments):
		if len(self.operations) > 0:
			if self.operations[0].finished:
				# Instruct the operation that it is finished.
				self.operations[0].ended()
				# Decide whether the operation was succesful or not.
				if self.operations[0].success == False:
					self.print_log("An operation (%s) finished with errors. Clearing operation queue." % self.operations[0].__class__.__name__)
					self.user_log_writer.write_log("Halted from error during %s." % self.operations[0].__class__.__name__)
					self.operations = []
				else:
					# Remove the operation from the queue.
					self.print_log("An operation (%s) finished successfully." % self.operations[0].__class__.__name__)
					self.operations.pop(0)
			else:
				# Run the operation.
				if self.operations[0].step_index == 0 and self.operations[0].has_started_message:
					self.user_log_writer.write_log( self.operations[0].started_message )
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

	def magnet_back_emf(self, arguments):
		if 'number' in arguments:
			return {'history': self.sensors_list['magnet_back_emf'].tail(arguments[u'number']) }
		data = self.sensors_list['magnet_back_emf'].tail(1)
		if len(data) == 0:
			return { "error":"unkown" }
		else:
			return data[0]

	def print_log(self, message):	
		now = datetime.datetime.now()
		print " [%s] %s " % ( now.strftime("%I:%M%p %d %B %Y"), message )

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
		if 'sensor' in arguments and arguments[u'sensor'] in self.sensors_list:
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
		# Only log data if we have data logging enabled.
		for k,s in self.sensors_list.iteritems():
			s.poll()
		database_connection.commit()

	def ups_power_lost(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log( "UPS power lost!" )
				self.operations = []
				self.operations.append( EmergencyShutdown(self.PID_controller) )
			else:
				self.print_log( "Illegal password sent for UPS shutdown." )
		else:
			self.print_log( "UPS shutdown attempted with no password." )

	# When the program starts up, by default it DOES take 
	# data. You have to enable data collection using the form
	# on the webpage, which requires a password.
	def set_data_logging_state(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				if 'state' in arguments:
					self.print_log( "Data logging set to: %s" % arguments['state'] )
					if arguments['state'] == True:
						self.log_data = True
						for k,s in self.sensors_list.iteritems():
							s.record_data = True
					else:
						self.log_data = False
						for k,s in self.sensors_list.iteritems():
							s.record_data = False
					return { "success": True }
				else:
					self.print_log( "Data logging state change attempted with no state." )
			else:
				self.print_log( "Illegal password sent for data logging state change." )
		else:
			self.print_log( "Data logging state change attempted with no password." )

	def get_data_logging_state(self, arguments):
		return { 'state': self.log_data }

	# When the program starts up, by deafult cycles are not scheduled
	def set_cycle_scheduling_state(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				if 'state' in arguments:
					self.print_log( "Cycle scheduling set to: %s" % arguments['state'] )
					if arguments['state'] == True:
						self.schedule_cycles = True
					else:
						self.schedule_cycles = False
					return { "success": True }
				else:
					self.print_log( "Cycle scheduling state change attempted with no state." )
			else:
				self.print_log( "Illegal password sent for cycle scheduling state change." )
		else:
			self.print_log( "Cycle scheduling state change attempted with no password." )

	def get_cycle_scheduling_state(self, arguments):
		return { 'state': self.schedule_cycles }

	# When the program starts up, by deafult the scheduled cycles will not run on weekends
	#def set_weekend_cycle_state(self, arguments):
	#	if 'password' in arguments:
	#		if arguments['password'] == self.password:
	#			if 'state' in arguments:
	#				self.print_log( "weekend scheduling set to: %s" % arguments['state'] )
	#				if arguments['state'] == True:
	#					self.sched_run_on_weekend = True
	#				else:
	#					self.sched_run_on_weekend = False
	#				return { "success": True }
	#			else:
	#				self.print_log( "Weekend scheduling state change attempted with no state." )
	#		else:
	#			self.print_log( "Illegal password sent for weekend scheduling state change." )
	#	else:
	#		self.print_log( "Weekend scheduling state change attempted with no password." )

	#def get_weekend_cycle_state(self, arguments):
	#	return { 'state': self.sched_run_on_weekend }
	
	def shutdown_server(self, arguments):
		if 'password' in arguments:
			if arguments['password'] == self.password:
				self.print_log( "Server shutting down!" )
				os._exit(0);
			else:
				self.print_log( "Illegal password sent for shutdown_server command." )
		else:
			self.print_log( "Server shutdown attempted with no password." )

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
				print "Error: invalid command sent to delegate."
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
		index = 1
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
