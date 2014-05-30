# cryo-server #

This application is designed to control and monitor the cryogenic system in the LWLab. 

## Concept ##

The software consists of three parts:

1. A class (Cryostat) which implements all of the methods for communicating with the cryostat measurment instruments.
2. The web-serving implementation which allows remote monitoring
3. A CyroManager class, which runs in a seperate thread from the web server, which periodically collects data from the cryostat, stores it in a database, and takes actions based upon the state of the cryostat.

When the software package is running, it will be possible to monitor and control the system from a web interface. The Cryostat module will allow for computer control
in scripts by importing the class. 

## Compiling the Coffeescript ##

You'll need node.js, npm (node package manager) and the npm module "coffee-script" in order to compile
the coffeescript into javascript.

Once everything is installed (the internet has plenty of tutorials), use the command (from the root directory) 

 coffee -wc --join ./assets/web.js ./assets/coffeescript/

## Running the software ##

Do
 
 sudo python server.py

You should only run it as `sudo` if your user can't bind to port 80 directly.