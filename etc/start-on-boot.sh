#!/usr/bin/bash

# This is a bash script which starts the server in screen mode. It should be run
# by root, or a user which can bind to port 80 and control the serial port.

screen -L -S cryoserver -d -m python /var/cryo-server/server.py