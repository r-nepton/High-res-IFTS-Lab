import random, serial, serial_dummy, time
from cryo_delegate import *

# The current sensor measures the current from the SIM970. It actually measures
# a voltage, but we multiply that by two to get the current.
class MagnetCurrentSensorConduit(GenericDataConduit):
	def __init__(self):
		self.name = "SIM970 Magnet Current Sensor #%d" % 2
		self.units = "Amperes"
		try:
			self.serial_connection = serial.Serial('/dev/SRS_MAINFRAME', 9600, timeout=0.1)
		except Exception:
			print "There was a problem connecting to the serial port constructor of: %s" % type(self)
			self.serial_connection = serial_dummy.SerialDummy()

		self.SIM970_port = 2
		self.fields = [ 'current' ]

	def get_data(self):
		# Set up the system so it is connected to the right machine.
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 7, 'disconnect'\r")
			self.serial_connection.read(100)
			self.serial_connection.write("VOLT? %d\r" % self.SIM970_port)
		except Exception:
			return { 'current':'unknown', 'error': 'Unable to connect to SIM972.', 'units': 'kelvin' }
			
		response = ""
		# Okay, we've configured the unit correctly. Now let's query for our data.
		try: 
			response = self.serial_connection.read(100);
			current = 2*float(response)
		except Exception:
			return { 'current':'unknown', 'error': 'Could not convert response "%s" to current' % response, 'units':'amperes' }

		# I guess everything worked correctly. Let's clean up now.
		self.serial_connection.write("disconnect\r")

		# Send out the measured temperature.
		return { 'current':current, 'units':'amperes' }

class MagnetCurrentSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Magnet Current Sensor" 
		self.database_name 	= "magnet_current"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= MagnetCurrentSensorConduit()
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)
