from .utils import modbus_crc


class CommandResponse:
    def __init__(self, data: bytearray):
        self.data = data

    @property
    def body(self):
        if self.data[1] == 0x03:
            return bytes(self.data[3:-2])
        elif self.data[1] == 0x06:
            return bytes(self.data[4:6])
        else:
            raise Exception(f'Cannot decode body for response: {self.data}')

    """Append data as it comes in"""
    def extend(self, data: bytearray):
        self.data.extend(data)

    """If you send a bad request, you'll get an "invalid request" error"""
    def is_invalid_error(self):
        return len(self.data) == 5 and self.data[1] == 0x83

    """Validates that the reponse is complete and uncorrupted"""
    def is_valid(self):
        if len(self.data) < 3:
            return False

        crc = modbus_crc(self.data[0:-2])
        crc_bytes = crc.to_bytes(2, byteorder='little')
        return self.data[-2:] == crc_bytes

    def __len__(self):
        return len(self.data)
