import argparse
import asyncio
import base64
import itertools
import json
import re
import textwrap
import time
from bleak import BleakScanner
from .bluetooth_client import BluetoothClient
from .commands import QueryRangeCommand
from .exc import ParseError, BadConnectionError


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


async def log(address):
    print(f'Connecting to {address}...')
    device = BluetoothClient(address)
    asyncio.get_running_loop().create_task(device.run())
    commands = [
        QueryRangeCommand(0x00, 0x00, 0x46),
        QueryRangeCommand(0x00, 0x46, 0x42),
        QueryRangeCommand(0x00, 0x88, 0x4a),
        QueryRangeCommand(0x0B, 0xB9, 0x3D)
    ]
    for command in itertools.cycle(commands):
        if not device.is_connected:
            await asyncio.sleep(1)
            continue

        result_future = await device.perform(command)
        try:
            result = await result_future
            time_str = time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime())
            log_entry = {
                'type': 'client',
                'time': time_str,
                'data': base64.b64encode(result).decode('ascii'),
                'command': base64.b64encode(bytes(command)).decode('ascii'),
            }
            print(json.dumps(log_entry))
        except (ParseError, BadConnectionError):
            continue


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Scans for Bluetti devices and logs information',
        epilog=textwrap.dedent("""\
            To use, run the scanner first:
            %(prog)s --scan

            Once you have found your device you can run the logger:
            %(prog)s --log 00:11:22:33:44:55
            """))
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Scans for devices and prints out addresses')
    parser.add_argument(
        '--log',
        metavar='ADDRESS',
        help='Connect and log data for the given device to STDOUT')
    args = parser.parse_args()
    if args.scan:
        asyncio.run(scan())
    elif args.log:
        asyncio.run(log(args.log))
    else:
        parser.print_help()
