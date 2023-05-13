from enum import Enum, unique
from typing import List
from ..commands import ReadHoldingRegisters
from .bluetti_device import BluettiDevice
from .struct import DeviceStruct


@unique
class OutputMode(Enum):
    STOP = 0
    INVERTER_OUTPUT = 1
    BYPASS_OUTPUT_C = 2
    BYPASS_OUTPUT_D = 3
    LOAD_MATCHING = 4


@unique
class AutoSleepMode(Enum):
    THIRTY_SECONDS = 2
    ONE_MINUTE = 3
    FIVE_MINUTES = 4
    NEVER = 5


class AC200M(BluettiDevice):
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
        self.struct.add_decimal_field('power_generation', 41, 1)  # Total power generated since last reset (kwh)
        self.struct.add_uint_field('total_battery_percent', 43)
        self.struct.add_bool_field('ac_output_on', 48)
        self.struct.add_bool_field('dc_output_on', 49)

        # Details
        self.struct.add_enum_field('ac_output_mode', 70, OutputMode)
        self.struct.add_uint_field('internal_ac_voltage', 71)
        self.struct.add_decimal_field('internal_current_one', 72, 1)
        self.struct.add_uint_field('internal_power_one', 73)
        self.struct.add_decimal_field('internal_ac_frequency', 74, 1)
        self.struct.add_uint_field('internal_dc_input_voltage', 86)
        self.struct.add_decimal_field('internal_dc_input_power', 87, 1)
        self.struct.add_decimal_field('internal_dc_input_current', 88, 2)

        # Battery Data
        self.struct.add_uint_field('pack_num_max', 91)
        self.struct.add_decimal_field('total_battery_voltage', 92, 2)
        self.struct.add_uint_field('pack_num', 96)
        self.struct.add_decimal_field('pack_voltage', 98, 2)  # Full pack voltage
        self.struct.add_uint_field('pack_battery_percent', 99)
        self.struct.add_decimal_array_field('cell_voltages', 105, 16, 2)

        # Controls
        self.struct.add_uint_field('pack_num', 3006)
        self.struct.add_bool_field('ac_output_on', 3007)
        self.struct.add_bool_field('dc_output_on', 3008)
        # 3031-3033 is the current device time & date without a timezone
        self.struct.add_bool_field('power_off', 3060)
        self.struct.add_enum_field('auto_sleep_mode', 3061, AutoSleepMode)

        super().__init__(address, 'AC200M', sn)

    @property
    def pack_num_max(self):
        return 3

    @property
    def polling_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(10, 40),
            ReadHoldingRegisters(70, 21),
            ReadHoldingRegisters(3001, 61),
        ]

    @property
    def pack_polling_commands(self) -> List[ReadHoldingRegisters]:
        return [ReadHoldingRegisters(91, 37)]

    @property
    def logging_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(0, 70),
            ReadHoldingRegisters(70, 21),
            ReadHoldingRegisters(3001, 61),
        ]

    @property
    def pack_logging_commands(self) -> List[ReadHoldingRegisters]:
        return [ReadHoldingRegisters(91, 119)]

    @property
    def writable_ranges(self) -> List[range]:
        return [range(3000, 3062)]
