__author__ = 'will'

from messages import *
from serial.tools import list_ports
import os
import time
import threading
import config
import traceback


serial_available = False
bluetooth_available = False
try:
    import serial

    serial_available = True
except Exception:
    print e

try:
    import bluetooth
    bluetooth_available = True
except Exception, e:
    print e

print " bluetooth: ", bluetooth_available
print " serial: ", serial_available


class TimeOutException(BaseException):
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
        self.last_mac = None
        if serial_available or bluetooth_available:
            self.buffer = ""
            self.run = True
            self.connected = False
            self.window = window
            self.send_thread = FuncThread(self.write_loop)
            self.read_thread = FuncThread(self.read_loop)
            self.receive_thread = FuncThread(self.receive_loop)
            self.send_thread.start()
            self.read_thread.start()
            self.receive_thread.start()
            self.attitude = [0, 0, 0]

        else:
            print("could not load serial module!")

    def read_all(self):
        if self.ser:
            return self.ser.readAll()
        return None

    def read(self, number_of_bytes=1):
        if self.ser:
            return self.ser.read(number_of_bytes)

    def write(self, data):
        if self.ser:
            return self.ser.write(data)
        else:
            return self.sock.send(data)

    def flush_input(self):
        if self.ser:
            self.ser.flushInput()

    def bt_connect(self, device_mac):

        self.last_mac = device_mac
        if self.sock:
            self.sock.close()
        time.sleep(0.5)
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((device_mac, 1))
        self.sock.settimeout(1.0)

        self.sock.setblocking(False)

        print "connected to bluetooth device ", device_mac
        self.ser = None
        self.connected = True

    def find_device(self):
        while self.run and not self.connected:
            if bluetooth_available:
                if self.last_mac:
                    for i in range(100):
                        print "lost connection? trying to reconnect to last mac, try:", i
                        try:
                            self.bt_connect(self.last_mac)
                            break
                        except Exception, ex:
                            print ex
                            print traceback.format_exc()

                        time.sleep(0.3)
                devices_macs = bluetooth.discover_devices()
                print "found: ", devices_macs
                for device_mac in devices_macs:
                    if device_mac in config.macs:
                        self.bt_connect(device_mac)
                        return
                for device_mac in devices_macs:
                    if bluetooth.lookup_name(device_mac) in config.names:
                        self.bt_connect(device_mac)
                        return
            try:
                self.sock = None
                self.ser = serial.Serial(self.list_serial_ports()[0], 115200, timeout=1)
                print "connected to ", self.ser
                self.flush_input()
                self.connected = True
                return
            except Exception as ex:
                print("could not connect, retrying in 3s\n", ex)
                time.sleep(3)

    def receive_loop(self):
        new_data = ""
        while self.run:
            if self.connected:
                try:
                    new_data = self.sock.recv(50)
                except Exception, ex:
                    print "nothing to receive ", ex

            self.buffer += new_data
            time.sleep(0.05)

    def write_loop(self):
        while self.run:
            self.find_device()

            if self.connected:

                try:
                    while self.connected:
                        for i in range(10):
                            if i % 2 == 0:
                                self.msp_query(MSP_RAW_GPS)
                            else:
                                self.msp_query(MSP_ATTITUDE)

                            time.sleep(0.03)
                except Exception as ex:
                    self.connected = False
                    print ex

    def read_loop(self):
        while self.run:
            time.sleep(0.1)
            if len(self.buffer) > 15:
                msgs = self.buffer.split('$M>')
                for msg in msgs:
                    try:
                        msg = bytearray(msg)
                        size = msg.pop(0)
                        command = msg.pop(0)
                        data = []
                        for i in range(size):
                            data.append(msg.pop(0))
                        checksum = 0
                        checksum ^= size
                        checksum ^= command
                        for i in data:
                            checksum ^= i
                        received_checksum = msg.pop(0)
                        if received_checksum == checksum:          # was not supposed to arrive now, but data is data!
                            self.try_handle_response(command, data)
                        self.buffer = ""
                    except Exception, ex:
                        self.buffer = msgs[-1]
                        #print "lost ",  msg, ex

    def stop(self):
        self.run = False
        self.sock.close()

    @staticmethod
    def list_serial_ports():
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

    def msp_query(self, command):
        self.flush_input()
        o = bytearray('$M<')
        c = 0
        o += chr(0)
        c ^= o[3]
        o += chr(command)
        c ^= o[4]
        o += chr(c)
        if self.sock:
            o = str(o)
        self.write(o)

    @staticmethod
    def decode_32(data):
        result = (data[0] & 0xff) + ((data[1] & 0xff) << 8) + ((data[2] & 0xff) << 16) + ((data[3] & 0xff) << 24)
        is_negative = data[3] >= 128
        if is_negative:
            result -= 2 ** 32
        return result

    @staticmethod
    def decode_16(data):
        result = (data[0] & 0xff) + ((data[1] & 0xff) << 8)
        is_negative = data[1] >= 128
        if is_negative:
            result -= 2 ** 16
        return result

    def try_handle_response(self, command, answer):
        if command == MSP_ATTITUDE:
            roll = self.decode_16(answer[0:2]) / 10.0
            pitch = self.decode_16(answer[2:4]) / 10.0
            mag = self.decode_16(answer[4:6])
            self.attitude = (roll, pitch, mag)
            self.window.set_attitude(roll, pitch, mag)
            #print roll, pitch, mag
            return roll, pitch, mag

        elif command == MSP_RAW_GPS:
            lat_list = answer[2:6]
            long_list = answer[6:10]
            latitude = self.decode_32(lat_list) / 10000000.0
            longitude = self.decode_32(long_list) / 10000000.0
            #print longitude,latitude, answer[0:2]
            self.window.set_tracked_position(longitude, latitude, self.attitude[2])
            self.window.set_data("gps_sats", answer[1])
            self.window.set_data("gps_fix", answer[0])
            #print longitude, latitude
            return longitude, latitude, answer[1]
