import time

import liblo as OSC
import sys
import RainPots.Parameters
import RainPots.SerialSender


# connector=MidiWii.connector.Instance


class Sender:

    def __new__(cls, port: int, params: RainPots.Parameters, serial_sender: RainPots.SerialSender.Sender, debug: bool):
        obj = object.__new__(cls)
        return obj

    def __init__(self, port: int, params: RainPots.Parameters, serial_sender: RainPots.SerialSender.Sender, debug: bool) -> None:
        try:
            self.target = OSC.Address(port)
            self.params = params
            self.serial_sender = serial_sender
            self.debug = debug
        except OSC.AddressError as err:
            print(err)
            sys.exit()

    def add_listener(self, port) -> None:
        OSC.send(self.target, '/rnbo/listeners/add', '127.0.0.1:%d' % port)

    def send_packet(self, packet) -> None:
        rainpots_unit = packet[0] & 0x0f
        controller = packet[1]
        value = (packet[3] << 7) | packet[2]
        normalized_value = self.params.get_normalized_value(rainpots_unit, controller, value)
        if normalized_value != -1:
            path = self.params.get_config()[rainpots_unit][controller]['path']
            try:
                current_param_value = self.params.get_values_by_path()[path]
            except KeyError:
                current_param_value = None

            # Parameter pickup
            # We don't have a value or if it's a button: send the incoming one
            if current_param_value is None or self.params.is_button(controller):
                OSC.send(self.target, path, normalized_value)
                if self.debug:
                    print("Sending: ", path, normalized_value)
            elif abs(current_param_value - normalized_value) <= 0.03:  # We do have a value: Check if it can be picked up
                self.params.get_values_by_path()[path] = None # Param is picked up after preset load: remove the value
                OSC.send(self.target, path, normalized_value)
                if self.debug:
                    print("Sending: ", path, normalized_value)
            elif self.debug:
                print("Needs pickup: %s %f %f" % (path, current_param_value, normalized_value))
        else:
            if self.debug:
                print("Unit %d Controller %d NOT Configured [%d]" % (rainpots_unit, controller, value))

            # TODO: REMOVE CODE
            """
            if rainpots_unit == 0 and 2 <= controller <= 5:
                self._load_preset(controller - 1)
            """

    def get_param(self) -> None:
        OSC.send(self.target, 'rnbo/inst/0/params')

    # TODO DEV CODE. REPLACE WITH REAL LOGIC ONCE THE PRESET MODULE ISD BUILT
    def _load_preset(self, preset_index) -> None:
        preset_name = self.params.get_presets()[preset_index]
        if preset_name == 'INIT':
            preset_name = "Like Bells"
        if self.debug:
            print("Recalling preset: %d: '%s'" % (preset_index, preset_name))
        self.params.reset_values_by_path()
        self.params.set_grab_values(True)
        OSC.send(self.target, '/rnbo/inst/0/presets/load', preset_name)
        time.sleep(1)
        self.params.set_grab_values(False)
        self.serial_sender.send_button_values()
        if self.debug:
            print('Continuing')
