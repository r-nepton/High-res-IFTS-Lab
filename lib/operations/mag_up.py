from generic_operation import *
from cryo_delegate import *

class MagUpOperation(GenericOperation):
	def __init__(self, mag_up_time, final_current, temperature_FAA_sensor, temperature_3K_sensor, PID_interface, current_sensor, breakout_board, back_emf_sensor): 
		
		self.mag_up_time 			= mag_up_time
		self.final_current 			= final_current
		self.PID_interface 			= PID_interface
		self.current_sensor			= current_sensor.conduit
		self.temperature_FAA_sensor = temperature_FAA_sensor.conduit
		self.temperature_3K_sensor 	= temperature_3K_sensor.conduit
		self.breakout_board			= breakout_board.conduit
		self.back_emf_sensor			= back_emf_sensor.conduit

		# Set the safety settings.
		self.absolute_max_current 		= 18.5 # amperes  (max current, from HPD's manual)
		self.absolute_min_mag_up_time 	= 3*60 # seconds (because a magnetization that's too fast could be dangerous)
		self.absolute_max_step_size 	= 0.200 # 200 mA.
		self.ramping_rate 				= 0
		self.max_FAA_temperature 		= 5 # kelvin
		self.ultimate_max_FAA_temperature = 6 # kelvin

		self.heat_switch_open			= True

		super(MagUpOperation, self).__init__()

		self.has_started_message = True
		self.started_message = "Starting magnetization."

	# When the MagUpOperation begins, we'll do a bunch of checks to ensure that everything is in order.
	def started(self):
		# Check the mag_up_time, in case it's too short.
		if self.mag_up_time < self.absolute_min_mag_up_time:
			self.finished = True
			self.print_log( "The specified mag_up_time is dangerously short. Terminating MagUp operation." )
			return

		# Check the absolute max current, to make sure it's not crazy high.
		if self.final_current > self.absolute_max_current:
			self.finished = True
			self.print_log( "The specified MagUp current is is dangerously high. Terminating MagUp operation." )

		# Verify the PID connection.
		if not self.PID_interface.verify_connection():
			self.finished = True
			self.print_log( "PID interface connection could not be verified. Terminating MagUp operation." )
			return

		# Double-check that the current is sensible.
		current = self.current_sensor.get_data()
		if isinstance(current['current'],basestring):
			# The current is not sensible.
			self.finished = True
			self.print_log( "The current cannot be read, indicating an error. Terminating MagUp operation." )
			return

		# Make sure that we're below the final current.
		if current['current'] > self.final_current:
			self.finished = True
			self.print_log( "The current is already over the specified current." )

		voltage = self.PID_interface.get_manual_output()

		self.expected_output_current = self.PID_interface.voltage_current_model( voltage )

		# Okay, we're pretty much ready to start the operation. The first step
		# is to establish the target rate of ramping.
		self.ramping_rate = (self.final_current - current['current']) / ( self.mag_up_time )

		# Set the PID controller to manual mode.
		self.PID_interface.set_manual_mode()

	def tick(self, dt):
		# Don't run the operation if finished is true. There are already
		# some other checks for this, but here's another.
		if self.finished:
			return

		# Measure the current data, and double-check that the current is sensible.
		current = self.current_sensor.get_data()
		if isinstance(current['current'],basestring):
			# The current is not sensible.
			self.finished = True
			self.print_log( "The current cannot be read, indicating an error. Terminating MagUp operation." )
			return

		# Measure the back emf
		back_emf = self.back_emf_sensor.get_data()

		# Every 5 steps, check the validity of the current->voltage model, and also see if we need to close the heat
		# switch.
		if self.step_index % 5 == 4:
			voltage = self.PID_interface.get_manual_output()
			if voltage is False:
				self.finished = True
				self.print_log( "The PID output voltage could not be read." )

			expected_voltage = self.PID_interface.current_voltage_model( current['current'] )
			# Check the validity. We either need the difference to be below
			# 100 mV or within a factor of two of the model.
			if abs( voltage - expected_voltage ) > 0.1 and abs(voltage - expected_voltage)/(voltage + expected_voltage) > 0.5:
				self.print_log( "The PID output current-voltage model failed. Expected voltage %s, measured voltage %s." % (expected_voltage, voltage) )

			# Check the heat switch. If the FAA temperature is near the base temperature, we can flip the switch.
			temperature_3K = self.temperature_3K_sensor.get_data()
			temperature_FAA = self.temperature_FAA_sensor.get_data()
			if self.heat_switch_open == True and (temperature_FAA['temperature'] > temperature_3K['temperature'] or temperature_FAA['temperature'] > self.max_FAA_temperature):
				# The temperature of the FAA is getting a bit too high.
				# Now, close the heat switch.
				self.breakout_board.close_heat_switch()
				self.heat_switch_open = False

			# Double check to make sure that the FAA is not burning out.
			if temperature_FAA['temperature'] > self.ultimate_max_FAA_temperature:
				self.finished = True
				self.print_log( "The FAA temperature exceeded the ultimate max threshold. Stopping mag-up." )
				return

		# Figure out the ramping step. Upper limit: max ramp step.
		ramping_step = min( self.ramping_rate * dt, self.absolute_max_step_size )
		if ramping_step == self.absolute_max_step_size:
			print "Step size hit maximum limit."

		# Check to see if we're above the final current.
		if current['current'] >= self.final_current or self.expected_output_current > self.final_current:
			self.finished 	= True
			self.success 	= True
			self.print_log( "The current is over the specified current. Magnetization completed." )
		else:
			#Check that the back emf is not above 100mV
			if back_emf['voltage'] > 0.1:
				self.PID_interface.set_current( self.expected_output_current )
				print "Magnet back EMF is too high, waiting for decrease"
			else:
				self.expected_output_current += ramping_step
				self.PID_interface.set_current( self.expected_output_current )
