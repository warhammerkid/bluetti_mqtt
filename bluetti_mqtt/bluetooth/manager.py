import asyncio
import logging
from typing import Dict, List
from bluetti_mqtt.core import BluettiDevice, DeviceCommand
from .client import BluetoothClient


class MultiDeviceManager:
    clients: Dict[BluettiDevice, BluetoothClient]

    def __init__(self, devices: List[BluettiDevice]):
        self.devices = devices
        self.clients = {}

    async def run(self):
        addresses = [d.address for d in self.devices]
        logging.info(f'Connecting to clients: {addresses}')
        self.clients = {d: BluetoothClient(d.address) for d in self.devices}
        await asyncio.gather(*[c.run() for c in self.clients.values()])

    def is_connected(self, device: BluettiDevice):
        if device in self.clients:
            return self.clients[device].is_connected
        else:
            return False

    async def perform(self, device: BluettiDevice, command: DeviceCommand):
        if device in self.clients:
            return await self.clients[device].perform(command)
        else:
            raise Exception('Unknown device')

    async def perform_nowait(self, device: BluettiDevice, command: DeviceCommand):
        if device in self.clients:
            await self.clients[device].perform_nowait(command)
        else:
            raise Exception('Unknown device')
