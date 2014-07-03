from generic_operation import *
from cryo_delegate import *

class MagDownOperation(GenericOperation):
	def __init__(self, mag_down_time, PID_interface, current_sensor): 
		self.mag_down_time 	= mag_down_time
		self.final_current 	= 0
		self.PID_interface 	= PID_interface
		self.current_sensor	= current_sensor

		# Set the safety settings.
		self.absolute_min_mag_down_time = 10 # seconds
		self.absolute_max_step_size 	= 0.010 # 10 mA.
		self.ramping_rate 				= 0

		super(MagDownOperation, self).__init__()

	# When the MagDownOperation begins, we'll do a bunch of checks to ensure that everything is in order.
	def started(self):
		# Check the mag_down_time, in case it's too short.
		if self.mag_down_time < self.absolute_min_mag_down_time:
			self.finished = True
			print "The specified mag_down_time is dangerously short. Terminating MagDown operation."
			return

		# Verify the PID connection.
		if not self.PID_interface.verify_connection():
			self.finished = True
			print "PID interface connection could not be verified. Terminating MagDown operation."
			return

		# Double-check that the current is sensible.
		current = self.current_sensor.get_data()
		if isinstance(current['current'],basestring):
			# The current is not sensible.
			self.finished = True
			print "The current cannot be read, indicating an error. Terminating MagDown operation."
			return

		# Make sure that we're below the final current.
		if current['current'] < self.final_current:
			self.finished = True
			print "The current is already below the specified current."

		voltage = self.PID_interface.get_manual_output()
		self.expected_output_current = self.PID_interface.voltage_current_model( voltage )

		# Okay, we're pretty much ready to start the operation. The first step
		# is to establish the target rate of ramping.
		self.ramping_rate = abs( (self.final_current - self.expected_output_current) / ( self.mag_down_time ) )

		# Set the PID controller to manual mode.
		self.PID_interface.set_manual_mode()

	def ended(self):
		# Attempt to zero out the final current. 
		#self.PID_interface.set_current(0)
		pass

	def tick(self, dt):
		# Don't run the operation if yield is called. There are already
		# some other checks for this, but here's another.
		if self.finished:
			return

		# Measure the current data, and double-check that the current is sensible.
		current = self.current_sensor.get_data()
		if isinstance(current['current'],basestring):
			# The current is not sensible.
			self.finished = True
			print "The current cannot be read, indicating an error. Terminating MagDown operation."
			return

		# Every 5 steps, check the validity of the current->voltage model.
		if self.step_index % 5 == 4:
			voltage = self.PID_interface.get_manual_output()
			if voltage is False:
				self.finished = True
				print "The PID output voltage could not be read."

			expected_voltage = self.PID_interface.current_voltage_model( current['current'] )
			# Check the validity. We either need the difference to be below
			# 100 mV or within a factor of two of the model.
			if abs( voltage - expected_voltage ) > 0.1 and abs(voltage - expected_voltage)/(voltage + expected_voltage) > 0.5:
				self.finished = True
				print "The PID output current-voltage model failed. Expected voltage %s, measured voltage %s." % (expected_voltage, voltage)			

		# Figure out the ramping step. Upper limit: max ramp step.
		ramping_step = min( abs(self.ramping_rate * dt), abs(self.absolute_max_step_size))
		if ramping_step == self.absolute_max_step_size:
			print "Step size hit maximum limit."

		# Make sure that we're below the final current.
		if current['current'] <= self.final_current or self.expected_output_current < self.final_current:
			self.finished = True
			print "The current is over the specified current."

		self.expected_output_current -= ramping_step
		self.PID_interface.set_current( self.expected_output_current )