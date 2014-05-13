import random
# A GenericDataConduit represents a method
# for getting data from a device.
class GenericDataConduit:
	def __init__(self):
		self.name = "GenericDataConduit"

	def field_name(self):
		return self.name

	def get_data(self):
		raise "You can't get data from a GenericDataConduit."

class RandomDataConduit(GenericDataConduit):
	def __init__(self):
		self.name = "RandomDataConduit"

	def get_data(self):
		return random.random()