import sqlite3, os, sys, getopt, datetime, re
import numpy as np

#read_db.py receives a database filename and stores
#the contents in a dictionary.

def main(sys):
	input_db = ''
	try:
		opts, args = getopt.getopt(argv,"hi:",["input_db="])
	except getopt.GetoptError:
		print 'read_db.py -i <input_db>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print 'read_db.py -i <input_db>'
			sys.exit()
		elif opt in ("-i", "--input_db"):
			input_db = arg
	return input_db

def read_data(input_db, no_processing=False):
	'''
	This function reads a .db file into python and then massages the 
	  data into a dictionary. 

	INPUT:
	  input_db: (str) The filepath to a .db file. 

	  no_processing[False]: (bool) Do minimal massaging of data. 

        OUTPUT:
	  A dictionary containing the information from the .db file. 
	'''
	#Check input_db is a file
	if not os.path.isfile(input_db):
		print 'The database \'%s\' does not exist' % input_db
		sys.exit(2)

	#Open database
	try:
		database_connection = sqlite3.connect(input_db)
		sql_cursor = database_connection.cursor()
	except Exception:
		print 'Could not open database \'%s\'' % input_db
 
	#Create the databse dictionary
#	global cryo_raw  -- we dont have to declare variables in python
	cryo_raw = {}

	#Read out each table in the database
	sql_cursor.execute('SELECT * FROM user_log')
	cryo_raw['log'] = sql_cursor.fetchall()
	#print cryo_raw['log'][1][1] How to access subsequent lists

	sql_cursor.execute('SELECT * FROM breakout_heatswitch')
	cryo_raw['heatswitch'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM compressor')
	cryo_raw['compressor'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM magnet_back_emf')
	cryo_raw['back_emf'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM magnet_current')
	cryo_raw['current'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM pressure_sensor_1')
	cryo_raw['pressure'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM ups')
	cryo_raw['ups'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM FAA_temperature')
	cryo_raw['rox_temp'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM pulse_tube_first_stage_temperature')
	cryo_raw['first_stage_temp'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM pulse_tube_second_stage_temperature')
	cryo_raw['second_stage_temp'] = sql_cursor.fetchall()

	if no_processing:
		return cryo_raw

        cryo_data = {}
	for _ii, _label in enumerate(cryo_raw.keys()):
                if _label == 'log':
                        continue
		cryo_data[_label] = {}
                _inds = np.array(cryo_raw[_label])[:,0]
                _times = np.array(cryo_raw[_label])[:,1]
                _info = np.array(cryo_raw[_label])[:,2]

		cryo_data[_label] = {'time':[datetime.datetime.strptime(i,'%Y-%m-%d %H:%M:%S') for i in _times]}
		# make the info more resonable
		_info_keys = re.split(',|:',(re.split('{|}',_info[0])[1:-1][0]))[::2]
		# make keys for the dictionary for this field
                for _in_k in _info_keys:
			cryo_data[_label][str(_in_k.split('"')[1])] = []
		# fill in the dictionary keys for this field
		for _samp_cnt,_samp in enumerate(_info):
			for _item in re.split(',',(re.split('{|}',_samp)[1:-1][0])):
				_in_lab = str(_item.split(':')[0].split('"')[1])
				_in_val = _item.split(':')[1]
				if _in_lab == 'units':# I dont want to rewrite this field a million times
					if _samp_cnt==0:
						cryo_data[_label][_in_lab] = str(_in_val.split('"')[1].strip())
						continue
					else:
						if cryo_data[_label][_in_lab]==str(_in_val.split('"')[1]).strip():
							continue # if we are just reading the same unit over and over don't rewrite the field
						else:
							print 'Your units are not constant for %s ....maybe check that out...'%(_label)
							print 'Prior units = %s, units now = %s'%(cryo_data[_label][_in_lab][0],str(_in_val.split('"')[1]).strip())
							continue
				if _in_val == u' true':
					cryo_data[_label][_in_lab].append(True)
				elif _in_val == u' false':
					cryo_data[_label][_in_lab].append(False)
				else:
					try:# this will convert the unicode to a number, if _in_val is a float
						cryo_data[_label][_in_lab].append(float(_in_val))
					except ValueError: # if _in_val is not a float, assume we should save a string
						cryo_data[_label][_in_lab].append(str(_in_val.split('"')[1]).strip())
			#if cryo_data[_label][_in_lab] ----make an exception for 'units'
			

#                 if _ii == 0:
#                         cryo_data['times'] = _times
#                 else:
#                         if not all(cryo_data['times'] == _times):
#                                 print 'The timestamps in your database are not the same?!'
        return cryo_data
if __name__ == "__main__":

	input_db = main(sys.argv[1:])
	read_data(input_db)

