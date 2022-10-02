from typing import List
from ..commands import QueryRangeCommand
from .bluetti_device import BluettiDevice
from .struct import DeviceStruct


class AC500(BluettiDevice):
    def __init__(self, address: str, sn: str):
        self.struct = DeviceStruct()

        # Page 0x00 - Core
        self.struct.add_uint_field('dc_input_power', 0x00, 0x24)
        self.struct.add_uint_field('ac_input_power', 0x00, 0x25)
        self.struct.add_uint_field('ac_output_power', 0x00, 0x26)
        self.struct.add_uint_field('dc_output_power', 0x00, 0x27)
        self.struct.add_decimal_field('power_generation', 0x00, 0x29, 1) # Total power generated since last reset in kwh
        self.struct.add_uint_field('total_battery_percent', 0x00, 0x2B)
        self.struct.add_bool_field('ac_output_on', 0x00, 0x30)
        self.struct.add_bool_field('dc_output_on', 0x00, 0x31)

        super().__init__(address, 'AC500', sn)

    @property
    def polling_commands(self) -> List[QueryRangeCommand]:
        return [QueryRangeCommand(0x00, 0x24, 0x0E)]

    @property
    def logging_commands(self) -> List[QueryRangeCommand]:
        return [
            QueryRangeCommand(0x00, 0x00, 0x46),
            QueryRangeCommand(0x00, 0x46, 0x15),
            QueryRangeCommand(0x00, 0x5B, 0x77),
            QueryRangeCommand(0x0B, 0xB8, 0x3E),
        ]
