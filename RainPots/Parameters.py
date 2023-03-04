import urllib.request
import urllib.parse
import requests
import json


class ParamConfig:
    def __init__(self, debug: bool):
        self.config = {}
        self.values_by_path = {}
        self.presets = []
        self.grab_param_values = False
        self.debug = debug
        self.controller_states = []
        self.controller_states_sent = []
        self.PICKUP_VALUE_LOCKED = 0
        self.PICKUP_VALUE_UP = 1
        self.PICKUP_VALUE_DOWN = 2
        for i in range(16):
            self.controller_states.append(self.PICKUP_VALUE_LOCKED)
            self.controller_states_sent.append(False)

    def get_config(self) -> dict:
        return self.config

    def get_presets(self) -> list:
        return self.presets

    def get_values_by_path(self) -> dict:
        return self.values_by_path

    def reset_values_by_path(self) -> None:
        for path in self.values_by_path:
            self.values_by_path[path] = None

    def set_grab_values(self, active: bool) -> None:
        self.grab_param_values = active

    def get_grab_values(self) -> bool:
        return self.grab_param_values

    def load_config(self) -> dict:
        url = 'http://localhost:5678'
        r = requests.get(url)
        full_response = r.json()
        try:
            self.presets = \
                full_response['CONTENTS']['rnbo']['CONTENTS']['inst']['CONTENTS']['0']['CONTENTS']['presets'][
                    'CONTENTS'][
                    'entries']['VALUE']
        except KeyError:
            self.presets = []
        if self.debug:
            print("PRESETS:\n", self.presets, "\n")
        params_dict = full_response['CONTENTS']['rnbo']['CONTENTS']['inst']['CONTENTS']['0']['CONTENTS']['params'][
            'CONTENTS']
        self.config = self._parse_params(params_dict)
        if self.debug:
            print("RNBO Patch Configuration:")
        for unit_index, controller_config in self.config.items():
            if self.debug:
                print("Unit: ", unit_index)
            for controller_index, controller_setting in controller_config.items():
                if self.debug:
                    print("\tCtl: ", controller_index, controller_setting['path'], "center: ",
                          controller_setting['center'])
                self.values_by_path[controller_setting['path']] = None
        if self.debug:
            print()
        return self.config

    def set_controller_state(self, pot_unit, state):
        if self.controller_states[pot_unit] != state:
            self.controller_states_sent[pot_unit] = False
        self.controller_states[pot_unit] = state
        if self.debug:
            print("Setting Controller State: ", pot_unit, self.controller_states[pot_unit])

    def _parse_params(self, json_response) -> dict:
        param_path_dict = {}
        for key, value in json_response.items():
            if 'normalized' in value['CONTENTS'].keys():
                full_path = value['CONTENTS']['normalized']['FULL_PATH']
                if 'meta' in value['CONTENTS'].keys():
                    meta_config = value['CONTENTS']['meta']
                    meta_value = json.loads(meta_config['VALUE'])
                    if 'rainpots' in meta_value.keys():
                        rainpots_config = meta_value['rainpots']
                        if 'unit' in rainpots_config and 'ctl' in rainpots_config:
                            unit_index = rainpots_config['unit']
                            center = False
                            if 'center' in rainpots_config:
                                center = (rainpots_config['center'] > 0)
                            ctl_index = rainpots_config['ctl']
                            if unit_index not in param_path_dict.keys():
                                param_path_dict[unit_index] = {}
                            if ctl_index not in param_path_dict[unit_index].keys():
                                param_path_dict[unit_index][ctl_index] = {'path': full_path, 'center': center}

            else:
                sub_dict = self._parse_params(value['CONTENTS'])
                # merging dicts
                for sub_unit_index in sub_dict:
                    if sub_unit_index not in param_path_dict.keys():
                        param_path_dict[sub_unit_index] = {}
                    for sub_ctl_index in sub_dict[sub_unit_index]:
                        param_path_dict[sub_unit_index][sub_ctl_index] = sub_dict[sub_unit_index][sub_ctl_index]
                # param_path_dict = param_path_dict | sub_dict

        return param_path_dict

    def get_normalized_value(self, rainpots_unit, controller, value) -> float:
        normalized_value = -1
        center_margin = 0.05

        if rainpots_unit in self.config.keys():
            if controller in self.config[rainpots_unit]:
                normalized_value = value / 511
                if self.config[rainpots_unit][controller]['center']:
                    if abs(normalized_value - 0.5) <= center_margin:
                        normalized_value = 0.5
                    elif normalized_value > 0.5 + center_margin:
                        normalized_value = self._scale(normalized_value, 0.5 + center_margin, 1., 0.5, 1.)
                    elif normalized_value < 0.5 - center_margin:
                        normalized_value = self._scale(normalized_value, 0., 0.5 - center_margin, 0., 0.5)

            normalized_value = int(normalized_value * 1000) / 1000.0
        return normalized_value

    def _scale(self, x, in_min, in_max, out_min, out_max) -> float:
        mapped = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
        return self._clip(mapped, out_min, out_max)

    @staticmethod
    def _clip(x, min_val, max_val) -> float:
        if x > max_val:
            x = max_val
        if x < min_val:
            x = min_val
        return x

    @staticmethod
    def is_button(ctl) -> bool:
        return ctl < 6
