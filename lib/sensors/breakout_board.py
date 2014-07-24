from cryo_delegate import *

# This is the interface for the breakout board. The breakout board contains
# an arduino which operates as a serial interface. The arduino controls both
# the heat switch and the magnetization cycle.
class BreakoutBoardInterface(object):
	def __init__(self):
		self.name = "Breakout Board"
		self.units = "N/A"

		try:
			self.serial_connection = serial.Serial('/dev/ttyACM0', 9600, timeout=0.1)
		except Exception:
			print "There was a problem connecting to the serial port constructor of: %s" % type(self)
			self.serial_connection = serial_dummy.SerialDummy()

	# This function implements all of the checksums, etc.
	def send_command(self, command_byte):
		command_string = command_byte + chr(ord(127 - command_byte)) + "\n"
		return self.serial_connection.write( command_string )

	# This function attempts to close the heat switch.
	def close_heat_switch(self):
		self.send_command("C")

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