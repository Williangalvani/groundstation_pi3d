groundstation_pi3d
==================

once again, i was wrong.
Now porting to pi3d, finally using the gpu.


This project is a groundstation software to communicate with a remote quadcopter

So far it contains:

-Serial communication to read quadcopter data.

-Google maps(with offline cache) to plot current quadcopter position.

-Navball to see quadcopter orientation.

The serial communication finds the first available port, and connects. Then it tries to communicate using the multiwii communication protocol.


### Requirements: ###
Pi3D (https://github.com/tipam/pi3d#setup-on-the-raspberry-pi)

just do :
>sudo pip install pi3d   

if it doesn't work, try:

>sudo pip install --pre pi3d"

### Running ###
To run:

>python mymapviewer.py

Noting that the code is quite ugly, it'll probably be fixed after everything works.
