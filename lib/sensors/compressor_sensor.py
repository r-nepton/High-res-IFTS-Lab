from syncom_multidrop import *
from cryo_delegate import *

# The temperature sensor reads the diode temperatures from the SIM922.
# The four channels are laid out on page 45 of the HPD104 operating manual.
class CompressorSensorConduit(GenericDataConduit):
	def __init__(self):
		self.name = "Compressor temperature sensor (inlet, outlet, oil, helium)"
		self.units = "Celsius"
		self.syncom_connection = SyncomMultiDropAdapter()

	def get_data(self):
		# Set up the system so it is connected to the right machine.

		# Set default values for all of the measurements.
		inlet_temperature 	= 'unknown'
		outlet_temperature 	= 'unknown'
		oil_temperature		= 'unknown'

		try:
			# Refer to the CP2800 manual, which describes the data dictionary
			# for the compressor. The water, oil, etc. temperatures come from
			# the 0x0D84 address, using indices 0-3.

			# First we'll clear whatever garbage data is in the buffer.
			self.syncom_connection.clear_buffer()

			# Measure the inlet temperature.
			self.syncom_connection.write( [0x63, 0x0D, 0x8F, 0x00] )
			result = self.syncom_connection.read()
			# The result is in tenths of a degree celsius.
			inlet_temperature = float(result) / 10

			# Measure the outlet temperature.
			self.syncom_connection.write( [0x63, 0x0D, 0x8F, 0x01] )
			result = self.syncom_connection.read()
			# The result is in tenths of a degree celsius.
			outlet_temperature = float(result) / 10

			# Measure the helium temperature.
			self.syncom_connection.write( [0x63, 0x0D, 0x8F, 0x03] )
			result = self.syncom_connection.read()
			# The result is in tenths of a degree celsius.
			oil_temperature = float(result) / 10

		except Exception as exception:
			# Something went wrong. This protocol is extremely bad, and is 
			# probably unreliable to expect it to always work. We'll just output
			# whatever we've got.
			return { 
				'inlet_temperature'		: inlet_temperature, 
				'outlet_temperature'	: outlet_temperature, 
				'oil_temperature'		: oil_temperature,  
				'error'					: "Unable to connect to compressor: error %s." % exception, 
				'units'					: 'celsius' 
			}

		# Well, I suppose everything worked. Send out the measured temperature.
		return { 
			'inlet_temperature'		: inlet_temperature, 
			'outlet_temperature'	: outlet_temperature, 
			'oil_temperature'		: oil_temperature, 
			'units'					: 'celsius' 
		}

class CompressorSensor(GenericCryoDataModel):
	def __init__(self): 
		self.name 			= "Compressor temperature sensor (inlet, outlet, oil, helium)" 
		self.database_name 	= "compressor"
		# The interface number comes from the HPD operating manual, page 45.
		self.conduit 		= CompressorSensorConduit()
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)