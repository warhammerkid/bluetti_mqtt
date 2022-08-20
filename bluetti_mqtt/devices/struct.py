from decimal import Decimal
from enum import Enum
import struct
from typing import Any, List, Type


class DeviceField:
    def __init__(self, name: str, page: int, offset: int, size: int):
        self.name = name
        self.page = page
        self.offset = offset
        self.size = size

    def parse(self, data: bytes) -> Any:
        raise NotImplementedError


class UintField(DeviceField):
    def __init__(self, name: str, page: int, offset: int):
        super().__init__(name, page, offset, 1)

    def parse(self, data: bytes) -> int:
        return struct.unpack('!H', data)[0]


class BoolField(DeviceField):
    def __init__(self, name: str, page: int, offset: int):
        super().__init__(name, page, offset, 1)

    def parse(self, data: bytes) -> bool:
        return struct.unpack('!H', data)[0] == 1


class EnumField(DeviceField):
    def __init__(self, name: str, page: int, offset: int, enum: Type[Enum]):
        self.enum = enum
        super().__init__(name, page, offset, 1)

    def parse(self, data: bytes) -> Any:
        val = struct.unpack('!H', data)[0]
        return self.enum(val)


class DecimalField(DeviceField):
    def __init__(self, name: str, page: int, offset: int, scale: int):
        self.scale = scale
        super().__init__(name, page, offset, 1)

    def parse(self, data: bytes) -> Decimal:
        val = Decimal(struct.unpack('!H', data)[0])
        return val / 10 ** self.scale


class DecimalArrayField(DeviceField):
    def __init__(self, name: str, page: int, offset: int, size: int, scale: int):
        self.scale = scale
        super().__init__(name, page, offset, size)

    def parse(self, data: bytes) -> Decimal:
        values = list(struct.unpack(f'!{self.size}H', data))
        return [Decimal(v) / 10 ** self.scale for v in values]


"""Fixed-width null-terminated string field"""
class StringField(DeviceField):
    def parse(self, data: bytes) -> str:
        return data.rstrip(b'\0').decode('ascii')


class VersionField(DeviceField):
    def __init__(self, name: str, page: int, offset: int):
        super().__init__(name, page, offset, 2)

    def parse(self, data: bytes) -> int:
        values = struct.unpack('!2H', data)
        return Decimal(values[0] + (values[1] << 16)) / 100


class SerialNumberField(DeviceField):
    def __init__(self, name: str, page: int, offset: int):
        super().__init__(name, page, offset, 4)

    def parse(self, data: bytes) -> int:
        values = struct.unpack('!4H', data)
        return values[0] + (values[1] << 16) + (values[2] << 32) + (values[3] << 48)


class DeviceStruct:
    fields: List[DeviceField]

    def __init__(self):
        self.fields = []

    def add_uint_field(self, name: str, page: int, offset: int):
        self.fields.append(UintField(name, page, offset))

    def add_bool_field(self, name: str, page: int, offset: int):
        self.fields.append(BoolField(name, page, offset))

    def add_enum_field(self, name: str, page: int, offset: int, enum: Type[Enum]):
        self.fields.append(EnumField(name, page, offset, enum))

    def add_decimal_field(self, name: str, page: int, offset: int, scale: int):
        self.fields.append(DecimalField(name, page, offset, scale))

    def add_decimal_array_field(self, name: str, page: int, offset: int, size: int, scale: int):
        self.fields.append(DecimalArrayField(name, page, offset, size, scale))

    def add_string_field(self, name: str, page: int, offset: int, size: int):
        self.fields.append(StringField(name, page, offset, size))

    def add_version_field(self, name: str, page: int, offset: int):
        self.fields.append(VersionField(name, page, offset))

    def add_sn_field(self, name: str, page: int, offset: int):
        self.fields.append(SerialNumberField(name, page, offset))

    def parse(self, page: int, offset: int, data: bytes) -> dict:
        # Offsets and size are counted in 2 byte chunks, so for the range we
        # need to divide the byte size by 2
        data_size = int(len(data) / 2)

        # Filter out fields not in range
        r = range(offset, offset + data_size)
        fields = [f for f in self.fields
                  if f.page == page and f.offset in r and f.offset + f.size - 1 in r]
        
        # Parse fields
        parsed = {}
        for f in fields:
            data_start = 2 * (f.offset - offset)
            field_data = data[data_start:data_start + 2 * f.size]
            parsed[f.name] = f.parse(field_data)

        return parsed
