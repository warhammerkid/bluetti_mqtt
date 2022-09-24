from enum import Enum, unique
from typing import List
from ..commands import QueryRangeCommand
from .bluetti_device import BluettiDevice
from .struct import DeviceStruct


@unique
class LedMode(Enum):
    LOW = 1
    HIGH = 2
    SOS = 3
    OFF = 4


class EB3A(BluettiDevice):
    def __init__(self, address: str, sn: str):
        self.struct = DeviceStruct()

        # Page 0x00 - Core
        self.struct.add_string_field('device_type', 0x00, 0x0A, 6)
        self.struct.add_sn_field('serial_number', 0x00, 0x11)
        self.struct.add_version_field('arm_version', 0x00, 0x17)
        self.struct.add_version_field('dsp_version', 0x00, 0x19)
        self.struct.add_uint_field('dc_input_power', 0x00, 0x24)
        self.struct.add_uint_field('ac_input_power', 0x00, 0x25)
        self.struct.add_uint_field('ac_output_power', 0x00, 0x26)
        self.struct.add_uint_field('dc_output_power', 0x00, 0x27)
        self.struct.add_decimal_field('power_generation', 0x00, 0x29, 1) # Total power generated since last reset in kwh
        self.struct.add_uint_field('total_battery_percent', 0x00, 0x2B)
        self.struct.add_bool_field('ac_output_on', 0x00, 0x30)
        self.struct.add_bool_field('dc_output_on', 0x00, 0x31)

        # Page 0x00 - Details
        self.struct.add_decimal_field('ac_input_voltage', 0x00, 0x4D, 1)
        self.struct.add_decimal_field('dc_input_voltage', 0x00, 0x56, 1)

        # Page 0x00 - Battery Data
        self.struct.add_uint_field('pack_num_max', 0x00, 0x5B)

        # Page 0x0B - Controls
        self.struct.add_bool_field('ac_output_on', 0x0B, 0xBF)
        self.struct.add_bool_field('dc_output_on', 0x0B, 0xC0)
        self.struct.add_enum_field('led_mode', 0x0B, 0xDA, LedMode)

        super().__init__(address, 'EB3A', sn)

    @property
    def polling_commands(self) -> List[QueryRangeCommand]:
        return [
            QueryRangeCommand(0x00, 0x0A, 0x28),
            QueryRangeCommand(0x00, 0x46, 0x15),
            QueryRangeCommand(0x0B, 0xB9, 0x3D)
        ]

    @property
    def logging_commands(self) -> List[QueryRangeCommand]:
        return [
            QueryRangeCommand(0x00, 0x0A, 0x35),
            QueryRangeCommand(0x00, 0x46, 0x42),
            QueryRangeCommand(0x00, 0x88, 0x4A),
            QueryRangeCommand(0x0B, 0xB9, 0x3D)
        ]
