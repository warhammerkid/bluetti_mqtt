import struct
from .utils import modbus_crc


class DeviceCommand:
    def __init__(self, function_code: int, data: bytes):
        self.function_code = function_code

        self.cmd = bytearray(len(data) + 4)
        self.cmd[0] = 1  # MODBUS address
        self.cmd[1] = function_code
        self.cmd[2:-2] = data
        struct.pack_into('<H', self.cmd, -2, modbus_crc(self.cmd[:-2]))

    def response_size(self) -> int:
        """Returns the expected response size in bytes"""
        pass

    def __iter__(self):
        """Provide an iter implemention so that bytes(cmd) works"""
        return iter(self.cmd)

    def is_exception_response(self, response: bytes):
        """Checks the response code to see if it's a MODBUS exception"""
        if len(response) < 2:
            return False
        else:
            return response[1] == self.function_code + 0x80

    def is_valid_response(self, response: bytes):
        """Validates that the reponse is complete and uncorrupted"""
        if len(response) < 3:
            return False

        crc = modbus_crc(response[0:-2])
        crc_bytes = crc.to_bytes(2, byteorder='little')
        return response[-2:] == crc_bytes

    def parse_response(self, response: bytes):
        """Returns the raw body of the response"""
        return response


class ReadHoldingRegisters(DeviceCommand):
    def __init__(self, starting_address: int, quantity: int):
        self.starting_address = starting_address
        self.quantity = quantity

        super().__init__(3, struct.pack('!HH', starting_address, quantity))

    def response_size(self):
        # 3 byte header
        # each returned field is actually 2 bytes (16-bit word)
        # 2 byte crc
        return 2 * self.quantity + 5

    def parse_response(self, response: bytes):
        return bytes(response[3:-2])

    def __repr__(self):
        return (
            f'ReadHoldingRegisters(starting_address={self.starting_address}, quantity={self.quantity})'
        )


class WriteSingleRegister(DeviceCommand):
    def __init__(self, address: int, value: int):
        self.address = address
        self.value = value

        super().__init__(6, struct.pack('!HH', address, value))

    def response_size(self):
        return 8

    def parse_response(self, response: bytes):
        return bytes(response[4:6])

    def __repr__(self):
        return (
            f'WriteSingleRegister(address={self.address}, value={self.value:#04x})'
        )


class WriteMultipleRegisters(DeviceCommand):
    def __init__(self, starting_address: int, data: bytes):
        if len(data) % 2 != 0:
            raise ValueError('data size must be multiple of 2')

        self.starting_address = starting_address
        self.data = data

        body = bytearray(len(data) + 5)
        half_len = len(data) >> 1
        struct.pack_into('!HHB', body, 0, starting_address, half_len, len(data))
        body[5:] = data
        super().__init__(16, body)

    def response_size(self):
        return 8

    def __repr__(self):
        return (
            f'WriteMultipleRegisters(starting_address={self.starting_address}, data={self.data})'
        )
