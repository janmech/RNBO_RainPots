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
            packet_cc = []
            controller = 0
            packet_index_cc = -1
            rainpots_unit = -1
            collecting_cc = False
            pgm_number = -1
            pgm_cmd = ''
            
            collecting_pgm_change = False
            while port.inWaiting() > 0:
                try:
                    received_byte = port.read()
                    int_value = int.from_bytes(received_byte, 'little')
                    if 176 <= int_value <= 191:  # B0 - BF (Control Change)
                        collecting_cc = True
                        packet_index_cc = 0
                        packet_cc = [0, 0, 0, 0]
                        controller = -1
                        packet_cc[packet_index_cc] = int_value
                    elif collecting_cc and not collecting_pgm_change:
                        packet_index_cc = packet_index_cc + 1
                        if packet_index_cc == 1:
                            packet_cc[1] = int_value
                        elif 2 <= packet_index_cc <= 3:
                            packet_cc[packet_index_cc] = int_value
                    if packet_index_cc == 3 and collecting_cc:
                        osc_sender.send_packet(packet_cc)
                        rainpots_unit = -1
                        collecting_cc = False

                    if 192 <= int_value <= 207 or int_value == 244:  # C0 - CF (Program Change) | F4 (Save Preset)
                        collecting_pgm_change = True
                        pgm_number = -1
                        if int_value == 244:
                            pgm_cmd = 'save'
                        else:
                            pgm_cmd = 'load'
                    elif collecting_pgm_change and not collecting_cc:
                        pgm_number = int_value
                        collecting_pgm_change = False
                        if debug:
                            print("SENDING PGM (%s)" % pgm_cmd, pgm_number)
                        osc_sender.send_pgm_control(pgm_cmd, pgm_number)
                        pgm_number = -1
                        pgm_cmd = ''
                except Exception as err:
                    print(err)
                    traceback.print_exc()
                    rainpots_unit = -1
                    collecting_cc = False
                    collecting_pgm_change = False
                    pgm_cmd = ''
                    pass
            # Limit CPU usage, so we do nit fry on core at 100% all times
            time.sleep(0.000000001)
    except KeyboardInterrupt:
        print()
        sys.exit(0)
#  OSC.send(target, "/rnbo/inst/0/params/voice-mode/normalized", final_value)
