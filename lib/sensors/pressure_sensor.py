# import random, serial, serial_dummy, re
# from cryo_delegate import *

import random, serial, re, serial_dummy
from dataconduits import GenericDataConduit, GenericCryoDataModel

class PressureSensorConduit(GenericDataConduit):
	def __init__(self, interface_number):
		# Try to connect to the relevant serial port.
		try:
			self.serial_connection = serial.Serial('/dev/PRESSURE_SENSOR', 9600, timeout=0.2)
		except Exception:
			print("There was a problem connecting to the serial port constructor of: %s" % self.__class__.__name__)
			self.serial_connection = serial_dummy.SerialDummy()

		self.name = "Generic Temperature Sensor #%d" % interface_number
		self.units = "Torr"
		self.fields = [ 'pressure' ]
		self.cold_cathode_max_pressure = 5e-5 # torr.
		# It is necessary to configure the unit to use air as the pressure sensing medium. 
		# Otherwise it is calibrated for nitrogen, which leads to incorrect measurements.
		# Refer to page 23 of the manual.
		# self.serial_connection.write("@254GT!AIR;FF;")
		self.serial_connection.write(b"@254GT!AIR;FF;")
		# Clear the buffer out.
		self.serial_connection.read(100)

	# This pressure sensor is a 972 DualMag Cold Cathode/MicroPirani Vacuum Transducer
	def get_data(self, cold_cathode=False):
		error = False
		# Clear out the buffer.
		try:
			if cold_cathode == True:
				# self.serial_connection.write("@254PR2?;FF")
				self.serial_connection.write(b"@254PR2?;FF")
			else:
				# self.serial_connection.write("@254PR1?;FF")
				self.serial_connection.write(b"@254PR1?;FF")
		except Exception:
			error = "Unable to establish serial connection with device."
			return { 'pressure': 'unknown', 'error':error, 'units': 'torr' }
		# Read 100 bytes (the response is always less than that) or until the end of the buffer.
		response = self.serial_connection.read(100)
		# Match the resulting string to the following. The result should look like this:
		# for example, "@253ACK9.00E+2;FF" means 9.00e2 Torr.
		# m = re.match('@253ACK([0-9]*.[0-9]*)E([\+\-][0-9]*);FF',response)
		# if m: # if the match works...
		# 	pressure = float(m.group(1)) * (10 ** float(m.group(2)))
		m = re.match(rb'@253ACK([0-9]*\.[0-9]*)E([+\-][0-9]*);FF', response)
		if m:
			pressure = float(m.group(1).decode('utf-8')) * (10 ** float(m.group(2).decode('utf-8')))
			# Now we have to decide whether we are in the right pressure range for the measurement. If not,
			# we'll need to change to cold cathode mode.
			if cold_cathode == False and pressure < self.cold_cathode_max_pressure:
				return self.get_data(True)
			else:
				return { 'pressure': pressure, 'units': 'torr' }
		else: 
			# error = "Invalid response from device: '%s'." % response
			error = "Invalid response from device: '%s'." % response.hex()
			return { 'pressure': 'unknown', 'error':error, 'units': 'torr' }

class GenericPressureSensor(GenericCryoDataModel):
	def __init__(self, interface_number): 
		self.interface_number = interface_number
		self.name 			= "Generic Pressure Sensor #%d" % self.interface_number
		self.database_name 	= "pressure_sensor_%d" % self.interface_number
		self.conduit 		= PressureSensorConduit(self.interface_number)
		self.units 			= self.conduit.units
		
		# GenericCryoDataModel.__init__(self, self.name)
		super().__init__(self.name)
