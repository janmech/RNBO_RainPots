#!/usr/bin/env python3
# coding=utf-8
import time
import argparse
import sys
import serial


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def invalid_choice():
    print(bcolors.FAIL + "Invalid choice\n" + bcolors.ENDC)


def enter_board_index() -> int:
    try:
        index = int(input(bcolors.OKBLUE + "Enter RainPot board index to configure: " + bcolors.ENDC))
        if index < 0:
            print(bcolors.FAIL + "Invalid Board index" + bcolors.ENDC)
            enter_board_index()
        return index
    except ValueError:
        print(bcolors.FAIL + "Invalid Board index" + bcolors.ENDC)
        enter_board_index()


def chose_operation(index: int) -> int:
    print(bcolors.HEADER + "Chose Operation for RainPot Board " + bcolors.ENDC + str(index) + ": \n")
    print("[0] Exit")
    print("[1] Calibrate Knobs")
    print("[2] Set Button Modes")
    print("[3] Activate/Deactivate Controller")
    try:
        op = int(input(bcolors.HEADER + "Operation: " + bcolors.ENDC))
        if op == 0:
            print("Exiting Configuration Tool")
            sys.exit(0)
        if not 1 <= op <= 3:
            invalid_choice()
            chose_operation(index)
        return op
    except ValueError:
        invalid_choice()
        chose_operation(index)


def calibration_position() -> str:
    try:
        pos_string = ['min', 'center', 'max']
        print(bcolors.WARNING + "\nSelected Operation: " + bcolors.ENDC + "Calibrate Knobs")
        print(bcolors.WARNING + "Set all knobs to position, then indicate which one it is." + bcolors.ENDC + "\n")
        print("[1] Minimum Position")
        print("[2] Center Position")
        print("\tFor knobs WITH center detent.")
        print("\tSet knobs WITHOUT center detent to minimum position.")
        print("[3] Maximum Position")
        pos = int(input(bcolors.HEADER + "Position: " + bcolors.ENDC))
        if not 1 <= pos <= 3:
            invalid_choice()
            calibration_position()
        return pos_string[pos - 1]
    except ValueError:
        invalid_choice()
        calibration_position()


def button_modes() -> list:
    print(bcolors.WARNING + "\nSelected Operation: " + bcolors.ENDC + "Set Button Modes\n")
    modes = [1, 5, 1, 1, 1, 1, 1, 0]
    use_radio_group = False
    display_zero_radio_group = False
    for btn_index in range(6):
        if btn_index == 1:
            answer = input("Set Max Steps for Button 1 [2 - 5] (default: 5) ")
            try:
                max_steps = int(answer)
            except ValueError:
                max_steps = 5
            modes[1] = max_steps
            answer = input("Display 0 (zero) for Button 1 [y/n] (default: y) ")
            if answer == 'n':
                modes[6] = 0
        elif btn_index == 2:
            answer = input("Use Buttons 2 - 4 as Radio Group [y/n] (default n) ")
            if answer == 'y':
                use_radio_group = True
                modes[2] = 4
            if use_radio_group:
                answer = input("Display 0 (zero) for Radio Group [y/n] (default n) ")
                if answer == 'y':
                    display_zero_radio_group = True

        elif not use_radio_group:
            print("\n" + bcolors.HEADER + "Set Mode for Button " + bcolors.ENDC + str(btn_index) + ":")
            print("[0] Toggle (default)")
            print("[1] Momentary")
            answer = input(bcolors.HEADER + "Button Mode: " + bcolors.ENDC)
            mode = 0
            if answer == '1':
                mode = 1
            modes[btn_index] = mode
        else:
            # We are using Radio Group, set all subsequent buttons to CONTROLLER_MODE_RADIO_GROUP (4)
            modes[btn_index] = 4

        if display_zero_radio_group:
            modes[7] = 1
        print("MODES:" , modes)
    return modes


def ask_ctl_status(index: int) -> int:
    state = 1
    answer = input(bcolors.OKCYAN + "Set Controller " + str(index) + " active? " + bcolors.ENDC + "[y/n] (default: y) ")
    if answer.lower() == 'n' or answer == '0':
        state = 0
    print("STATE: ", state)
    return state


def controller_states() -> list:
    states = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ]
    for ctl_index in range(14):
        states[ctl_index] = ask_ctl_status(ctl_index)
    return states


def get_button_modes_command(board_index: int, modes: list) -> list:
    msg_bytes = []
    status_byte = 240 + board_index  # COMMAND START BYTE
    msg_bytes.append(status_byte)
    # MSG_CONTROLLER_MODE 0xE3 (DECIMAL: 243)
    msg_bytes.append(227)
    for btn_mode in modes:
        msg_bytes.append(btn_mode)
    return msg_bytes


def get_controller_states_command(board_index: int, states: list) -> list:
    msg_bytes = []
    status_byte = 240 + board_index  # COMMAND START BYTE
    msg_bytes.append(status_byte)
    #  MSG_CONTROLLER_STATUS 0xE4 (DECIMAL: 228)
    msg_bytes.append(228)
    for btn_state in states:
        msg_bytes.append(btn_state)
    return msg_bytes


def get_command_calibration(board_index: int, position: str) -> list:
    msg_bytes = []
    status_byte = 240 + board_index  # COMMAND START BYTE
    msg_bytes.append(status_byte)
    if position == 'min':
        msg_bytes.append(224)  # 0XE0 = CALIBRATE MIN (DECIMAL 224)
    if position == 'center':
        msg_bytes.append(225)  # 0XE1 = CALIBRATE CENTER (DECIMAL 225)
    if position == 'max':
        msg_bytes.append(226)  # 0XE2 = CALIBRATE MAX (DECIMAL 242)
    return msg_bytes


def send_command(cmd_values: list, port: serial.serialposix.Serial) -> None:
    cmd_bytes = bytes(cmd_values)
    print("Sending configuration:", cmd_bytes)
    port.write(bytes(cmd_bytes))


def main():
    try:
        print(bcolors.WARNING)
        print("**************************************")
        print("*** RainPots Board Config Utility  ***")
        print("**************************************")
        print(bcolors.ENDC)

        port = serial.Serial("/dev/ttyS0", baudrate=380400)
        if port.isOpen():
            port.close()
        if not port.isOpen():
            port.open()

        board_index = enter_board_index()
        print(bcolors.WARNING)
        print("\nSelected Board: %d" % board_index)
        print(bcolors.ENDC)
        operation = chose_operation(board_index)
        if operation == 1:
            cal_pos = calibration_position()
            print("Calibrating Knobs")
            cmd_values = get_command_calibration(board_index, cal_pos)
            send_command(cmd_values, port)
        if operation == 2:
            btn_modes = button_modes()

            btn_modes_display = btn_modes.copy()
            display_zero = btn_modes_display.pop()

            print("Setting Button Modes/Steps to: ", btn_modes_display)
            print("Display 0 (zero) on Button 1: ", display_zero)
            cmd_values = get_button_modes_command(board_index, btn_modes)
            send_command(cmd_values, port)

        if operation == 3:
            ctl_states = controller_states()
            print("Setting Controller States to: ", ctl_states)
            cmd_values = get_controller_states_command(board_index, ctl_states)
            send_command(cmd_values, port)
        repeat = input("Would you like to configure another board? [y/n] ")
        if repeat.lower() == 'y':
            main()
        sys.exit(0)
    except KeyboardInterrupt:
        print(bcolors.ENDC + "\n")
        sys.exit(0)


if __name__ == '__main__':
    main()
