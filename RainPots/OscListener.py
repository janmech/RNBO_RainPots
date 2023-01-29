from liblo import *
import sys
import time
import json


class Listener(ServerThread):
    def __init__(self, port, params, serial_sender, debug: bool):
        self.params = params
        self.grab_param_values = False
        self.debug = debug
        self.serial_sender = serial_sender
        ServerThread.__init__(self, port)
    """
    @make_method('/rnbo/inst/0/messages/out/mod-env-1', 'f')
    def env_callback(self, path, f):
        pass
        # print("rmod-env-1 %f" % f[0])
    """

    @make_method('/rnbo/inst/0/messages/out/reload', 'f')
    def load_preset(self, path, value):
        print("RELOAD FLAG: ", path,  value)
        if value[0] == 1:  # preset loading has started
            if self.debug:
                print("PRESET RELOAD ---START---")
                print("Resetting Button Values and starting collecting")
            self.params.reset_values_by_path()
            self.params.set_grab_values(True)
        if value[0] == 0:
            if self.debug:
                print("PRESET RELOAD ---FINISHED---")
                print(self.params.get_values_by_path())
            self.params.set_grab_values(False)
            time.sleep(0.1)
            self.serial_sender.send_button_values()

    @make_method('/rnbo/resp', None)
    def response(self, path, args):
        print("\t RESPONSE ENDPOINT:", args)
        try:  # Try to reload config after new export to target
            response = json.loads(args[0])
            message = response['result']['message']
            progress = response['result']['progress']
            if self.debug:
                print("\tMessage:", message)
                print("\tProgress:", progress)
            if message == 'loaded' and progress == 100:
                self.params.load_config()
        except Exception:
            pass

    @make_method(None, None)
    def fallback(self, path, args):
        if self.params.get_grab_values():
            if self.debug:
                print("fallback", path, args)
            if path.endswith('/normalized') and path in self.params.get_values_by_path().keys():
                truncated = int(args[0] * 1000) / 1000
                self.params.get_values_by_path()[path] = truncated
                if self.debug:
                    print("   -->Setting Value:   ", path, self.params.get_values_by_path()[path])
        elif self.debug:
            print("\t OSC Message:", path, args)
