import logging
import re
from typing import Set
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bluetti_mqtt.core import BluettiDevice, AC200M, AC300, AC500, EP500, EP500P, EB3A
from .client import BluetoothClient
from .exc import BadConnectionError, InvalidRequestError, ParseError
from .manager import MultiDeviceManager


DEVICE_NAME_RE = re.compile(r'^(AC200M|AC300|AC500|EP500P|EP500|EB3A)(\d+)$')


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
        if match[1] == 'AC200M':
            return AC200M(device.address, match[2])
        if match[1] == 'AC300':
            return AC300(device.address, match[2])
        if match[1] == 'AC500':
            return AC500(device.address, match[2])
        if match[1] == 'EP500':
            return EP500(device.address, match[2])
        if match[1] == 'EP500P':
            return EP500P(device.address, match[2])
        if match[1] == 'EB3A':
            return EB3A(device.address, match[2])

    return [build_device(d) for d in filtered]
