import random
import cryo_delegate
import sqlite3, json, os, sys, numpy
# A GenericDataConduit represents a method
# for getting data from a device.


class GenericDataConduit:
	def __init__(self):
		self.name = "GenericDataConduit"

	def field_name(self):
		return self.name

	def get_data(self):
		raise "You can't get data from a GenericDataConduit."

	def sum_data(d1, d2):
		data = [ 'inlet_temperature', 'outlet_temperature', 'oil_temperature']
	#	for field in data:
	#		if d1[field] 

class RandomDataConduit(GenericDataConduit):
	def __init__(self):
		self.name = "RandomDataConduit"

	def get_data(self):
		return random.random()

# The GenericCryoDataModel object is the base class of all
# data sources. It understands how to create its own database
# table, write its own log files, and perform queries upon itself.
class GenericCryoDataModel(object):
	def __init__(self, name):
		self.name 			= name
		if hasattr(self, 'conduit') == False:
			self.conduit 		= GenericDataConduit()
		if hasattr(self, 'database_name') == False:
			self.database_name 	= self.name
		if hasattr(self, 'units') == False:
			self.units = "count"

		self.db = cryo_delegate.database_connection.cursor() # database connection.
		self.initialize()

	def __del__(self):
		print "Saving database '%s'..." % self.name
		try:
			cryo_delegate.database_connection.commit()
		except Exception():
			pass

	# This function returns the database configuration. It should almost always
	# be the same.
	def database_configuration(self):
		q 	= "CREATE TABLE IF NOT EXISTS %s (" % self.database_name
		q 	+= "id INTEGER PRIMARY KEY,\n"
		q 	+= "time 	timestamp(14) not null,"
		q 	+= "value 	varchar(512) null"
		q 	+= ")"
		return q

	def poll(self):
		# Insert a data entry.
		self.insert_data( self.conduit.get_data() )

	# Inser the data value (a python hash) into the database
	# using the current time.
	def insert_data(self, value):
		q 	= "INSERT INTO %s (time, value) VALUES (CURRENT_TIMESTAMP, ?)" % self.database_name
		self.db.execute(q, [json.dumps(value)]) 

	# Get the last X entries, averaged with the specified resolution (all in seconds or unix time).
	#def range(self, start, end, resolution=30):
	#	q	= "SELECT value,CAST(strftime('%%s',time) as INT) FROM %s WHERE time < ? AND time > ?" % (self.database_name)
	#	self.db.execute(q, [start, end])
	#	data = []
		# Preload the range with blank data.
	#	for p in numpy.linspace(start,end,step=resolution):
	#		data.append { 'time': p, 'data': 'unknown', 'count':0 }
		# Average together the data.
	#	for r in self.db.fetchall():
			# Determine the right index for the space.
	#		index = numpy.ceil( (end - start) / resolution )
			

	# Get the last X number of entries into the database.
	def tail(self, number=10):
		q 	= "SELECT value,CAST(strftime('%%s',time) as INT) FROM %s ORDER BY time DESC LIMIT ?" % self.database_name
		self.db.execute(q, [number])
		return [ { 'time': f[1], 'data': json.loads(f[0]) }  for f in self.db.fetchall() ]

	def initialize(self):
		# Set up the databsae.
		self.db.execute( self.database_configuration() )
