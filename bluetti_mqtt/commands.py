import struct
from .utils import modbus_crc


class DeviceCommand:
    def __init__(self, cmd: bytes):
        self.cmd = cmd

    """Returns the expected response size in bytes"""
    def response_size(self) -> int:
        pass

    """Provide an iter implemention so that bytes(cmd) works"""
    def __iter__(self):
        return iter(self.cmd)


class QueryRangeCommand(DeviceCommand):
    def __init__(self, page: int, offset: int, length: int):
        self.page = page
        self.offset = offset
        self.length = length

        cmd = bytearray(8)
        cmd[0] = 1  # Standard prefix
        cmd[1] = 3  # Range query command
        struct.pack_into('!BBH', cmd, 2, page, offset, length)
        struct.pack_into('<H', cmd, -2, modbus_crc(cmd[:-2]))
        super().__init__(cmd)

    def response_size(self):
        # 3 byte header
        # each returned field is actually 2 bytes
        # 2 byte crc
        return 2 * self.length + 5

    def __repr__(self):
        return (
            f'QueryRangeCommand({self.page=:#04x}, {self.offset=:#04x},'
            f' {self.length=:#04x})'
        )


class UpdateFieldCommand(DeviceCommand):
    def __init__(self, page: int, offset: int, value: int):
        self.page = page
        self.offset = offset
        self.value = value

        cmd = bytearray(8)
        cmd[0] = 1  # Standard prefix
        cmd[1] = 6  # Field update command
        struct.pack_into('!BBH', cmd, 2, page, offset, value)
        struct.pack_into('<H', cmd, -2, modbus_crc(cmd[:-2]))
        super().__init__(cmd)

    def response_size(self):
        return 8

    def __repr__(self):
        return (
            f'UpdateFieldCommand({self.page=:#04x}, {self.offset=:#04x},'
            f' {self.value=:#04x})'
        )


class UpdateRangeCommand(DeviceCommand):
    def __init__(self, page: int, offset: int, data: bytes):
        if len(data) % 2 != 0:
            raise ValueError('data size must be multiple of 2')

        self.page = page
        self.offset = offset
        self.data = data

        cmd = bytearray(len(data) + 9)
        cmd[0] = 1   # Standard prefix
        cmd[1] = 16  # Field update command
        half_len = len(data) >> 1
        struct.pack_into('!BBHB', cmd, 2, page, offset, half_len, len(data))
        cmd[7:-2] = data
        struct.pack_into('<H', cmd, -2, modbus_crc(cmd[:-2]))
        super().__init__(cmd)

    def response_size(self):
        return 8

    def __repr__(self):
        return (
            f'UpdateRangeCommand({self.page=:#04x}, {self.offset=:#04x},'
            f' {self.data=})'
        )
