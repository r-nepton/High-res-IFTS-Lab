#!/bin/bash
# This script kills the current cryo-server, recompiles the 
# coffeescript and then re-starts the server.
# Use the option -r to remove the current database.

remove_database=0
while [ "$1" != "" ]; do
	case $1 in
		-r | --remove )		shift
					remove_database=1
	esac
	shift
done

echo "Killing screen..."
sudo screen -S cryoserver -X quit

if [ "$remove_database" -eq 1 ]; then
	echo "Removing database..."
	rm -f ./data/database.db
fi

echo "Compiling coffeescript..."
cat ./assets/coffeescript/*.coffee | coffee -wcs > ./assets/web.js

echo "Starting cryoserver..."
sudo screen -L -S cryoserver -d -m /home/matt/anaconda2/bin/python ./server.py
