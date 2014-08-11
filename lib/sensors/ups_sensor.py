from cryo_delegate import *
import shell_command, re

# This class interfaces with the UPS via the command line cyberpower utility.
# The cyberpower utility is called pwrstat: 
# http://www.cyberpowersystems.com/user-manuals/PPL-1.2_Software_UserManual.pdf

class UPSDataConduit(GenericDataConduit):
	def __init__(self):
		self.name	= "Cyberpower Universal Power Supply"
		self.units	= "%"

	def get_data(self):
		try:			
			result = shell_command.shell_command("pwrstat -status")
		except Exception:
			result = ""

		# Check to see if the pwrstat utility is operating normally.
		if not re.search("The UPS information shows as following:", result):
			return {
				"error": "There was a problem connecting to the UPS.",
				"error_message": result
			}

		# First, get the battery capacity.
		m = re.search("Battery Capacity\.+ (.*?)%\n", result)
		battery_capacity = int( m.group(1) )

		# Now, get the current power load.
		m = re.search("Load\.+ (.*?)Watt", result)
		power_load = int(m.group(1))
		
		# Now determine the power state.
		m = re.search("Power Supply by.+? (.*?)\n", result)
		line_power = (m.group(1) == "Utility Power")

		return { 
			'battery_capacity': 		battery_capacity,
			'battery_capacity_units': 	"percent",
			'line_power':				line_power,					
			'power_load':				power_load,
			'power_load_units':			'watts'
		}

class UPSSensor(GenericCryoDataModel):
	def __init__(self):
		self.name 			= "Cyberpower Universal Power Supply"
		self.database_name 	= "ups"
		self.conduit 		= UPSDataConduit()
		self.units 			= self.conduit.units

		GenericCryoDataModel.__init__(self, self.name)