from cryo_delegate import *
import json, serial_dummy, serial

# This is the interface for the breakout board. The breakout board contains
# an arduino which operates as a serial interface. The arduino controls both
# the heat switch and the magnetization cycle.
class BreakoutBoardInterface(GenericDataConduit):
	def __init__(self):
		self.name = "Breakout Board"
		self.units = "N/A"
                
		self.heat_switch_open	= True

		try:
			self.serial_connection = serial.Serial('/dev/ttyACM0', 9600, timeout=0.1)
		except Exception as e:
			print "There was a problem (%s) connecting to the serial port constructor of: %s" % (e, self.__class__.__name__)
			self.serial_connection = serial_dummy.SerialDummy()

	# This function implements all of the checksums, etc.
	def send_command(self, command_byte):
		command_string = command_byte + chr(127 - ord(command_byte)) + "\n"
		return self.serial_connection.write( command_string )

	# This function attempts to close the heat switch.
	def close_heat_switch(self):
		self.send_command("C")

	# This function gets the data from the conduit. The only data we read, right now,
	# is the state of the touch sensors.
	def get_data(self):
		self.serial_connection.flushInput()
		# The "T" command gets the touch state, and returns it in JSON format.
		self.send_command("T")
		state = self.serial_connection.read(100)
		# We'll just dump the results out.
		try: 
			return json.loads(state)
		except Exception:
			return { 'error': 'unable to talk to the breakout board, for some reason.'}

	# This function returns true or false depending on the state
	# of the connection.
	def verify_connection(self):
		self.serial_connection.flushInput();
		self.send_command("I")
		response = self.serial_connection.read(100)
		if response[0:19] == "BOB control software":
			return True 
		else:
			return False

	# Open heat switch.
	def open_heat_switch(self):
		self.send_command("O")

	# Switch to magnetization cycle (RED), where the magnet loop
	# resistance is ~0 ohms
	def switch_to_magnetization_cycle(self):
		self.send_command("M")

	# Switch to regulation cycle (BLUE) where the magnet loop 
	# resistance is ~25 ohms.
	def switch_to_regulation_cycle(self):
		self.send_command("R")

class BreakoutBoardSensor(GenericCryoDataModel):
	def __init__(self):
		self.name 			= "Breakout board (BOB)"
		self.database_name 	= "breakout_heatswitch"
		self.conduit 		= BreakoutBoardInterface()
		self.units 			= self.conduit.units

		GenericCryoDataModel.__init__(self, self.name)

	# The poll function is overriden for the breakout board, because
	# the state rarely ever changes. So we'll only record an entry if the 
	# current state is different from the recorded state.
	def poll(self):
		current_data = self.conduit.get_data()
		previous_data = self.tail(1)
		if len(previous_data) > 0:
			# Only insert if the current data is different from the previous data.
			if json.dumps( current_data ) != json.dumps( previous_data[0]['data'] ):
				self.insert_data( current_data )
		else: 
			# If there isn't any data, put some in.
			self.insert_data( current_data )
