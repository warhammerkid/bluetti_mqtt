class ParseError(Exception):
    pass


class ModbusError(Exception):
    """Used when the command returns a MODBUS exception"""
    pass


# Triggers a re-connect
class BadConnectionError(Exception):
    pass
