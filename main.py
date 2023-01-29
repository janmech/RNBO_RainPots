#!/usr/bin/env python3
# coding=utf-8
import serial
import time
import struct
import liblo as OSC
import sys
import traceback
import argparse
from RainPots import Parameters
from RainPots import OscListener
from RainPots import OscSender
from RainPots import SerialSender

# version 2022-01-22


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--debug", help="Enable debug output", required=False, action='store_true', default=False)
        arguments = parser.parse_args()
        debug = arguments.debug

        if debug:
            print("Starting RainPots\n")

        params = Parameters.ParamConfig(debug)
        param_config = params.load_config()

        port = serial.Serial("/dev/ttyS0", baudrate=380400)
        if port.isOpen():
            port.close()
        if not port.isOpen():
            port.open()
        try:
            serial_sender = SerialSender.Sender(params, port, debug)
            osc_sender = OscSender.Sender(1234, params, serial_sender, debug)

            listener = OscListener.Listener(9999, params, serial_sender, debug)
            listener.start()
        except Exception as err:
            print(str(err))
            sys.exit()

        try:
            target = OSC.Address(1234)
        except OSC.AddressError as err:
            print(err)
            sys.exit()

        # add listener
        OSC.send(target, '/rnbo/listeners/add', '127.0.0.1:9999')

        while True:
            data_bytes = []
            packet = []
            controller = 0
            packet_index = -1
            rainpots_unit = -1
            collecting = False
            while port.inWaiting() > 0:
                try:
                    received_byte = port.read()
                    int_value = int.from_bytes(received_byte, 'little')
                    if 176 <= int_value <= 191:
                        collecting = True
                        packet_index = 0
                        packet = [0, 0, 0, 0]
                        controller = -1
                        # rainpots_unit = int_value & 0x0f
                        packet[packet_index] = int_value
                        # data_bytes = [0, 0]
                    elif collecting:
                        packet_index = packet_index + 1
                        if packet_index == 1:
                            packet[1] = int_value
                        elif 2 <= packet_index <= 3:
                            packet[packet_index] = int_value
                    if packet_index == 3:
                        osc_sender.send_packet(packet)
                        rainpots_unit = -1
                        collecting = False

                except Exception as err:
                    print(err)
                    traceback.print_exc()
                    rainpots_unit = -1
                    collecting = False
                    pass
            # Limit CPU usage, so we do nit fry on core at 100% all times
            time.sleep(0.000000001)
    except KeyboardInterrupt:
        print()
        sys.exit(0)
#  OSC.send(target, "/rnbo/inst/0/params/voice-mode/normalized", final_value)
