from generic_operation import *
from cryo_delegate import *

# The ChangeRegulationOperation changes the regulation setpoint. It only works
# when the system is already in regulation mode.

class ChangeRegulationOperation(GenericOperation):
	def __init__(self, regulation_temperature, PID_interface, use_slow_ramp=False):
		self.PID_instance = PID_interface

		# Set all the safety settings.
		self.max_start_current		= 0.020  # 20 mA can be safely switched.
		self.max_FAA_temperature	= 2  # max allowable temperature to begin regulation
		if use_slow_ramp:
			self.ramping_rate	= 0.0001  # ramping rate for R(T) measurements
		else:
			self.ramping_rate	= 0.002  # 2 mK/s; 0.0001 is the minimum that still works
		self.max_step			= 0.004  # 2 mK is the max step.
		self.regulation_temperature = regulation_temperature

		super().__init__()  # Python 3: no need to pass class and self
		self.has_started_message = True
		self.started_message = "Changing regulation setpoint to %0.0f mK." % (regulation_temperature * 1000)

	def started(self):
		if not self.PID_instance.verify_connection():
			self.print_log("Unable to connect to the PID controller.")
			self.finished = True
			return

		if not self.PID_instance.is_in_PID_mode():
			self.finished = True
			self.print_log("The PID controller not in PID mode. Can't change regulation setpoint unless already in regulation. Start regulation first.")
			return

	def tick(self, dt):
		setpoint = self.PID_instance.get_setpoint()
		if self.regulation_temperature > setpoint:
			direction = 1
		else:
			direction = -1

		# Determine the appropriate step size to take.
		step = self.ramping_rate * dt * direction
		# Ensure that the step size doesn't get too big.
		if abs(step) > self.max_step:
			step = self.max_step * direction

		# If the setpoint is negligibly close, set it exactly and clean up.
		if abs(setpoint - self.regulation_temperature) < step:
			self.PID_instance.set_setpoint(self.regulation_temperature)
			self.finished = True
			self.success = True
			self.print_log("here")
			return

		# Take a step.
		self.PID_instance.set_setpoint(setpoint + step)
		self.print_log("taking a temp that is {:4.5f} mK large and current setpoint is {:4.5f}, dt = {:1.1f}".format(
			step * 1000, setpoint * 1000, dt))