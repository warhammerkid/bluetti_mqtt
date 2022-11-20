from typing import Any, List
from ..commands import QueryRangeCommand, UpdateFieldCommand
from .struct import BoolField, DeviceStruct, EnumField


class BluettiDevice:
    struct: DeviceStruct

    def __init__(self, address: str, type: str, sn: str):
        self.address = address
        self.type = type
        self.sn = sn

    def parse(self, page: int, offset: int, data: bytes) -> dict:
        return self.struct.parse(page, offset, data)

    @property
    def pack_num_max(self):
        """
        A given device has a maximum number of battery packs, including the
        internal battery if it has one. We can provide this information statically
        so it's not necessary to poll the device.
        """
        return 1

    @property
    def polling_commands(self) -> List[QueryRangeCommand]:
        """A given device has an optimal set of commands for polling"""
        raise NotImplementedError

    @property
    def pack_polling_commands(self) -> List[QueryRangeCommand]:
        """A given device may have a set of commands for polling pack data"""
        return []

    @property
    def logging_commands(self) -> List[QueryRangeCommand]:
        """A given device has an optimal set of commands for debug logging"""
        raise NotImplementedError

    @property
    def pack_logging_commands(self) -> List[QueryRangeCommand]:
        """A given device may have a set of commands for logging pack data"""
        return []

    def has_field(self, field: str):
        return any(f.name == field for f in self.struct.fields)

    def has_field_setter(self, field: str):
        return any(f.page == 0x0B and f.name == field for f in self.struct.fields)

    def build_setter_command(self, field: str, value: Any):
        device_field = next(f for f in self.struct.fields if f.page == 0x0B and f.name == field)

        # Convert value to an integer
        if isinstance(device_field, EnumField):
            value = device_field.enum[value].value
        elif isinstance(device_field, BoolField):
            value = 1 if value else 0

        return UpdateFieldCommand(device_field.page, device_field.offset, value)
