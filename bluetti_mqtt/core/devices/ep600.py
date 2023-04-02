from typing import List
from ..commands import QueryRangeCommand
from .bluetti_device import BluettiDevice
from .struct import DeviceStruct


class EP600(BluettiDevice):
    def __init__(self, address: str, sn: str):
        self.struct = DeviceStruct()

        self.struct.add_uint_field('total_battery_percent', 0x00, 0x66)
        self.struct.add_swap_string_field('device_type', 0x00, 0x6E, 6)
        self.struct.add_sn_field('serial_number', 0x00, 0x74)
        self.struct.add_decimal_field('power_generation', 0x00, 0x9A, 1)  # Total power generated since last reset (kwh)
        self.struct.add_swap_string_field('device_type', 0x04, 0x4D, 6)
        self.struct.add_sn_field('serial_number', 0x04, 0x53)
        self.struct.add_decimal_field('power_generation', 0x04, 0xB2, 1)  # Total power generated since last reset (kwh)
        # 0x07D1-0x07D3 is the current device time & date without a timezone
        self.struct.add_uint_field('battery_range_start', 0x07, 0xE6)
        self.struct.add_uint_field('battery_range_end', 0x07, 0xE7)
        self.struct.add_uint_field('max_ac_input_power', 0x08, 0xA5)
        self.struct.add_uint_field('max_ac_input_current', 0x08, 0xA6)
        self.struct.add_uint_field('max_ac_output_power', 0x08, 0xA7)
        self.struct.add_uint_field('max_ac_output_current', 0x08, 0xA8)
        self.struct.add_swap_string_field('battery_type', 0x17, 0xD5, 6)
        self.struct.add_sn_field('battery_serial_number', 0x17, 0xDB)
        self.struct.add_version_field('bcu_version', 0x18, 0x1F)
        self.struct.add_version_field('bmu_version', 0x18, 0x22)
        self.struct.add_version_field('safety_module_version', 0x18, 0x25)
        self.struct.add_version_field('high_voltage_module_version', 0x18, 0x28)

        super().__init__(address, 'EP600', sn)

    @property
    def polling_commands(self) -> List[QueryRangeCommand]:
        return [
            QueryRangeCommand(0x00, 0x64, 0x3E),
            QueryRangeCommand(0x07, 0xE6, 0x02),
        ]

    @property
    def logging_commands(self) -> List[QueryRangeCommand]:
        return [
            QueryRangeCommand(0x00, 0x64, 0x3E),
            QueryRangeCommand(0x04, 0x4C, 0x33),
            QueryRangeCommand(0x04, 0xB0, 0x50),
            QueryRangeCommand(0x05, 0x14, 0x1F),
            QueryRangeCommand(0x05, 0x78, 0x30),
            QueryRangeCommand(0x05, 0xDC, 0x1E),
            QueryRangeCommand(0x07, 0xD0, 0x30),
            QueryRangeCommand(0x08, 0x00, 0x29),
            QueryRangeCommand(0x08, 0x98, 0x29),
            QueryRangeCommand(0x08, 0xFC, 0x04),
            QueryRangeCommand(0x08, 0xFC, 0x04),
            QueryRangeCommand(0x09, 0x00, 0x20),
            QueryRangeCommand(0x17, 0x70, 0x20),
            QueryRangeCommand(0x17, 0x70, 0x2C),
            QueryRangeCommand(0x18, 0x00, 0x3C),
            QueryRangeCommand(0x18, 0x9C, 0x64),
        ]
