import random, time
import serial, serial_dummy
from dataconduits import GenericDataConduit, GenericCryoDataModel

# The temperature sensor reads the diode temperatures from the SIM922.
# The four channels are laid out on page 45 of the HPD104 operating manual.
class DiodeTemperatureSensorConduit(GenericDataConduit):
	def __init__(self, interface_number):
		self.name = "SIM922 Silicon Diode Temperature Sensor #%d" % interface_number
		self.units = "Kelvin"

		try:
			self.serial_connection = serial.Serial('/dev/SRS_MAINFRAME', 9600, timeout=0.5)
		except Exception:
			print("There was a problem connecting to the serial port constructor of: %s" % self.__class__.__name__)
			self.serial_connection = serial_dummy.SerialDummy()

		self.SIM922_port = interface_number
		self.fields = [ 'temperature' ]

	def get_data(self):
		# Set up the system so it is connected to the right machine.
		try:
			self.serial_connection.write(b"disconnect\r")
			self.serial_connection.write(b"CONN 5, 'disconnect'\r")
			self.serial_connection.read(100)
			self.serial_connection.write(("TVAL? %d\r" % self.SIM922_port).encode('utf-8'))
		except Exception:
			return { 'temperature':'unknown', 'error': 'Unable to connect to SIM922.', 'units': 'kelvin' }
		
		# Okay, we've configured the unit correctly. Now let's query for our data.
		try: 
			response = self.serial_connection.read(100);
			temperature = float(response.decode('utf-8').strip())
		except Exception:
			return { 'temperature':'unknown', 'error': 'Could not convert response "%s" to temperature' % response, 'units':'kelvin' }

		# I guess everything worked correctly. Let's clean up now.
		self.serial_connection.write(b"disconnect\r")

		# The diode temperature sensor can only measure up to 300 K. Above
		# that, it gives out crazy measurements (like 500 K)
		if temperature > 300:
			return { 'temperature':'unknown', 'error': 'Temperature (%s K) is above the limit for the device.' % temperature, 'units':'kelvin' }

		# Send out the measured temperature.
		return { 'temperature':temperature, 'units':'kelvin' }

class RuOxTemperatureSensorConduit(GenericDataConduit):
	def __init__(self, interface_number):
		self.name = "SIM921 Ruthenium Oxide Temperature Sensor #%d" % interface_number
		self.units = "Kelvin"

		try:
			self.serial_connection = serial.Serial('/dev/SRS_MAINFRAME', 9600, timeout=0.5)
		except Exception:
			print("There was a problem connecting to the serial port constructor of: %s" % self.__class__.__name__)
			self.serial_connection = serial_dummy.SerialDummy()

		self.SIM925_port = interface_number
		self.fields = [ 'temperature' ]

	def get_data(self):
		# Set up the system so it is connected to the right machine.
		try:
			self.serial_connection.write(b"disconnect\r")
			# First, connect to the octal multiplexer and set the channel.
			#self.serial_connection.write("CONN 6, 'disconnect'\r")
			#self.serial_connection.write("CHAN %d\r" % self.SIM925_port)
			# The channel switching time is 50 ms. Delay to ensure correct switch.
			# The AC resistance bridge needs 3 seconds to stabilize
			#time.sleep(3)
			# Now disconnect from the mux and connect to the bridge reader.
			#self.serial_connection.write("disconnect\r")
			self.serial_connection.write(b"CONN 1, 'disconnect'\r")
			# Clear out the buffer.
			self.serial_connection.read(2000)
			self.serial_connection.write(b"TVAL?\r")
		except Exception:
			return { 'temperature':'unknown', 'error': 'Unable to connect to SIM921.', 'units': 'kelvin' }
		
		# Okay, we've configured the unit correctly. Now let's query for our data.
		try: 
			response = self.serial_connection.read(100);
			temperature = float(response.decode('utf-8').strip())
		except Exception:
			return { 'temperature':'unknown', 'error': 'Could not convert response "%s" to temperature' % response, 'units':'kelvin' }

		# I guess everything worked correctly. Let's clean up now.
		self.serial_connection.write(b"disconnect\r")

		# The RuOx temperature sensor can only measure up to 4.28 K. Above
		# that, it gives out crazy measurements (like 500 K)
		if temperature > 4:
			return { 'temperature':'unknown', 'error': 'Temperature (%s K) is above the limit for the device.' % temperature, 'units':'kelvin' }

		# Send out the measured temperature.
		return { 'temperature':temperature, 'units':'kelvin' }

class PulseTubeFirstStageTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Pulse Tube Stage #1 Temperature (nom. 60 K)" 
		self.database_name 	= "pulse_tube_first_stage_temperature"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= DiodeTemperatureSensorConduit(1)
		self.units 			= self.conduit.units	
		
		# GenericCryoDataModel.__init__(self, self.name)
		super().__init__(self.name)

class PulseTubeSecondStageTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Pulse Tube Stage #2 Temperature (nom. 3 K)" 
		self.database_name 	= "pulse_tube_second_stage_temperature"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= DiodeTemperatureSensorConduit(3)
		self.units 			= self.conduit.units
		
		# GenericCryoDataModel.__init__(self, self.name)
		super().__init__(self.name)

class MagnetDiodeTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Magnet Temperature (diode)" 
		self.database_name 	= "magnet_temperature_diode"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= DiodeTemperatureSensorConduit(2)
		self.units 			= self.conduit.units
		
		# GenericCryoDataModel.__init__(self, self.name)
		super().__init__(self.name)

class FAATemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Ferric Ammonium Alum (FAA) Temperature (RuOx)" 
		self.database_name 	= "FAA_temperature"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= RuOxTemperatureSensorConduit(1)
		self.units 			= self.conduit.units
		
		# GenericCryoDataModel.__init__(self, self.name)
		super().__init__(self.name)

class GGGTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Gadolinium Gallium Garnet (GGG) Temperature (RuOx)" 
		self.database_name 	= "GGG_temperature"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= RuOxTemperatureSensorConduit(2)
		self.units 			= self.conduit.units
		
		# GenericCryoDataModel.__init__(self, self.name)
		super().__init__(self.name)

class MagnetRuOxTemperatureSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Magnet Temperature (RuOx)" 
		self.database_name 	= "magnet_temperature_ruox"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= RuOxTemperatureSensorConduit(3)
		self.units 			= self.conduit.units
		
		# GenericCryoDataModel.__init__(self, self.name)
		super().__init__(self.name)

