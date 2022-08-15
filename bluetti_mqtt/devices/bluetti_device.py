from typing import Any
from bluetti_mqtt.commands import UpdateFieldCommand
from .struct import BoolField, DeviceStruct, EnumField


class BluettiDevice:
    struct: DeviceStruct

    def __init__(self, address: str, type: str, sn: str):
        self.address = address
        self.type = type
        self.sn = sn

    def parse(self, page: int, offset: int, data: bytes) -> dict:
        return self.struct.parse(page, offset, data)

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
