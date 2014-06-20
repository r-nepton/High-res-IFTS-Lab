import random, serial, time
from cryo_delegate import *

# The temperature sensor reads the diode temperatures from the SIM922.
# The four channels are laid out on page 45 of the HPD104 operating manual.
class DiodeTemperatureSensorConduit(GenericDataConduit):
	def __init__(self, interface_number):
		self.name = "SIM922 Silicon Diode Temperature Sensor #%d" % interface_number
		self.units = "Kelvin"
		self.serial_connection = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5)
		self.SIM922_port = interface_number

	def get_data(self):
		# Set up the system so it is connected to the right machine.
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 5, 'disconnect'\r")
			self.serial_connection.read(100)
			self.serial_connection.write("TVAL? %d\r" % self.SIM922_port)
		except Exception:
			return { 'temperature':'unknown', 'error': 'Unable to connect to SIM922.', 'units': 'kelvin' }
		
		# Okay, we've configured the unit correctly. Now let's query for our data.
		try: 
			response = self.serial_connection.read(100);
			temperature = float(response)
		except Exception:
			return { 'temperature':'unknown', 'error': 'Could not convert response "%s" to temperature' % response, 'units':'kelvin' }

		# I guess everything worked correctly. Let's clean up now.
		self.serial_connection.write("disconnect\r")

		# Send out the measured temperature.
		return { 'temperature':temperature, 'units':'kelvin' }

class RuOxTemperatureSensorConduit(GenericDataConduit):
	def __init__(self, interface_number):
		self.name = "SIM921 Ruthenium Oxide Temperature Sensor #%d" % interface_number
		self.units = "Kelvin"
		self.serial_connection = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5)
		self.SIM925_port = interface_number

	def get_data(self):
		# Set up the system so it is connected to the right machine.
		try:
			self.serial_connection.write("disconnect\r")
			# First, connect to the octal multiplexer and set the channel.
			#self.serial_connection.write("CONN 6, 'disconnect'\r")
			#self.serial_connection.write("CHAN %d\r" % self.SIM925_port)
			# The channel switching time is 50 ms. Delay to ensure correct switch.
			#time.sleep(0.05)
			# Now disconnect from the mux and connect to the bridge reader.
			#self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 1, 'disconnect'\r")
			# Clear out the buffer.
			self.serial_connection.read(2000)
			self.serial_connection.write("TVAL?\r")
		except Exception:
			return { 'temperature':'unknown', 'error': 'Unable to connect to SIM921.', 'units': 'kelvin' }
		
		# Okay, we've configured the unit correctly. Now let's query for our data.
		try: 
			response = self.serial_connection.read(100);
			temperature = float(response)
		except Exception:
			return { 'temperature':'unknown', 'error': 'Could not convert response "%s" to temperature' % response, 'units':'kelvin' }

		# I guess everything worked correctly. Let's clean up now.
		self.serial_connection.write("disconnect\r")

		# Send out the measured temperature.
		return { 'temperature':temperature, 'units':'kelvin' }

class PulseTubeFirstStageTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Pulse Tube Stage #1 Temperature (nom. 60 K)" 
		self.database_name 	= "pulse_tube_first_stage_temperature"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= DiodeTemperatureSensorConduit(1)
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)

class PulseTubeSecondStageTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Pulse Tube Stage #2 Temperature (nom. 3 K)" 
		self.database_name 	= "pulse_tube_second_stage_temperature"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= DiodeTemperatureSensorConduit(3)
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)

class MagnetDiodeTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Magnet Temperature (diode)" 
		self.database_name 	= "magnet_temperature_diode"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= DiodeTemperatureSensorConduit(2)
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)

class FAATemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Ferric Ammonium Alum (FAA) Temperature (RuOx)" 
		self.database_name 	= "FAA_temperature"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= RuOxTemperatureSensorConduit(1)
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)

class GGGTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Gadolinium Gallium Garnet (GGG) Temperature (RuOx)" 
		self.database_name 	= "GGG_temperature"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= RuOxTemperatureSensorConduit(2)
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)

class MagnetRuOxTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Magnet Temperature (RuOx)" 
		self.database_name 	= "magnet_temperature_ruox"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= RuOxTemperatureSensorConduit(3)
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)