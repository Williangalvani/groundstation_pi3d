__author__ = 'will'

from messages import *
from serial.tools import list_ports
import os
import time
import threading
import config

serial_available = False
bluetooth_available = False
try:
    import serial

    serial_available = True
except:
    pass

try:
    import bluetooth

    bluetooth_available = True
except:
    pass


class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args

        threading.Thread.__init__(self)

    def run(self):
        self._target(*self._args)


class TelemetryReader():
    def __init__(self, window):
        self.ser = None
        self.sock = None
        if serial_available or bluetooth_available:
            self.run = True
            self.connected = False
            self.window = window
            self.thread = FuncThread(self.loop)
            self.thread.start()
            self.attitude = [0, 0, 0]
        else:
            print("could not load serial module!")

    def read_all(self):
        if self.ser:
            return self.ser.readAll()
        return None

    def read(self, bytes=1):
        if self.ser:
            return self.ser.read(bytes)
        else:
            return self.sock.recv(bytes)

    def write(self, data):
        if self.ser:
            return self.ser.write(data)
        else:
            return self.sock.send(data)

    def flush_input(self):
        data = None
        if self.ser:
            self.ser.flushInput()
        # else:
        #     try:
        #         self.sock.set_timeout(0.1)
        #         data = self.sock.recv(1000)
        #         self.sock.set_timeout(1.0)
        #     except:
        #         pass
        #     print "dropped" , data

    def find_device(self):
        while self.run and not self.connected:
            if bluetooth_available:
                devices_macs = bluetooth.discover_devices()
                for device_mac in devices_macs:
                    if device_mac in config.macs:
                        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                        self.sock.connect((device_mac, 1))
                        #print dir(self.sock)
                        self.ser = None
                        self.connected = True
                        return
                    if bluetooth.lookup_name(device_mac) in config.names:
                        time.sleep(1)
                        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                        self.sock.connect((device_mac, 1))
                        #print dir(self.sock)
                        print "connected to bluetooth device ", device_mac
                        self.ser = None
                        self.connected = True
                        return
            try:
                self.sock = None
                self.ser = serial.Serial(self.list_serial_ports()[0], 115200, timeout=1)
                print "connected to " , self.ser
                self.flush_input()
                self.connected = True
                return
            except Exception as e:
                print("could not connect, retrying in 3s\n", e )
                time.sleep(3)

    def loop(self):
        self.find_device()

        if self.connected:
            try:
                while self.run:
                    for i in range(10):
                        if i % 3 == 0:
                            self.read_gps()

                        else:
                            self.read_attitude()


                        time.sleep(0.05)
            except Exception as e:
                self.connected = False
                print (e)

    def stop(self):
        self.run = False
        self.sock.close()

    def list_serial_ports(self):
        # Windows
        if os.name == 'nt':
            # Scan for available ports.
            available = []
            for i in range(256):
                try:
                    s = serial.Serial(i)
                    available.append('COM' + str(i + 1))
                    s.close()
                except serial.SerialException:
                    pass
            return available
        else:
            # Mac / Linux
            return [port[0] for port in list_ports.comports()]

    def receiveAnswer(self, expectedCommand):
        header = self.read(3)
        if '$M>' not in header:
            return None
        size = ord(self.read())
        command = ord(self.read())
        data = []
        for i in range(size):
            data.append(ord(self.read()))
        checksum = 0
        checksum ^= size;
        checksum ^= command;
        for i in data:
            checksum ^= i;
        receivedChecksum = ord(self.read())
        #print 'command' , command
        #print 'size' , size
        #print 'data' , data
        #print checksum, receivedChecksum
        if command != expectedCommand:
            print( "commands dont match!", command, expectedCommand)
            self.flush_input()
            if receivedChecksum == checksum:          # was not supposed to arrive now, but data is data!
                self.try_handle_response(command,data)
            return None
        if checksum == receivedChecksum:
            return data
        else:
            print ('lost packet!')
            return None

    def MSPquery(self, command):
        o = bytearray('$M<')
        c = 0
        o += chr(0)
        c ^= o[3]       #no payload
        o += chr(command)
        c ^= o[4]
        o += chr(c)
        if self.sock:
            o = str(o)
        answer = None
        while not answer:
            #print "writing" , o
            self.write(o)
            #self.flush_input()
            answer = self.receiveAnswer(command)
            #print answer
        return answer


    def decode32(self, data):
        #print data
        result = (data[0] & 0xff) + ((data[1] & 0xff) << 8) + ((data[2] & 0xff) << 16) + ((data[3] & 0xff) << 24)
        is_negative = data[3] >= 128
        if is_negative:
            result -= 2 ** 32
        return result

    def decode16(self, data):
        #print data
        result = (data[0] & 0xff) + ((data[1] & 0xff) << 8)
        is_negative = data[1] >= 128
        if is_negative:
            result -= 2 ** 16
        return result


    def read_gps(self):
        answer = self.MSPquery(MSP_RAW_GPS)
        if answer:
            return self.try_handle_response(MSP_RAW_GPS,answer)
        return (0, 0, 0)

    def read_attitude(self):
        answer = self.MSPquery(MSP_ATTITUDE)
        if answer:
            return self.try_handle_response(MSP_ATTITUDE, answer)
        return (0,0,0)

    def try_handle_response(self, command, answer):
        if command == MSP_ATTITUDE:
            roll = self.decode16(answer[0:2]) / 10.0
            pitch = self.decode16(answer[2:4]) / 10.0
            mag = self.decode16(answer[4:6])
            self.window.set_attitude(roll,pitch,mag)
            return roll, pitch, mag

        elif command == MSP_RAW_GPS:
            lat_list = answer[2:6]
            long_list = answer[6:10]
            latitude = self.decode32(lat_list) / 10000000.0
            longitude = self.decode32(long_list) / 10000000.0
            #print longitude,latitude, answer[0:2]
            self.window.set_tracked_position(latitude, longitude, self.attitude[2])
            self.window.set_data("gps_sats", answer[1])
            self.window.set_data("gps_fix", answer[0])
            return longitude, latitude, answer[1]


if __name__ == '__main__':
    import bluetooth

    target_name = "HB01"
    target_address = "00:13:03:29:20:30"


    #nearby_devices = bluetooth.discover_devices()
    # print "founds macs: ", nearby_devices

    # for mac in nearby_devices:
    #     print mac, bluetooth.lookup_name(mac)

    # for bdaddr in nearby_devices:
    #     if target_name == bluetooth.lookup_name(bdaddr):
    #         target_address = bdaddr
    #         break
    #
    # if target_address is not None:
    #     print "found target bluetooth device with address ", target_address
    # else:
    #     print "could not find target bluetooth device nearby"
    #
    # print bluetooth.find_service(address=target_address)
    port = 1
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    #print sock.bound
    #connected = False
    sock.connect((target_address, port))
    #connected = sock.connected



    print 'Connected'
    sock.settimeout(1.0)

    sock.send('!hw\r')
    try:
        print sock.recv(100)
    except:
        pass
    print MSPquery(sock, MSP_IDENT)
    print MSPquery(sock, MSP_ATTITUDE)
    print MSPquery(sock, MSP_RAW_GPS)
    print MSPquery(sock, MSP_STATUS)

    sock.send("x")
    print 'Sent data'

    data = sock.recv(1)
    print 'received [%s]' % data

