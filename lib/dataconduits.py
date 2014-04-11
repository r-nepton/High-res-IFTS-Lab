import random
# A GenericDataConduit represents a method
# for getting data from a device.
class GenericDataConduit:
	def __init__(self):
		self.name = "GenericDataConduit"

	def field_name():
		return self.name

	def get_data():
		raise "You can't get data from a GenericDataConduit."

class RandomDataConduit(GenericDataConduit):
	def __init__(self):
		self.name = "RandomDataConduit"

	def get_data():
		return random.random()