from generic_operation import *
from cryo_delegate import *

class MagUpOperation(GenericOperation):
	def __init__(self, mag_up_time, final_current, PID_interface, current_sensor): 
		self.mag_up_time 	= mag_up_time
		self.final_current 	= final_current
		self.PID_interface 	= PID_interface
		self.current_sensor	= current_sensor

		# Set the safety settings.
		self.absolute_max_current 		= 18.5 # amperes
		self.absolute_min_mag_up_time 	= 15*60 # seconds
		self.absolute_max_step_size 	= 0.010 # 10 mA.
		self.ramping_rate 				= 0

		super(MagUpOperation, self).__init()

	# When the MagUpOperation begins, we'll do a bunch of checks to ensure that everything is in order.
	def started(self):
		# Check the mag_up_time, in case it's too short.
		if self.mag_up_time < self.absolute_min_mag_up_time:
			self.yield = True
			print "The specified mag_up_time is dangerously short. Terminating MagUp operation."
			return

		# Check the absolute max current, to make sure it's not crazy high.
		if self.final_current > self.absolute_max_current:
			self.yield = True
			print "The specified MagUp current is is dangerously high. Terminating MagUp operation."

		# Verify the PID connection.
		if not self.PID_interface.verify_connection():
			self.yield = True
			print "PID interface connection could not be verified. Terminating MagUp operation."
			return

		# Double-check that the current is sensible.
		current = self.current_sensor.get_data()
		if isinstance(current['current'],basestring):
			# The current is not sensible.
			self.yield = True
			print "The current cannot be read, indicating an error. Terminating MagUp operation."
			return

		# Make sure that we're below the final current.
		if current['current'] > final_current:
			self.yield = True
			print "The current is already over the specified current."

		# Okay, we're pretty much ready to start the operation. The first step
		# is to establish the target rate of ramping.
		self.ramping_rate = (self.final_current - current['current']) / ( self.mag_up_time )

		# Set the PID controller to manual mode.
		self.PID_interface.set_manual_mode()

	def tick(self):
		# Don't run the operation if yield is called. There are already
		# some other checks for this, but here's another.
		if self.yield:
			return