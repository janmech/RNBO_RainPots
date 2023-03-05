import serial
import time
import sys


class Sender:
    def __init__(self, params, serial_port, debug: bool):
        self.param = params
        self.serial_port = serial_port
        self.debug = debug
        self.meter_state = [0, 0]

    def send_button_values(self):
        button_out_states = {}
        # 1. get configured button controllers
        for unit_index, unit_data in self.param.get_config().items():
            for controller_index, controller_data in unit_data.items():
                if 0 <= controller_index <= 5:
                    path = controller_data['path']
                    values_by_path = self.param.get_values_by_path()

                    if path in values_by_path.keys():
                        value = values_by_path[path]
                        # Create Dict entry if it doesn't exist
                        if unit_index not in button_out_states.keys():
                            button_out_states[unit_index] = {}

                        button_out_states[unit_index][controller_index] = value
        command_values = []
        for pot_unit, unit_data in button_out_states.items():
            command_values = []
            start_condition = 240 + int(pot_unit)
            command_values.append(start_condition)
            command_values.append(229)  # 0xE5 = SET BUTTON VALUES (DECIMAL 229)
            for btn_index in range(6):
                if btn_index in unit_data.keys() and unit_data[btn_index] is not None:
                    if self.debug:
                        print("SERIAL VALUE SENDING: ", btn_index, unit_data, unit_data[btn_index])
                    value = self.format_value(btn_index, unit_data[btn_index])
                else:
                    value = 15  # 0x0F - Don't Set Button
                command_values.append(value)
                if self.debug:
                    print("Sending Command Button Values: ", command_values)
                self.serial_port.write(bytes(command_values))
                time.sleep(0.005)

    def send_meter(self, meter_index: int, meter_value: int):
        try:
            if self.meter_state[meter_index] != meter_value:
                command_values = []
                start_condition = 240 + int(0) # Meter Module is always defined as Module 0
                command_values.append(start_condition)
                command_values.append(230)  # 0xE6 = METER VALUE (DECIMAL 230)
                command_values.append(meter_index)  # Data Byte 1: Meter Index
                command_values.append(meter_value)  # Data Byte 2: Meter Value
                self.serial_port.write(bytes(command_values))
                self.meter_state[meter_index] = meter_value
        except Exception:
            # Do nothing. We just don't want the code to break
            pass

        pass

    @staticmethod
    def format_value(btn_index: int, raw_value: float) -> int:
        formatted_value = 0
        if btn_index != 1:
            if raw_value > 0:
                formatted_value = 1
        else:
            if raw_value == 0:
                formatted_value = 0
            else:
                formatted_value = round(1. / raw_value)
        formatted_value = int(formatted_value)
        return formatted_value


"""
    def send_pickup(self, pot_unit):
        # if not self.param.controller_states_sent[pot_unit]:
        command_values = []
        start_condition = 240 + int(pot_unit)
        command_values.append(start_condition)
        command_values.append(230)  # 0xE6 = SIGNAL VALUE PICKUP (DECIMAL 230)
        command_values.append(self.param.controller_states[pot_unit]) # Data Byte 1: Direction
        self.param.controller_states_sent[pot_unit] = True
        if self.debug:
            print("Sending Command Value Pickup: ", command_values)
        self.serial_port.write(bytes(command_values))
"""
