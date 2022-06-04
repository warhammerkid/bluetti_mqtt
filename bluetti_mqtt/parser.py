from decimal import Decimal
from enum import Enum, unique
import struct
from typing import List, Tuple
from bluetti_mqtt.commands import QueryRangeCommand


@unique
class OutputMode(Enum):
    STOP = 0
    INVERTER_OUTPUT = 1
    BYPASS_OUTPUT_C = 2
    BYPASS_OUTPUT_D = 3
    LOAD_MATCHING = 4


@unique
class UpsMode(Enum):
    UNAVAILABLE = 0
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


class DataParser:
    def __init__(self, offset: int, data: bytes):
        self.offset = offset
        self.data = data

    """Parses the data and returns the parser for chaining"""
    def parse(self):
        return self

    def _parse_bool_field(self, offset: int) -> bool:
        return self._parse_uint_field(offset) == 1

    def _parse_uint_field(self, offset: int) -> int:
        return struct.unpack('!H', self._read_data(offset, 1))[0]

    def _parse_decimal_field(self, offset: int, scale: int) -> float:
        d = Decimal(self._parse_uint_field(offset))
        return d / 10 ** scale

    def _read_data(self, offset: int, size: int):
        data_start = 2 * (offset - self.offset)
        return self.data[data_start:data_start + 2 * size]


class LowerStatusPageParser(DataParser):
    device_type: str
    serial_number: int
    arm_version: Decimal
    dsp_version: Decimal
    dc_input_power: int
    ac_input_power: int
    ac_output_power: int
    dc_output_power: int
    total_battery_percent: int
    ac_output_on: bool
    dc_output_on: bool

    def __init__(self, data: bytes):
        super().__init__(0x00, data)

    def parse(self):
        self.device_type = self._parse_string_field(0x0A, 6)
        self.serial_number = self._parse_sn_field(0x11)
        self.arm_version = self._parse_version_field(0x17)
        self.dsp_version = self._parse_version_field(0x19)
        self.dc_input_power = self._parse_uint_field(0x24)
        self.ac_input_power = self._parse_uint_field(0x25)
        self.ac_output_power = self._parse_uint_field(0x26)
        self.dc_output_power = self._parse_uint_field(0x27)
        self.total_battery_percent = self._parse_uint_field(0x2B)
        self.ac_output_on = self._parse_bool_field(0x30)
        self.dc_output_on = self._parse_bool_field(0x31)
        return self

    @staticmethod
    def build_query_command():
        return QueryRangeCommand(0x00, 0x00, 0x46)

    def __repr__(self):
        return (
            f'LowerStatusPageParser(device_type={self.device_type},'
            f' serial_number={self.serial_number},'
            f' arm_version={self.arm_version},'
            f' dsp_version={self.dsp_version},'
            f' dc_input_power={self.dc_input_power}W,'
            f' ac_input_power={self.ac_input_power}W,'
            f' ac_output_power={self.ac_output_power}W,'
            f' dc_output_power={self.dc_output_power}W,'
            f' total_battery_percent={self.total_battery_percent}%,'
            f' ac_output_on={self.ac_output_on},'
            f' dc_output_on={self.dc_output_on})'
        )

    """Parses a fixed-width null-terminated string"""
    def _parse_string_field(self, offset: int, size: int):
        data = self._read_data(offset, size)
        return data.rstrip(b'\0').decode('ascii')

    def _parse_sn_field(self, offset: int) -> int:
        data = self._read_data(offset, 4)
        values = struct.unpack('!4H', data)
        return values[0] + (values[1] << 16) + (values[2] << 32) + (values[3] << 48)

    def _parse_version_field(self, offset: int):
        data = self._read_data(offset, 2)
        values = struct.unpack('!2H', data)
        return Decimal(values[0] + (values[1] << 16)) / 100


