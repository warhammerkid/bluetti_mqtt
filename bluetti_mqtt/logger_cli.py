import argparse
import asyncio
import base64
from bleak import BleakError
from io import TextIOWrapper
import json
import sys
import textwrap
import time
from typing import cast
from bluetti_mqtt.bluetooth import (
    check_addresses, scan_devices, BluetoothClient, InvalidRequestError,
    ParseError, BadConnectionError
)
from bluetti_mqtt.core import (
    BluettiDevice, CommandResponse, QueryRangeCommand, DeviceCommand
)


def log_packet(output: TextIOWrapper, data: bytes, command: DeviceCommand):
    log_entry = {
        'type': 'client',
        'time': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime()),
        'data': base64.b64encode(data).decode('ascii'),
        'command': base64.b64encode(bytes(command)).decode('ascii'),
    }
    output.write(json.dumps(log_entry) + '\n')


def log_invalid(output: TextIOWrapper, err: Exception, command: DeviceCommand):
    log_entry = {
        'type': 'client',
        'time': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime()),
        'error': err.args[0],
        'command': base64.b64encode(bytes(command)).decode('ascii'),
    }
    output.write(json.dumps(log_entry) + '\n')


async def log_command(client: BluetoothClient, device: BluettiDevice, command: DeviceCommand, log_file: TextIOWrapper):
    response_future = await client.perform(command)
    try:
        response = cast(CommandResponse, await response_future)
        if isinstance(command, QueryRangeCommand):
            parsed = device.parse(command.page, command.offset, response.body)
            print(parsed)
        log_packet(log_file, response.data, command)
    except (BadConnectionError, BleakError, InvalidRequestError, ParseError) as err:
        print(f'Got an error running command {command}: {err}')
        log_invalid(log_file, err, command)


async def log(address: str, path: str):
    devices = await check_addresses({address})
    if len(devices) == 0:
        sys.exit('Could not find the given device to connect to')
    device = devices[0]

    print(f'Connecting to {device.address}')
    client = BluetoothClient(device.address)
    asyncio.get_running_loop().create_task(client.run())

    with open(path, 'a') as log_file:
        # Wait for device connection
        while not client.is_connected:
            print('Waiting for connection...')
            await asyncio.sleep(1)
            continue

        # Poll device
        while True:
            for command in device.logging_commands:
                await log_command(client, device, command, log_file)

            # Skip pack polling if not available
            if len(device.pack_logging_commands) == 0:
                continue

            for pack in range(1, device.pack_num_max + 1):
                # Send pack set command if the device supports more than 1 pack
                if device.pack_num_max > 1:
                    command = device.build_setter_command('pack_num', pack)
                    await log_command(client, device, command, log_file)
                    await asyncio.sleep(10) # We need to wait after switching packs for the data to be available

                for command in device.pack_logging_commands:
                    await log_command(client, device, command, log_file)


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
        asyncio.run(scan_devices())
    elif args.log:
        asyncio.run(log(args.address, args.log))
    else:
        parser.print_help()

if __name__ == "__main__":
    main(sys.argv)
