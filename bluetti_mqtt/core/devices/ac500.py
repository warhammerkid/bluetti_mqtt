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
class UpsMode(Enum):
    CUSTOMIZED = 1
    PV_PRIORITY = 2
    STANDARD = 3
    TIME_CONTROL = 4


@unique
class MachineAddress(Enum):
    SLAVE = 0
    MASTER = 1


@unique
class AutoSleepMode(Enum):
    THIRTY_SECONDS = 2
    ONE_MINUTE = 3
    FIVE_MINUTES = 4
    NEVER = 5


class AC500(BluettiDevice):
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
        self.struct.add_decimal_field('internal_ac_voltage', 71, 1)
        self.struct.add_decimal_field('internal_current_one', 72, 1)
        self.struct.add_uint_field('internal_power_one', 73)
        self.struct.add_decimal_field('internal_ac_frequency', 74, 2)
        self.struct.add_decimal_field('internal_current_two', 75, 1)
        self.struct.add_uint_field('internal_power_two', 76)
        self.struct.add_decimal_field('ac_input_voltage', 77, 1)
        self.struct.add_decimal_field('internal_current_three', 78, 1)
        self.struct.add_uint_field('internal_power_three', 79)
        self.struct.add_decimal_field('ac_input_frequency', 80, 2)
        self.struct.add_decimal_field('internal_dc_input_voltage', 86, 1)
        self.struct.add_uint_field('internal_dc_input_power', 87)
        self.struct.add_decimal_field('internal_dc_input_current', 88, 1)

        # Battery Data
        self.struct.add_uint_field('pack_num_max', 91)
        self.struct.add_decimal_field('total_battery_voltage', 92, 1)
        self.struct.add_uint_field('pack_num', 96)
        self.struct.add_decimal_field('pack_voltage', 98, 2)  # Full pack voltage
        self.struct.add_uint_field('pack_battery_percent', 99)
        self.struct.add_decimal_array_field('cell_voltages', 105, 16, 2)

        # Controls
        self.struct.add_enum_field('ups_mode', 3001, UpsMode)
        self.struct.add_bool_field('split_phase_on', 3004)
        self.struct.add_enum_field('split_phase_machine_mode', 3005, MachineAddress)
        self.struct.add_uint_field('pack_num', 3006)
        self.struct.add_bool_field('ac_output_on', 3007)
        self.struct.add_bool_field('dc_output_on', 3008)
        self.struct.add_bool_field('grid_charge_on', 3011)
        self.struct.add_bool_field('time_control_on', 3013)
        self.struct.add_uint_field('battery_range_start', 3015)
        self.struct.add_uint_field('battery_range_end', 3016)
        # 3031-3033 is the current device time & date without a timezone
        self.struct.add_bool_field('bluetooth_connected', 3036)
        # 3039-3056 is the time control programming
        self.struct.add_enum_field('auto_sleep_mode', 3061, AutoSleepMode)

        super().__init__(address, 'AC500', sn)

    @property
    def pack_num_max(self):
        return 6

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
            ReadHoldingRegisters(3000, 62),
        ]

    @property
    def pack_logging_commands(self) -> List[ReadHoldingRegisters]:
        return [ReadHoldingRegisters(91, 119)]

    @property
    def writable_ranges(self) -> List[range]:
        return [range(3000, 3062)]
