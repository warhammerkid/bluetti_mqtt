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
        self.struct.add_uint_field('pv_input_power_all', 144)  # Total PV in
        self.struct.add_uint_field('ac_output_power', 142)  # Total AC out
        self.struct.add_uint_field('grid_power', 146)  # Total Grid in - value only +/- unknown
        self.struct.add_uint_field('grid_power_high', 147)
        self.struct.add_uint_field('battery_range_start', 2022)
        self.struct.add_uint_field('battery_range_end', 2023)
        self.struct.add_uint_field('pv_input_power1', 1212)  # MPP 1 in - value * 0.1
        self.struct.add_uint_field('pv_input_voltage1', 1213)  # MPP 1 in  - value * 0.1
        self.struct.add_uint_field('pv_input_current1', 1214)  # MPP 1 in
        self.struct.add_uint_field('pv_input_power2', 1220)  # MPP 2 in  - value * 0.1
        self.struct.add_uint_field('pv_input_voltage2', 1221)  # MPP 2 in  - value * 0.1
        self.struct.add_uint_field('pv_input_current2', 1222)  # MPP 2 in
        self.struct.add_uint_field('grid_frequency', 1300)
        self.struct.add_uint_field('grid_power1', 1313)
        self.struct.add_uint_field('grid_voltage1', 1314)  # value * 0.1
        self.struct.add_uint_field('grid_current1', 1315)  # value * 0.1
        self.struct.add_uint_field('grid_power2', 1319)
        self.struct.add_uint_field('grid_voltage2', 1320)  # value * 0.1
        self.struct.add_uint_field('grid_current2', 1321)  # value * 0.1
        self.struct.add_uint_field('grid_power3', 1325)
        self.struct.add_uint_field('grid_voltage3', 1326)  # value * 0.1
        self.struct.add_uint_field('grid_current3', 1327)  # value * 0.1
        # AC Output details
        self.struct.add_uint_field('ac_output_power1', 1430)
        self.struct.add_uint_field('ac_output_voltage1', 1431)  # value * 0.1
        self.struct.add_uint_field('ac_output_current1', 1432)  # value * 0.1
        self.struct.add_uint_field('ac_output_power2', 1436)
        self.struct.add_uint_field('ac_output_voltage2', 1437)  # value * 0.1
        self.struct.add_uint_field('ac_output_current2', 1438)  # value * 0.1
        self.struct.add_uint_field('ac_output_power3', 1442)
        self.struct.add_uint_field('ac_output_voltage3', 1443)  # value * 0.1
        self.struct.add_uint_field('ac_output_current3', 1444)  # value * 0.1
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
            ReadHoldingRegisters(1212, 11),
            ReadHoldingRegisters(1300, 30),
            ReadHoldingRegisters(1429, 16),
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
