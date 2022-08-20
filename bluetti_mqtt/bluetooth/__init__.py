import asyncio
import logging
import re
import time
from typing import Dict, List, Set
from bleak import BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from bluetti_mqtt.bus import CommandMessage, EventBus, ParserMessage
from bluetti_mqtt.commands import QueryRangeCommand
from bluetti_mqtt.devices import BluettiDevice, AC200M, AC300, EP500, EP500P, EB3A
from bluetti_mqtt.bluetooth.client import BluetoothClient
from bluetti_mqtt.bluetooth.exc import BadConnectionError, ParseError


DEVICE_NAME_RE = re.compile(r'^(AC200M|AC300|EP500P|EP500|EB3A)(\d+)$')


class BluetoothClientHandler:
    clients: Dict[BluettiDevice, BluetoothClient]

    def __init__(self, devices: List[BluettiDevice], interval: int, bus: EventBus):
        self.devices = devices
        self.interval = interval
        self.bus = bus
        self.clients = {}

    async def run(self):
        loop = asyncio.get_running_loop()

        # Start clients
        addresses = [d.address for d in self.devices]
        logging.info(f'Connecting to clients: {addresses}')
        self.clients = {d: BluetoothClient(d.address) for d in self.devices}
        self.client_tasks = [loop.create_task(c.run()) for c in self.clients.values()]

        # Connect to event bus
        self.bus.add_command_listener(self.handle_command)

        # Poll the clients
        logging.info('Starting to poll clients...')
        await asyncio.gather(*[self._poll(d, c) for d, c in self.clients.items()])

    async def handle_command(self, msg: CommandMessage):
        if msg.device in self.clients:
            client = self.clients[msg.device]
            logging.debug(f'Performing command {msg.device}: {msg.command}')
            await client.perform_nowait(msg.command)

    async def _poll(self, device: BluettiDevice, client: BluetoothClient):
        while True:
            if not client.is_connected:
                logging.debug(f'Waiting for connection to {device.address} to start polling...')
                await asyncio.sleep(1)
                continue

            start_time = time.monotonic()
            await self._poll_with_command(device, client, QueryRangeCommand(0x00, 0x0A, 0x35))
            await self._poll_with_command(device, client, QueryRangeCommand(0x00, 0x46, 0x42))
            await self._poll_with_command(device, client, QueryRangeCommand(0x0B, 0xB9, 0x3D))
            elapsed = time.monotonic() - start_time

            # Limit polling rate if interval provided
            if self.interval > 0 and self.interval > elapsed:
                await asyncio.sleep(self.interval - elapsed)

    async def _poll_with_command(self, device: BluettiDevice, client: BluetoothClient, command: QueryRangeCommand):
        result_future = await client.perform(command)
        try:
            result = await result_future
            parsed = device.parse(command.page, command.offset, result[3:-2])
            await self.bus.put(ParserMessage(device, parsed))
        except ParseError:
            logging.debug('Got a parse exception...')
        except (BadConnectionError, BleakError) as err:
            logging.debug(f'Needed to disconnect due to error: {err}')


async def scan_devices():
    print('Scanning....')
    devices = await BleakScanner.discover()
    if len(devices) == 0:
        print('0 devices found - something probably went wrong')
    else:
        bluetti_devices = [d for d in devices if d.name and DEVICE_NAME_RE.match(d.name)]
        for d in bluetti_devices:
            print(f'Found {d.name}: address {d.address}')


async def check_addresses(addresses: Set[str]):
    logging.debug(f'Checking we can connect: {addresses}')
    devices = await BleakScanner.discover()
    filtered = [d for d in devices if d.address in addresses]
    logging.debug(f'Found devices: {filtered}')

    if len(filtered) != len(addresses):
        return []

    def build_device(device: BLEDevice) -> BluettiDevice:
        match = DEVICE_NAME_RE.match(device.name)
        if match[1] == 'AC200M': return AC200M(device.address, match[2])
        if match[1] == 'AC300': return AC300(device.address, match[2])
        if match[1] == 'EP500': return EP500(device.address, match[2])
        if match[1] == 'EP500P': return EP500P(device.address, match[2])
        if match[1] == 'EB3A': return EB3A(device.address, match[2])
    return [build_device(d) for d in filtered]
