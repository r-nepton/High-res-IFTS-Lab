import random, serial, serial_dummy, time
from cryo_delegate import *

# The back-EMF sensor measures the voltage from the SIM970.
# This voltage should be kept below (+-)100mV
class MagnetBackEmfSensorConduit(GenericDataConduit):
	def __init__(self):
		self.name = "SIM970 Magnet Back EMF Sensor #%d" % 1
		self.units = "Volts"
		try:
			self.serial_connection = serial.Serial('/dev/SRS_MAINFRAME', 9600, timeout=0.1)
		except Exception:
			print "There was a problem connecting to the serial port constructor of: %s" % type(self)
			self.serial_connection = serial_dummy.SerialDummy()

		self.SIM970_port = 1
		self.fields = [ 'voltage' ]

	def get_data(self):
		# Set up the system so it is connected to the right machine.
		try:
			self.serial_connection.write("disconnect\r")
			self.serial_connection.write("CONN 7, 'disconnect'\r")
			self.serial_connection.read(100)
			self.serial_connection.write("VOLT? %d\r" % self.SIM970_port)
		except Exception:
			return { 'voltage':'unknown', 'error': 'Unable to connect to SIM972.', 'units': 'volts' }
			
		response = ""
		# Okay, we've configured the unit correctly. Now let's query for our data.
		try: 
			response = self.serial_connection.read(100);
			voltage = float(response)
		except Exception:
			return { 'voltage':'unknown', 'error': 'Could not convert response "%s" to voltage' % response, 'units':'volts' }

		# I guess everything worked correctly. Let's clean up now.
		self.serial_connection.write("disconnect\r")

		# Send out the measured temperature.
		return { 'voltage':voltage, 'units':'volts' }

class MagnetBackEmfSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Magnet Back EMF Sensor" 
		self.database_name 	= "magnet_back_emf"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= MagnetBackEmfSensorConduit()
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)
