from decimal import Decimal
from enum import Enum, unique
import struct
from .commands import QueryRangeCommand


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


class MidStatusPageParser(DataParser):
    inverter_mode: OutputMode
    ac_input_voltage: Decimal
    ac_input_frequency: Decimal
    current_pack: int
    pack_battery_percent: int

    def __init__(self, data: bytes):
        super().__init__(0x46, data)

    def parse(self):
        self.ac_output_mode = OutputMode(self._parse_uint_field(0x46))
        self.ac_input_voltage = self._parse_decimal_field(0x4D, 1)
        self.ac_input_frequency = self._parse_decimal_field(0x50, 2)
        self.pack_battery_percent = self._parse_uint_field(0x5E)
        self.pack_num = self._parse_uint_field(0x60)
        return self

    @staticmethod
    def build_query_command():
        return QueryRangeCommand(0x00, 0x46, 0x42)


class ControlPageParser(DataParser):
    ups_mode: UpsMode
    current_pack: int
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
        self.current_pack = self._parse_uint_field(0xBE)
        self.ac_output_on = self._parse_bool_field(0xBF)
        self.dc_output_on = self._parse_bool_field(0xC0)
        self.grid_charge_on = self._parse_bool_field(0xC3)
        self.time_control_on = self._parse_bool_field(0xC5)
        self.battery_range_start = self._parse_uint_field(0xC7)
        self.battery_range_end = self._parse_uint_field(0xC8)
        self.auto_sleep_mode = AutoSleepMode(self._parse_uint_field(0xF5))
        return self

    @staticmethod
    def build_query_command():
        return QueryRangeCommand(0x0B, 0xB9, 0x3D)
