from typing import List
from ..commands import ReadHoldingRegisters
from .bluetti_device import BluettiDevice
from .struct import DeviceStruct


class EP600(BluettiDevice):
    def __init__(self, address: str, sn: str):
        self.struct = DeviceStruct()
        # EP600 current values
        self.struct.add_uint_field('total_battery_percent', 102)
        self.struct.add_swap_string_field('device_type', 110, 6)
        self.struct.add_sn_field('serial_number', 116)
        self.struct.add_uint_field('dc_input_power', 144)  # Total PV in
        self.struct.add_uint_field('ac_output_power', 142)  # Total AC out
        self.struct.add_uint_field('grid_power', 146)  # Total Grid in
        self.struct.add_uint_field('battery_range_start', 2022)
        self.struct.add_uint_field('battery_range_end', 2023)
        # EP600 totals
        self.struct.add_decimal_field('total_ac_consumption', 152, 1)  # Load consumption
        self.struct.add_decimal_field('power_generation', 154, 1)  # Total power generated since last reset (kwh)
        self.struct.add_decimal_field('total_grid_consumption', 156, 1)  # Grid consumption stats
        self.struct.add_decimal_field('total_grid_feed', 158, 1)
        super().__init__(address, 'EP600', sn)

    @property
    def polling_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(100, 62),
            ReadHoldingRegisters(2022, 2),
            ReadHoldingRegisters(1212, 3),
            ReadHoldingRegisters(1300, 30),
        ]

    @property
    def logging_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(100, 62),
            ReadHoldingRegisters(1100, 51),
            ReadHoldingRegisters(1200, 90),
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
