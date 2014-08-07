# This script is called when the power to the UPS is lost. It
# connects to the (running) cryo-server and issues a "UPS power lost" 
# message.

from websocket import create_connection
import json

ws = create_connection("ws://localhost/json")

# The message requires a password to work. The password comes from the password file.
f = open("secret.passwords")
password_database = json.loads( f.read() )
password = password_database['password']

message = {
	"transaction_id": 100,
	"data": {
		"action": "shutdown_server",
		"arguments": {
			"password": password
		}
	}
}

print "Server shutdown message sent."

ws.send( json.dumps( message ) )