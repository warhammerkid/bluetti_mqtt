import argparse
import asyncio
import base64
from bleak import BleakError, BleakScanner
from io import TextIOWrapper
import json
import sys
import textwrap
import time
from typing import cast
from bluetti_mqtt.bluetooth import BluetoothClient, ModbusError, ParseError, BadConnectionError
from bluetti_mqtt.core import ReadHoldingRegisters


def log_packet(output: TextIOWrapper, data: bytes, command: ReadHoldingRegisters):
    log_entry = {
        'type': 'client',
        'time': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime()),
        'data': base64.b64encode(data).decode('ascii'),
        'command': base64.b64encode(bytes(command)).decode('ascii'),
    }
    output.write(json.dumps(log_entry) + '\n')


def log_invalid(output: TextIOWrapper, err: Exception, command: ReadHoldingRegisters):
    log_entry = {
        'type': 'client',
        'time': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime()),
        'error': err.args[0],
        'command': base64.b64encode(bytes(command)).decode('ascii'),
    }
    output.write(json.dumps(log_entry) + '\n')


async def log_command(client: BluetoothClient, command: ReadHoldingRegisters, log_file: TextIOWrapper):
    response_future = await client.perform(command)
    try:
        response = cast(bytes, await response_future)
        print(f'Device data readable at {command.starting_address}')
        log_packet(log_file, response, command)
    except (BadConnectionError, BleakError, ParseError) as err:
        print(f'Got an error running command {command}: {err}')
        log_invalid(log_file, err, command)
    except ModbusError as err:
        # This is expected if we attempt to access an invalid address
        log_invalid(log_file, err, command)


async def scan_devices():
    print('Scanning....')
    devices = await BleakScanner.discover()
    if len(devices) == 0:
        print('0 devices found - something probably went wrong')
    else:
        for d in devices:
            print(f'Found {d.name}: address {d.address}')


async def discover(address: str, path: str):
    print(f'Connecting to {address}')
    client = BluetoothClient(address)
    asyncio.get_running_loop().create_task(client.run())

    with open(path, 'a') as log_file:
        # Wait for device connection
        while not client.is_ready:
            print('Waiting for connection...')
            await asyncio.sleep(1)
            continue

        # Work our way through all the valid addresses
        print('Discovering device data - THIS MAY TAKE SEVERAL HOURS')
        print('0% complete with discovery')
        max_address = 12500
        last_percent = 0
        for address in range(0, max_address + 1):
            # Log progress
            percent = int(address / max_address * 100)
            if percent != last_percent:
                print(f'{percent}% complete with discovery')
                last_percent = percent

            # Query address
            command = ReadHoldingRegisters(address, 1)
            await log_command(client, command, log_file)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Attempts to discover supported MODBUS ranges for undocumented Bluetti devices',
        epilog=textwrap.dedent("""\
            To use, run the scanner first:
            %(prog)s --scan

            Once you have found your device you can run the discovery tool:
            %(prog)s --log log-file.log 00:11:22:33:44:55

            Before starting this process, it is advised to connect AC and DC
            inputs (if supported) as well as to attach DC and AC loads. This
            will help with interpreting the data. Once the discovery process is
            complete, which may take a while, the data can be used to add
            support.
            """))
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Scans for devices and prints out addresses')
    parser.add_argument(
        '--log',
        metavar='PATH',
        help='Connect and write discovered data for the device to the file')
    parser.add_argument(
        'address',
        metavar='ADDRESS',
        nargs='?',
        help='The device MAC to connect to for discovery')
    args = parser.parse_args()
    if args.scan:
        asyncio.run(scan_devices())
    elif args.log:
        asyncio.run(discover(args.address, args.log))
    else:
        parser.print_help()


if __name__ == "__main__":
    main(sys.argv)
