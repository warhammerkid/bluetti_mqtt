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
from bluetti_mqtt.bluetooth.client import BluetoothClient
from bluetti_mqtt.bluetooth.exc import InvalidRequestError, ParseError, BadConnectionError
from bluetti_mqtt.commands import QueryRangeCommand, UpdateFieldCommand, DeviceCommand
from bluetti_mqtt.parser import MidStatusPageParser


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


def log_invalid(output: TextIOWrapper, err: InvalidRequestError, command: DeviceCommand):
    log_entry = {
        'type': 'client',
        'time': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime()),
        'error': err.args[0],
        'command': base64.b64encode(bytes(command)).decode('ascii'),
    }
    output.write(json.dumps(log_entry) + '\n')


async def log_command(device: BluetoothClient, command: DeviceCommand, log_file: TextIOWrapper):
    result_future = await device.perform(command)
    try:
        result = await result_future
        log_packet(log_file, result, command)
    except InvalidRequestError as err:
        print('Got a "invalid request" error')
        log_invalid(log_file, err, command)
    except ParseError:
        print('Got a parse exception...')
    except BadConnectionError as err:
        print(f'Needed to disconnect due to error: {err}')


async def log(address: str, path: str):
    print(f'Connecting to {address}')
    device = BluetoothClient(address)
    asyncio.get_running_loop().create_task(device.run())

    with open(path, 'a') as log_file:
        # Wait for device connection
        while not device.is_connected:
            print('Waiting for connection...')
            await asyncio.sleep(1)
            continue

        # Get pack max
        result_future = await device.perform(MidStatusPageParser.build_query_command())
        result = await result_future
        pack_max = MidStatusPageParser(result[3:-2]).parse().pack_num_max
        print(f'Device has a maximum of {pack_max} battery packs')

        # Poll device
        while True:
            await log_command(device, QueryRangeCommand(0x00, 0x00, 0x46), log_file)
            await log_command(device, QueryRangeCommand(0x0B, 0xB9, 0x3D), log_file)

            for pack in range(1, pack_max + 1):
                await log_command(device, UpdateFieldCommand(0x0B, 0xBE, pack), log_file)
                await asyncio.sleep(10) # We need to wait after switching packs for the data to be available
                await log_command(device, QueryRangeCommand(0x00, 0x46, 0x42), log_file)
                await log_command(device, QueryRangeCommand(0x00, 0x88, 0x4a), log_file)


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
