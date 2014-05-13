import random
from cryo_delegate import *

class TemperatureSensorConduit(GenericDataConduit):
	def __init__(self, interface_number):
		self.name = "Generic Temperature Sensor #%d" % interface_number
		self.units = "Kelvin"

	def get_data(self):
		return { 'temperature':random.random(), 'units':'kelvin' }

class GenericTemperatureSensor(GenericCryoDataModel):
	def __init__(self, interface_number): 
		self.interface_number = interface_number
		self.name 			= "Generic Temperature Sensor #%d" % self.interface_number
		self.database_name 	= "temperature_sensor_%d" % self.interface_number
		self.conduit 		= TemperatureSensorConduit(self.interface_number)
		self.units 			= self.conduit.units
		
		GenericCryoDataModel.__init__(self, self.name)