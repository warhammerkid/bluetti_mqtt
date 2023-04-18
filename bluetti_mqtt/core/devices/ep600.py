from typing import List
from ..commands import ReadHoldingRegisters
from .bluetti_device import BluettiDevice
from .struct import DeviceStruct


class EP600(BluettiDevice):
    def __init__(self, address: str, sn: str):
        self.struct = DeviceStruct()

        self.struct.add_uint_field('total_battery_percent', 102)
        self.struct.add_swap_string_field('device_type', 110, 6)
        self.struct.add_sn_field('serial_number', 116)
        self.struct.add_decimal_field('power_generation', 154, 1)  # Total power generated since last reset (kwh)
        self.struct.add_swap_string_field('device_type', 1101, 6)
        self.struct.add_sn_field('serial_number', 1107)
        self.struct.add_decimal_field('power_generation', 1202, 1)  # Total power generated since last reset (kwh)
        # 2001-2003 is the current device time & date without a timezone
        self.struct.add_uint_field('battery_range_start', 2022)
        self.struct.add_uint_field('battery_range_end', 2023)
        self.struct.add_uint_field('max_ac_input_power', 2213)
        self.struct.add_uint_field('max_ac_input_current', 2214)
        self.struct.add_uint_field('max_ac_output_power', 2215)
        self.struct.add_uint_field('max_ac_output_current', 2216)
        self.struct.add_swap_string_field('battery_type', 6101, 6)
        self.struct.add_sn_field('battery_serial_number', 6107)
        self.struct.add_version_field('bcu_version', 6175)
        self.struct.add_version_field('bmu_version', 6178)
        self.struct.add_version_field('safety_module_version', 6181)
        self.struct.add_version_field('high_voltage_module_version', 6184)

        super().__init__(address, 'EP600', sn)

    @property
    def polling_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(100, 62),
            ReadHoldingRegisters(2022, 2),
        ]

    @property
    def logging_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(100, 62),
            ReadHoldingRegisters(1100, 51),
            ReadHoldingRegisters(1200, 80),
            ReadHoldingRegisters(1300, 31),
            ReadHoldingRegisters(1400, 48),
            ReadHoldingRegisters(1500, 30),
            ReadHoldingRegisters(2000, 89),
            ReadHoldingRegisters(2200, 41),
            ReadHoldingRegisters(2300, 36),
            ReadHoldingRegisters(6000, 32),
            ReadHoldingRegisters(6100, 100),
            ReadHoldingRegisters(6300, 100),
        ]
