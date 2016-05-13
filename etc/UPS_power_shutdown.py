# This script is called when the power to the UPS is lost. It
# connects to the (running) cryo-server and issues a "UPS power lost" 
# message.

from websocket import create_connection
import json, os

# It is helpful to change directories to the current directory of the
# script. That way, we can access relative file paths properly.
os.chdir( os.path.dirname(os.path.realpath(__file__)) )

# Connect to the locally-running server.
ws = create_connection("ws://localhost/json")

# The message requires a password to work. The password comes from the password file.
f = open("secret.passwords")
password_database = json.loads( f.read() )
password = password_database['password']

message = {
	"transaction_id": 100,
	"data": {
		"action": "ups_power_lost",
		"arguments": {
			"password": password
		}
	}
}

ws.send( json.dumps( message ) )
