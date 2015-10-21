from generic_operation import *
from cryo_delegate import *

class BeginRegulationOperation(GenericOperation):
	def __init__(self, regulation_temperature, PID_interface, current_sensor, temperature_FAA_sensor, breakout_board, back_emf_sensor): 
		self.temperature_FAA_sensor = temperature_FAA_sensor.conduit
		self.breakout_board			= breakout_board.conduit
		self.PID_instance 			= PID_interface
		self.current_sensor			= current_sensor.conduit
		self.regulation_temperature = regulation_temperature
		self.back_emf_sensor			= back_emf_sensor.conduit

		# Set all the safety settings.
		self.max_start_current 		= 0.020 # 20 mA can be safely switched.
		self.max_FAA_temperature 	= 2 # max allowable temperature to begin regulation
		self.ramping_rate			= 0.002 # 2 mK per second ramping rate.
		self.max_step				= 0.004 # 2 mK is the max step.

		super(BeginRegulationOperation, self).__init__()

		self.has_started_message = True
		self.started_message = "Preparing for regulation cycle."

	# In case an external thing wants to update the regulation temperature.
	def update_regulation_temperature(self, regulation_temperature):
		# But don't update the regulation setpoint if we are already
		# started.
		if self.step_index == 0:
			self.regulation_temperature = regulation_temperature

	def started(self):
		# Verify the PID connection.
		if not self.PID_instance.verify_connection():
			self.print_log( "Unable to connect to the PID controller." )
			self.finished = True 
			return

		# Verify the current.
		current = self.current_sensor.get_data()
		if isinstance(current['current'],basestring):
			# The current is not sensible.
			self.finished = True
			self.print_log( "The current cannot be read, indicating an error. Terminating operation." )
			return

		if current['current'] > self.max_start_current:
			self.finished = True
			self.print_log( "The current was too high to begin regulation (%s)" % current['current'] )
			return

		if self.PID_instance.is_in_PID_mode():
			self.finished = True
			self.print_log( "The PID controller is already in PID mode, which is confusing. Can't begin regulation if already in regulation. Quitting now." )
			return

		# Okay, the current is zero. It is safe to switch to regulation mode.
		self.breakout_board.switch_to_regulation_cycle()

		# Now we'll measure the temperature of the FAA.
		FAA_temperature = self.temperature_FAA_sensor.get_data()
		if isinstance(FAA_temperature['temperature'],basestring):
			# The temperature is not sensible.
			self.finished = True
			self.print_log( "The FAA temperature could not be read, aborting transition to regulation." )
			return

		# Check to make sure the FAA temperature is low enough.
		if FAA_temperature['temperature'] > self.max_FAA_temperature and FAA_temperature['temperature'] > self.regulation_temperature:
			# The temperature is too high.
			self.finished = True
			self.print_log( "The FAA temperature is too high, aborting transition to regulation." )
			return

		# Okay, the temperature is sensible. Now let's set the PID setpoint
		# to match the FAA temperature.
		self.PID_instance.set_setpoint(FAA_temperature['temperature'])

		# Okay, finally we can switch to PID mode.
		self.PID_instance.set_regulation_mode()

		# Now the next step is to slowly increment the setpoint over time. This is
		# spread out over a long time.

	def tick(self, dt):
		# Double check to make sure we're not done.
		if self.finished:
			return

		# Measure back emf, this shouldn't be an issue in regulation mode
		back_emf = self.back_emf_sensor.get_data()

		setpoint = self.PID_instance.get_setpoint()
		# If the setpoint is negligibly close, let's just
		# set it exactly and clean up.
		if setpoint - self.regulation_temperature > 0.001:
			self.PID_instance.set_setpoint( self.regulation_temperature )
			self.finished 	= True
			# Operation successful.
			self.success	= True
			return
		
		# Determine the appropriate step size to take.
		step = self.ramping_rate * dt
		# Ensure that the step size doesn't get too big.
		if step > self.max_step:
			step = self.max_step

		# Check that the back emf is within (+-)90mV
		if abs(back_emf) > 0.09:
			self.PID_instance.set_setpoint( setpoint)
		else:
			# Take a step.
			self.PID_instance.set_setpoint( setpoint + step )