class MidStatusPageParser(DataParser):
    ac_output_mode: OutputMode
    internal_ac_voltage: Decimal
    internal_current_one: Decimal
    internal_power_one: int
    internal_ac_frequency: Decimal
    internal_current_two: Decimal
    internal_power_two: int
    ac_input_voltage: Decimal
    internal_current_three: Decimal
    internal_power_three: int
    ac_input_frequency: Decimal
    dc_input_voltage: Decimal
    dc_input_power: int
    dc_input_current: Decimal
    pack_num_max: int
    pack_num: int
    pack_battery_percent: int
    pack_voltages: List[Decimal]

    def __init__(self, data: bytes):
        super().__init__(0x46, data)

    def parse(self):
        self.ac_output_mode = OutputMode(self._parse_uint_field(0x46))
        self.internal_ac_voltage = self._parse_decimal_field(0x47, 1)
        self.internal_current_one = self._parse_decimal_field(0x48, 1)
        self.internal_power_one = self._parse_uint_field(0x49)
        self.internal_ac_frequency = self._parse_decimal_field(0x4A, 2)
        self.internal_current_two = self._parse_decimal_field(0x4B, 1)
        self.internal_power_two = self._parse_uint_field(0x4C)
        self.ac_input_voltage = self._parse_decimal_field(0x4D, 1)
        self.internal_current_three = self._parse_decimal_field(0x4E, 1)
        self.internal_power_three = self._parse_uint_field(0x4F)
        self.ac_input_frequency = self._parse_decimal_field(0x50, 2)
        self.dc_input_voltage = self._parse_decimal_field(0x56, 1)
        self.dc_input_power = self._parse_uint_field(0x57)
        self.dc_input_current = self._parse_decimal_field(0x58, 1)
        self.pack_num_max = self._parse_uint_field(0x5B)
        # 0x5C looks like the current battery pack voltage - decimal:1 or decimal:2 depending on model
        self.pack_battery_percent = self._parse_uint_field(0x5E)
        self.pack_num = self._parse_uint_field(0x60)
        self.pack_voltages = self._parse_voltages_field(0x69, 16)
        return self

    @staticmethod
    def build_query_command():
        return QueryRangeCommand(0x00, 0x46, 0x42)

    def __repr__(self):
        return (
            f'MidStatusPageParser(ac_output_mode={self.ac_output_mode.name},'
            f' internal_ac_voltage={self.internal_ac_voltage}V,'
            f' internal_current_one={self.internal_current_one}A,'
            f' internal_power_one={self.internal_power_one}W,'
            f' internal_ac_frequency={self.internal_ac_frequency}Hz,'
            f' internal_current_two={self.internal_current_two}A,'
            f' internal_power_two={self.internal_power_two}W,'
            f' ac_input_voltage={self.ac_input_voltage}V,'
            f' internal_current_three={self.internal_current_three}A,'
            f' internal_power_three={self.internal_power_three}W,'
            f' ac_input_frequency={self.ac_input_frequency}Hz,'
            f' dc_input_voltage={self.dc_input_voltage}V,'
            f' dc_input_power={self.dc_input_power}W,'
            f' dc_input_current={self.dc_input_current},'
            f' pack_num_max={self.pack_num_max},'
            f' pack_num={self.pack_num},'
            f' pack_battery_percent={self.pack_battery_percent}%,'
            f' pack_voltages={self.pack_voltages})'
        )

    def _parse_voltages_field(self, offset: int, num: int):
        data = self._read_data(offset, num)
        values = list(struct.unpack(f'!{num}H', data))
        return [Decimal(v) / 100 for v in values]


class ControlPageParser(DataParser):
    ups_mode: UpsMode
    pack_num: int
    ac_output_on: bool
    dc_output_on: bool
    grid_charge_on: bool
    time_control_on: bool
    battery_range_start: int
    battery_range_end: int
    auto_sleep_mode: AutoSleepMode

    def __init__(self, data: bytes):
        super().__init__(0xB9, data)

    def parse(self):
        self.ups_mode = UpsMode(self._parse_uint_field(0xB9))
        self.pack_num = self._parse_uint_field(0xBE)
        self.ac_output_on = self._parse_bool_field(0xBF)
        self.dc_output_on = self._parse_bool_field(0xC0)
        self.grid_charge_on = self._parse_bool_field(0xC3)
        self.time_control_on = self._parse_bool_field(0xC5)
        self.battery_range_start = self._parse_uint_field(0xC7)
        self.battery_range_end = self._parse_uint_field(0xC8)
        # 0xD7-0xD9 is the current device time & date without a timezone
        # 0xDF-0xF0 is the time control programming
        self.auto_sleep_mode = AutoSleepMode(self._parse_uint_field(0xF5))
        return self

    @staticmethod
    def build_query_command():
        return QueryRangeCommand(0x0B, 0xB9, 0x3D)

    def __repr__(self):
        return (
            f'ControlPageParser(ups_mode={self.ups_mode.name},'
            f' pack_num={self.pack_num},'
            f' ac_output_on={self.ac_output_on},'
            f' dc_output_on={self.dc_output_on},'
            f' grid_charge_on={self.grid_charge_on},'
            f' time_control_on={self.time_control_on},'
            f' battery_range_start={self.battery_range_start}%,'
            f' battery_range_end={self.battery_range_end}%,'
            f' auto_sleep_mode={self.auto_sleep_mode.name})'
        )
