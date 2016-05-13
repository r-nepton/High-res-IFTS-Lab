import sqlite3, os, sys, getopt, numpy, datetime

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

def read_data(input_db):
	
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
	global cryo_data
	cryo_data = {}

	#Read out each table in the database
	sql_cursor.execute('SELECT * FROM user_log')
	cryo_data['log'] = sql_cursor.fetchall()
	#print cryo_data['log'][1][1] How to access subsequent lists

	sql_cursor.execute('SELECT * FROM breakout_heatswitch')
	cryo_data['heatswitch'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM compressor')
	cryo_data['compressor'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM magnet_back_emf')
	cryo_data['back_emf'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM magnet_current')
	cryo_data['current'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM pressure_sensor_1')
	cryo_data['pressure'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM ups')
	cryo_data['ups'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM FAA_temperature')
	cryo_data['rox_temp'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM pulse_tube_first_stage_temperature')
	cryo_data['first_stage_temp'] = sql_cursor.fetchall()

	sql_cursor.execute('SELECT * FROM pulse_tube_second_stage_temperature')
	cryo_data['second_stage_temp'] = sql_cursor.fetchall()

	return cryo_data

if __name__ == "__main__":

	input_db = main(sys.argv[1:])
	read_data(input_db)

