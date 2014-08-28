import random, serial, serial_dummy, time
from cryo_delegate import *

class PIDControllerInterface(object):
	def __init__(self):
		self.name 	= "SIM960 Process Controller"
		self.units 	= "Amperes"

		# The maximum allowable manual output step:
		self.max_manual_output_step = 0.003
		# The expected circuit resistance is 25 ohm.
		self.anticipated_circuit_resistance = 0.15

		try:
			self.serial_connection = serial.Serial('/dev/SRS_MAINFRAME', 9600, timeout=0.1)
		except Exception:
			print "There was a problem connecting to the serial port constructor of: %s" % self.__class__.__name__
			self.serial_connection = serial_dummy.SerialDummy()

	# Connect to the SIM960 and verify that the connection is valid. Return
	# True or False depending on the connection status.
	def verify_connection(self):
		# Set up the system so it is connected to the right machine.
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 3, 'disconnect'\r")
			self.serial_connection.read(100)
			self.serial_connection.write("*IDN?\r")
			result = self.serial_connection.read(100)
			if result[0:32] == "Stanford_Research_Systems,SIM960":
				# I guess everything worked correctly. Let's clean up now.
				self.serial_connection.write("disconnect\r")
				return True
			else:
				# I guess everything worked correctly. Let's clean up now.
				self.serial_connection.write("disconnect\r")
				print "Failed to verify connection with SIM960."
				return False

		except Exception:
			return False

		return False

	def copy_pid_output_to_manual_output(self):
		if self.is_in_PID_mode() == False:
			print "Unable to copy PID output to manual when already in manual mode."
			return False
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 3, 'disconnect'\r")
			self.serial_connection.read(100)
			# Set the controller to MANUAL mode (z = 0), refer to SIM960 manual p.38
			self.serial_connection.write("OMON?\r")
			result = float( self.serial_connection.read(100) )
			self.serial_connection.write("MOUT %+2.3f\r" % result)

		except Exception as e:
			print e
			return False

		return False

	# This function tries to decide whether the system is currently in PID
	# mode, or manual output mode.
	def is_in_PID_mode(self):
		self.serial_connection.write("disconnect\r")
		self.serial_connection.write("CONN 3, 'disconnect'\r")
		self.serial_connection.read(100)
		# Now verify the controller setting.
		self.serial_connection.write("AMAN?\r")
		result = self.serial_connection.read(100)		
		# If Z = 1, the system is in PID/regulation mode. Else: manual.
		if result == "1\r\n":
			return True
		else:
			return False

	# Set the internal setpoint value for the PID controller.
	def set_setpoint(self, setpoint_in_kelvin):
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 3, 'disconnect'\r")
			self.serial_connection.read(100)
			# Now set the internal setpoint.
			self.serial_connection.write("SETP %+2.3f\r" % setpoint_in_kelvin)

		except Exception as e:
			print e
			return False

		return False

	def get_setpoint(self):
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 3, 'disconnect'\r")
			self.serial_connection.read(100)
			# We'll check the manual output.
			self.serial_connection.write("SETP?\r")
			result = float(self.serial_connection.read(100))
			return result

		except Exception as e:
			print e
			return False

		return False
		
	# Put the PID controller into manual mode.
	def set_manual_mode(self):
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 3, 'disconnect'\r")
			self.serial_connection.read(100)
			# Set the controller to MANUAL mode (z = 0), refer to SIM960 manual p.38
			self.serial_connection.write("AMAN 0\r")
			self.serial_connection.read(100)
			# Now verify the controller setting.
			self.serial_connection.write("AMAN?\r")
			result = self.serial_connection.read(100)		

			if result == "0\r\n":
				return True
			else:
				raise Exception("I can't change the mode of the PID controller, for some reason.")

		except Exception as e:
			print e
			return False

		return False

	# Set regulation mode.
	def set_regulation_mode(self):
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 3, 'disconnect'\r")
			self.serial_connection.read(100)
			# Set the controller to PID mode (z = 1), refer to SIM960 manual p.38
			self.serial_connection.write("AMAN 1\r")
			self.serial_connection.read(100)
			# Now verify the controller setting.
			self.serial_connection.write("AMAN?\r")
			result = self.serial_connection.read(100)		

			if result == "1\r\n":
				return True
			else:
				raise Exception("I can't change the mode of the PID controller, for some reason.")

		except Exception:
			return False

		return False

	# Set the current. Actually, you're setting a voltage, but through a resistance
	# model, you can get the current back.
	def set_manual_output_voltage(self, voltage):
		try:
			print "Set voltage -> %s" % voltage
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 3, 'disconnect'\r")
			self.serial_connection.read(100)
			# We'll check the manual output differential.
			self.serial_connection.write("MOUT?\r")
			result = float(self.serial_connection.read(100))
			if abs(voltage - result) > self.max_manual_output_step:
				raise Exception("The requested manual output is too large. voltage = %s, step = %s" % (voltage, (voltage - result) ))
			else:
				# Ready to set the voltage. The format is, e.g.: "MOUT +3.123"
				self.serial_connection.write("MOUT %+2.3f\r" % voltage)
				return True

		except Exception as e:
			print e
			return False

		return False

	# Get the current output value on the manual circuit.
	def get_manual_output(self):
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 3, 'disconnect'\r")
			self.serial_connection.read(100)
			# We'll check the manual output.
			self.serial_connection.write("MOUT?\r")
			result = float(self.serial_connection.read(100))
			return result

		except Exception as e:
			print e
			return False

		return False

	# This model decides the relationship between PID voltage and current,
	# essentially by calculating the resistance of the circuit.
	def current_voltage_model(self, current):
		# Experimental test: while in voltage-controlled mode, 
		# 1.000 V on the PID -> 1.877 V on the output of the power supply.
		return (current * self.anticipated_circuit_resistance) / 1.877

	def voltage_current_model(self, voltage):
		# Experimental test: while in voltage-controlled mode, 
		# 1.000 V on the PID -> 1.877 V on the output of the power supply.
		return (voltage / self.anticipated_circuit_resistance) * 1.877

	# Set the output current (indirectly, via voltage). Returns true if
	# the operation is successful. 
	def set_current(self, current):
		# We can't actually set the current directly, so we must rely on a
		# current output model.
		print "Set current -> %s" % current
		voltage = self.current_voltage_model( current )

		return self.set_manual_output_voltage( voltage )
