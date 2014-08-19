# The emergency shutdown operation is called when 
# the system is operating a thigh magnetic field and
# power cuts out.

from generic_operation import *
from cryo_delegate import *

class EmergencyShutdown(GenericOperation):
	def __init__(self, PID_interface):
		self.PID_instance = PID_interface
		self.shutdown_time = 7*60 # We think that shutdown in 7 minutes is safe
		# when operating from a full-battery UPS.
		self.demagnetization_rate = 0

		super(EmergencyShutdown, self).__init__()

		self.has_started_message = True
		self.started_message = "Emergency demagnetization started."

	def started(self):
		# If we can't talk to the PID controller,
		# hopefully that means that the field is zero. Otherwise, we
		# might be fucked. Either way: keep trying to issue commands in vain.
		if not self.PID_instance.verify_connection():
			self.print_log( "Unable to connect to the PID controller." )

		# If we're in PID mode, we just need to switch to manual to ramp down.
		if self.PID_instance.is_in_PID_mode():
			self.PID_instance.copy_pid_output_to_manual_output()

		# Double-check that we're in manual mode.
		self.PID_instance.set_manual_mode()

		# Get the current output value.
		output = self.PID_instance.get_manual_output()

		self.start_output = output
		self.demagnetization_rate = output / self.shutdown_time

	def tick(self, dt):
		# Here, we're just going to ignore all safety checks and
		# just power through it. The current output should be 
		elapsed_time = time.time() - self.start_time
		self.PID_instance.set_dangerous_manual_output_voltage( self.start_output - (self.start_output)*(elapsed_time / self.shutdown_time) )

		if elapsed_time > self.shutdown_time:
			self.PID_instance.set_dangerous_manual_output_voltage( 0 )
			self.finished = True
			self.success = True