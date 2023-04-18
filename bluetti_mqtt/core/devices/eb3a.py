from enum import Enum, unique
from typing import List
from ..commands import ReadHoldingRegisters
from .bluetti_device import BluettiDevice
from .struct import DeviceStruct


@unique
class LedMode(Enum):
    LOW = 1
    HIGH = 2
    SOS = 3
    OFF = 4


@unique
class EcoShutdown(Enum):
    ONE_HOUR = 1
    TWO_HOURS = 2
    THREE_HOURS = 3
    FOUR_HOURS = 4


@unique
class ChargingMode(Enum):
    STANDARD = 0
    SILENT = 1
    TURBO = 2


class EB3A(BluettiDevice):
    def __init__(self, address: str, sn: str):
        self.struct = DeviceStruct()

        # Core
        self.struct.add_string_field('device_type', 10, 6)
        self.struct.add_sn_field('serial_number', 17)
        self.struct.add_version_field('arm_version', 23)
        self.struct.add_version_field('dsp_version', 25)
        self.struct.add_uint_field('dc_input_power', 36)
        self.struct.add_uint_field('ac_input_power', 37)
        self.struct.add_uint_field('ac_output_power', 38)
        self.struct.add_uint_field('dc_output_power', 39)
        self.struct.add_uint_field('total_battery_percent', 43)
        self.struct.add_bool_field('ac_output_on', 48)
        self.struct.add_bool_field('dc_output_on', 49)

        # Details
        self.struct.add_decimal_field('ac_input_voltage', 77, 1)
        self.struct.add_decimal_field('internal_dc_input_voltage', 86, 2)

        # Battery Data
        self.struct.add_uint_field('pack_num_max', 91)

        # Controls
        self.struct.add_bool_field('ac_output_on', 3007)
        self.struct.add_bool_field('dc_output_on', 3008)
        self.struct.add_enum_field('led_mode', 3034, LedMode)
        self.struct.add_bool_field('power_off', 3060)
        self.struct.add_bool_field('eco_on', 3063)
        self.struct.add_enum_field('eco_shutdown', 3064, EcoShutdown)
        self.struct.add_enum_field('charging_mode', 3065, ChargingMode)
        self.struct.add_bool_field('power_lifting_on', 3066)

        super().__init__(address, 'EB3A', sn)

    @property
    def polling_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(10, 40),
            ReadHoldingRegisters(70, 21),
            ReadHoldingRegisters(3034, 1),
            ReadHoldingRegisters(3060, 7)
        ]

    @property
    def logging_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(10, 53),
            ReadHoldingRegisters(70, 66),
            ReadHoldingRegisters(136, 74),
            ReadHoldingRegisters(3000, 67)
        ]

    @property
    def writable_ranges(self) -> List[range]:
        return [range(3000, 3067)]
