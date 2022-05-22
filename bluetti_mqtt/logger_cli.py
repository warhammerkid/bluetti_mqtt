import argparse
import asyncio
import base64
from io import TextIOWrapper
import itertools
import json
import re
import textwrap
import time
from bleak import BleakScanner
from .bluetooth_client import BluetoothClient
from .commands import DeviceCommand
from .exc import ParseError, BadConnectionError
from .parser import (LowerStatusPageParser, MidStatusPageParser,
                     ControlPageParser)


async def scan():
    print('Scanning....')
    devices = await BleakScanner.discover()
    if len(devices) == 0:
        print('0 devices found - something probably went wrong')
    else:
        prefix = re.compile(r'^(AC200M|AC300|EP500P|EP500)\d+$')
        bluetti_devices = [d for d in devices if prefix.match(d.name)]
        for d in bluetti_devices:
            print(f'Found {d.name}: address {d.address}')


def log_packet(output: TextIOWrapper, data: bytes, command: DeviceCommand):
    log_entry = {
        'type': 'client',
        'time': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime()),
        'data': base64.b64encode(data).decode('ascii'),
        'command': base64.b64encode(bytes(command)).decode('ascii'),
    }
    output.write(json.dumps(log_entry) + '\n')


async def log(address: str, path: str):
    print(f'Connecting to {address}')
    device = BluetoothClient(address)
    asyncio.get_running_loop().create_task(device.run())
    parsers = [LowerStatusPageParser, MidStatusPageParser, ControlPageParser]

    with open(path, 'a') as log_file:
        for parser in itertools.cycle(parsers):
            if not device.is_connected:
                print('Waiting for connection...')
                await asyncio.sleep(1)
                continue

            command = parser.build_query_command()
            result_future = await device.perform(command)
            try:
                result = await result_future
                log_packet(log_file, result, command)
            except ParseError:
                print('Got a parse exception...')
            except BadConnectionError as err:
                print(f'Needed to disconnect due to error: {err}')


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Scans for Bluetti devices and logs information',
        epilog=textwrap.dedent("""\
            To use, run the scanner first:
            %(prog)s --scan

            Once you have found your device you can run the logger:
            %(prog)s --log log-file.log 00:11:22:33:44:55
            """))
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Scans for devices and prints out addresses')
    parser.add_argument(
        '--log',
        metavar='PATH',
        help='Connect and log data for the device to the given file')
    parser.add_argument(
        'address',
        metavar='ADDRESS',
        nargs='?',
        help='The device MAC to connect to for logging')
    args = parser.parse_args()
    if args.scan:
        asyncio.run(scan())
    elif args.log:
        asyncio.run(log(args.address, args.log))
    else:
        parser.print_help()
