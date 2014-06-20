from cryo_delegate import *

# The user-log is written by the actual person.
class UserLogWriter(GenericCryoDataModel):
	def __init__(self):
		self.name 			= "User-written log file"
		self.database_name 	= "user_log"
		self.units 			= "words"

		GenericCryoDataModel.__init__(self, self.name)

	# This function would write the actual log entry.
	def write_log(self, log):
		self.insert_data( log )

# The computer-log is written by the computer.
class ComputerLogWriter(UserLogWriter):
	def __init__(self):
		self.name 			= "Robot-written log file"
		self.database_name	= "robot_log"
		self.units			= "words"

		GenericCryoDataModel.__init__(self, self.name)