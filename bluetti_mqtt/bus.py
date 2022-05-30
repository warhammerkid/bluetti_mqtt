from bluetti_mqtt.device import BluettiDevice
from bluetti_mqtt.parser import DataParser

class ParserMessage:
    def __init__(self, device: BluettiDevice, parser: DataParser):
        self.device = device
        self.parser = parser
