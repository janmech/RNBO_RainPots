#!/usr/bin/env python3
# coding=utf-8
import time
import argparse
import sys
import serial

if __name__ == '__main__':
    port = serial.Serial("/dev/ttyS0", baudrate=380400)
    if port.isOpen():
        port.close()
    if not port.isOpen():
        port.open()

    board_index = 6
    command_values = []
    start_condition = 240 + board_index
    command_values.append(start_condition)
    command_values.append(229)  # 0xE5 = SET BUTTON VALUES (DECIMAL 229)
    state = 1
    for i in range(6):
        if i == 1:
            command_values.append(2)
        elif i == 2:
            command_values.append(0)
        else:
            command_values.append(state)
            state = 1 - state
    command_bytes = bytes(command_values)
    print("SET BUTTONS: ", command_values, command_bytes)
    port.write(command_bytes)
    time.sleep(5)
    command_values = []
    start_condition = 240 + board_index
    command_values.append(start_condition)
    command_values.append(229)  # 0xE5 = SET BUTTON VALUES (DECIMAL 229)
    state = 0
    for i in range(6):
        if i == 1:
            command_values.append(3)
        elif i == 2:
            command_values.append(3)
        else:
            command_values.append(state)
            state = 1 - state
    command_bytes = bytes(command_values)
    print("SET BUTTONS: ", command_values, command_bytes)
    port.write(command_bytes)
    sys.exit(0)

