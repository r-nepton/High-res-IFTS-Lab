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

	# This method sums together data using an averaging technique, suitable for
	# use as a "reduce" method.
	def sum_data(self, d1, d2):
		# We'll copy the results into a new result dictionary.
		result = {}

		def valid_field(field, dictionary):
			return field in dictionary and not isinstance(dictionary[field], basestring)

		def field_count(field, dictionary):
			if field+'_data_count' in dictionary:
				return dictionary[field+'_data_count']
			else:
				return 1

		# Try to sum the values together. But there's a chance that the values
		# are not numeric (e.g. in the case of an error) so the non-error values
		# are used. This system can be used in combination with a "reduce"-style
		# function, because it averages over valid data points by recording the
		# count of that data point.
		for field in self.fields:
			if valid_field(field, d1) and valid_field(field, d2):
				# We are combining the two results: so we need to weight the sum
				# by the number of points represented in each value.
				d1_weight = field_count(field, d1)
				d2_weight = field_count(field, d2)
				result[field] = ( d1_weight*d1[field] + d2_weight*d2[field] ) / (d1_weight + d2_weight)
				result[field+'_data_count'] = d1_weight + d2_weight
			elif valid_field(field, d1):
				result[field] = d1[field]
			elif valid_field(field, d2):
				result[field] = d2[field]
			else:
				result[field] = 'unknown'

			return result

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
	def range(self, start, end, data_points):
		q	= "SELECT value,CAST(strftime('%%s',time) as INT) as t FROM %s WHERE t > ? AND t < ?" % (self.database_name)
		self.db.execute(q, [start, end])
		data = []
		# Preload the range with blank data.
		for p in numpy.linspace(start,end,data_points):
			data.append( [] )
		# Collect together the data into bins.
		for r in self.db.fetchall():
			# Determine the right index for the space.
			index = int(numpy.ceil( data_points * ( r[1] - start ) / ( (end - start) ) ))
			# Collect the bins together.
			data[index].append( json.loads(r[0]) )

		result = []
		# Now, reduce the bins together. But only include bins which have real data.
		for index,d in enumerate(data):
			if len(d) > 0:
				smash = reduce( lambda x,y: self.conduit.sum_data(x,y), d )
				result.append( { 
					'data': smash, 
					'time': start + index * (end - start) / ( data_points )
				})

		# Okay finally we're done.
		return result

	# Get the last X number of entries into the database.
	def tail(self, number=10):
		q 	= "SELECT value,CAST(strftime('%%s',time) as INT) FROM %s ORDER BY time DESC LIMIT ?" % self.database_name
		self.db.execute(q, [number])
		return [ { 'time': f[1], 'data': json.loads(f[0]) }  for f in self.db.fetchall() ]

	def initialize(self):
		# Set up the databsae.
		self.db.execute( self.database_configuration() )
