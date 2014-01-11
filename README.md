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
  -  PIL
  -  pyGObject
pyserial


### Installing ###
to install pil and pygobject:
>sudo apt-get install python-imaging python-gobject

if you dont have pip installed:
>sudo apt-get install python-pip

Then, to install pi3d:

>sudo pip install --pre pi3d"

now pyserial, which must be version 2.7+: 
>sudo pip install pyserial --upgrade

### Running ###
To run:

>python mymapviewer.py

Noting that the code is quite ugly, it'll probably be fixed after everything works.

### Bluetooth ###

for bluetooth support:

>sudo apt-get install bluez python-bluez

you might also have to do:

> sudo bluez-simple-agent hci0 XX:XX:XX:XX:XX:XX

(it will then ask for the pin, on my HB01 the PIN is 1234)

where hci0 is the pc bluetooth adapter, and XX:XX:XX:XX:XX:XX is your remote bluetooth adapter mac address
