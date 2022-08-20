from enum import Enum, unique
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
class AutoSleepMode(Enum):
    THIRTY_SECONDS = 2
    ONE_MINUTE = 3
    FIVE_MINUTES = 4
    NEVER = 5


class EP500P(BluettiDevice):
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
        self.struct.add_enum_field('ac_output_mode', 0x00, 0x46, OutputMode)
        self.struct.add_decimal_field('internal_ac_voltage', 0x00, 0x47, 1)
        self.struct.add_decimal_field('internal_current_one', 0x00, 0x48, 1)
        self.struct.add_uint_field('internal_power_one', 0x00, 0x49)
        self.struct.add_decimal_field('internal_ac_frequency', 0x00, 0x4A, 2)
        self.struct.add_decimal_field('internal_current_two', 0x00, 0x4B, 1)
        self.struct.add_uint_field('internal_power_two', 0x00, 0x4C)
        self.struct.add_decimal_field('ac_input_voltage', 0x00, 0x4D, 1)
        self.struct.add_decimal_field('internal_current_three', 0x00, 0x4E, 1)
        self.struct.add_uint_field('internal_power_three', 0x00, 0x4F)
        self.struct.add_decimal_field('ac_input_frequency', 0x00, 0x50, 2)
        self.struct.add_decimal_field('dc_input_voltage', 0x00, 0x56, 1)
        self.struct.add_uint_field('dc_input_power', 0x00, 0x57)
        self.struct.add_decimal_field('dc_input_current', 0x00, 0x58, 1)

        # Page 0x00 - Battery Data
        self.struct.add_uint_field('pack_num_max', 0x00, 0x5B)
        self.struct.add_decimal_field('pack_voltage', 0x00, 0x5C, 1) # Full pack voltage
        self.struct.add_uint_field('pack_battery_percent', 0x00, 0x5E)
        self.struct.add_uint_field('pack_num', 0x00, 0x60)
        self.struct.add_decimal_array_field('cell_voltages', 0x00, 0x69, 16, 2)

        # Page 0x0B - Controls
        self.struct.add_enum_field('ups_mode', 0x0B, 0xB9, UpsMode)
        self.struct.add_uint_field('pack_num', 0x0B, 0xBE)
        self.struct.add_bool_field('ac_output_on', 0x0B, 0xBF)
        self.struct.add_bool_field('dc_output_on', 0x0B, 0xC0)
        self.struct.add_bool_field('grid_charge_on', 0x0B, 0xC3)
        self.struct.add_bool_field('time_control_on', 0x0B, 0xC5)
        self.struct.add_uint_field('battery_range_start', 0x0B, 0xC7)
        self.struct.add_uint_field('battery_range_end', 0x0B, 0xC8)
        # 0xD7-0xD9 is the current device time & date without a timezone
        self.struct.add_bool_field('bluetooth_connected', 0x0B, 0xDC)
        # 0xDF-0xF0 is the time control programming
        self.struct.add_enum_field('auto_sleep_mode', 0x0B, 0xF5, AutoSleepMode)

        super().__init__(address, 'EP500P', sn)
