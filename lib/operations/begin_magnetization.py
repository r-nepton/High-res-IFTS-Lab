from generic_operation import *
from cryo_delegate import *

# The BeginMagnetizationOperation operation takes a cryostat which has
# just finished a cooldown, or just finished a regulation cycle, and
# prepares it to perform a magnetization cycle. When it completes successfully,
# the next step is to perform a ramp-up to full field.
class BeginMagnetizationOperation(GenericOperation):
	def __init__(self, PID_interface, temperature_3K_sensor, temperature_FAA_sensor, breakout_board): 
		self.temperature_3K_sensor 	= temperature_3K_sensor.conduit
		self.temperature_FAA_sensor = temperature_FAA_sensor.conduit
		self.breakout_board			= breakout_board.conduit
		self.PID_instance 			= PID_interface

		# Set all the safety settings.
		self.max_3K_stage_temperature = 4 # Upper limit of 3 K stage temperature
		self.max_FAA_temperature 	  = 4 # Upper limit of the FAA temperature
		self.heat_switch_open		  = True
		self.max_step 				  = 0.005 # in Kelvin
		self.step_rate				  = 0.002 # in Kelvin/second

		super(BeginMagnetizationOperation, self).__init__()

		self.has_started_message = True
		self.started_message = "Preparing for magnetization cycle."

	# Perform initial checks for the operation.
	def started(self):
		# Verify the PID connection.
		if not self.PID_instance.verify_connection():
			self.print_log( "Unable to connect to the PID controller." )
			self.finished = True 
			return

		# Verify the stage temperatures.
		temperature_3K = self.temperature_3K_sensor.get_data()
		if temperature_3K['temperature'] > self.max_3K_stage_temperature:
			self.print_log( "The 3 K stage temperature is too high! (%s K)" %  temperature_3K['temperature'] )
			self.finished = True
			return

		# Verify the FAA temperature.
		temperature_FAA = self.temperature_FAA_sensor.get_data()
		if temperature_FAA['temperature'] > self.max_FAA_temperature:
			self.print_log( "The FAA temperature is too high! (%s K)" %  temperature_FAA['temperature'] )
			self.finished = True
			return

		# Okay, well I think that the temperatures and all that are good. Now,
		# we'll open the heat switch.
		self.breakout_board.open_heat_switch()
		self.heat_switch_open = True

		# If the system was in PID mode, we'll need to switch into 
		# manual mode right now. In order to prevent jumps during
		# the switch, we'll copy the current PID output to manual mode
		# before switching.
		if self.PID_instance.is_in_PID_mode():
			self.PID_instance.copy_pid_output_to_manual_output()
		
		# Switch to manual mode.
		self.PID_instance.set_manual_mode()

		# The next step is to step the voltage to zero. It is necessary to do this slowly.
		# This will be handled by the ticking.

	def tick(self, dt):
		# Double check to make sure we're not done.
		if self.finished:
			return

		# Check to see if the FAA temperature is above the stage temperature.
		temperature_3K = self.temperature_3K_sensor.get_data()
		temperature_FAA = self.temperature_FAA_sensor.get_data()
		
		if self.heat_switch_open == True:
			# If the stage temperature and 3 K stage temperature have equalized, 
			# we'll close the heat switch.
			if temperature_3K['temperature'] > temperature_FAA['temperature']:
				self.breakout_board.close_heat_switch()
				self.heat_switch_open = False

		# Now we'll ramp down the manual PID output to zero.
		current_output = self.PID_instance.get_manual_output()

		# A good rampdown rate is 2 mV per second.
		step = self.step_rate * dt
		if step > self.max_step: 
			step = self.max_step

		if current_output - step < 0:
			# Wrap everything up:
			self.PID_instance.set_manual_output_voltage( 0 )
			# Engage the magnetization cycle switch.
			self.breakout_board.switch_to_magnetization_cycle()
			self.finished = True
			# The operation completed without errors.
			self.success = True
		else: 
			# Ramp down the output voltage.
			self.PID_instance.set_manual_output_voltage( current_output - step )