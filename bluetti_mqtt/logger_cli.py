import argparse
import asyncio
import base64
from io import TextIOWrapper
import json
import sys
import textwrap
import time
from bluetti_mqtt.bluetooth import check_addresses, scan_devices
from bluetti_mqtt.bluetooth.client import BluetoothClient
from bluetti_mqtt.bluetooth.exc import InvalidRequestError, ParseError, BadConnectionError
from bluetti_mqtt.commands import QueryRangeCommand, UpdateFieldCommand, DeviceCommand
from bluetti_mqtt.devices import BluettiDevice


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
    result_future = await client.perform(command)
    try:
        result = await result_future
        if isinstance(command, QueryRangeCommand):
            parsed = device.parse(command.page, command.offset, result[3:-2])
            print(parsed)
        log_packet(log_file, result, command)
    except (InvalidRequestError, ParseError, BadConnectionError) as err:
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

        # Get pack max
        result_future = await client.perform(QueryRangeCommand(0x00, 0x5B, 1))
        result = await result_future
        pack_max = device.parse(0x00, 0x5B, result[3:-2])['pack_num_max']
        print(f'Device has a maximum of {pack_max} battery packs')

        # Poll device
        while True:
            if device.type == 'EB3A':
                await log_command(client, device, QueryRangeCommand(0x00, 0x0A, 0x35), log_file)
            else:
                await log_command(client, device, QueryRangeCommand(0x00, 0x00, 0x46), log_file)

            await log_command(client, device, QueryRangeCommand(0x0B, 0xB9, 0x3D), log_file)

            for pack in range(1, pack_max + 1):
                if pack_max > 1:
                    await log_command(client, device, UpdateFieldCommand(0x0B, 0xBE, pack), log_file)
                    await asyncio.sleep(10) # We need to wait after switching packs for the data to be available
                await log_command(client, device, QueryRangeCommand(0x00, 0x46, 0x42), log_file)
                await log_command(client, device, QueryRangeCommand(0x00, 0x88, 0x4a), log_file)


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
