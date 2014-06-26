import random, serial, serial_dummy, time
from cryo_delegate import *

class PIDControllerSensorConduit(GenericDataConduit):
	def __init__(self):
		self.name 	= "SIM960 Process Controller"
		self.units 	= "Amperes"

	# Connect to the SIM960 and verify that the connection is valid. Return
	# True or False depending on the connection status.
	def verify_connection(self):
		pass

	# Put the PID controller into manual mode.
	def set_manual_mode(self):
		# Refer to page 40 of the HPD104 manual.
		# 1. Transfer the PID output to the manual output, if necessary.
		# 2. Switch the output setting of the controller -> Manual
		# 3. Drive the current to zero in accordance with the manual demagnetization procedure
		# 4. Wait for the user to indicate that the mag cycle switch has been switched.
		pass

	# Set regulation mode.
	def set_regulation_mode(self):
		pass

	# Set the current. Actually, you're setting a voltage, but through a resistance
	# model, you can get the current back.
	def set_current(self, current):
		pass

	# Measure voltage output, mode, settings, who knows.
	def get_data(self):
		return {}