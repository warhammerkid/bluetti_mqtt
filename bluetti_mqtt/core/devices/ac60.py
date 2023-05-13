from typing import List
from ..commands import ReadHoldingRegisters
from .bluetti_device import BluettiDevice
from .struct import DeviceStruct


class AC60(BluettiDevice):
    def __init__(self, address: str, sn: str):
        self.struct = DeviceStruct()

        self.struct.add_uint_field('total_battery_percent', 102)
        self.struct.add_swap_string_field('device_type', 110, 6)
        self.struct.add_sn_field('serial_number', 116)
        self.struct.add_decimal_field('power_generation', 154, 1)  # Total power generated since last reset (kwh)
        self.struct.add_swap_string_field('device_type', 1101, 6)
        self.struct.add_sn_field('serial_number', 1107)
        self.struct.add_decimal_field('power_generation', 1202, 1)  # Total power generated since last reset (kwh)
        self.struct.add_swap_string_field('battery_type', 6101, 6)
        self.struct.add_sn_field('battery_serial_number', 6107)
        self.struct.add_version_field('bcu_version', 6175)

        super().__init__(address, 'AC60', sn)

    @property
    def polling_commands(self) -> List[ReadHoldingRegisters]:
        return [
            ReadHoldingRegisters(100, 62),
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
            ReadHoldingRegisters(2000, 67),
            ReadHoldingRegisters(2200, 29),
            ReadHoldingRegisters(6000, 31),
            ReadHoldingRegisters(6100, 100),
            ReadHoldingRegisters(6300, 52),
        ]
