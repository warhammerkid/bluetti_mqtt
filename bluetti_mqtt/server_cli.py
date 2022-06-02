import argparse
import asyncio
import logging
from typing import Set
import warnings
import sys
from bluetti_mqtt.bluetooth import BluetoothClientHandler, scan_devices
from bluetti_mqtt.bus import EventBus
from bluetti_mqtt.mqtt_client import MQTTClient


class CommandLineHandler:
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]

    def execute(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Scans for Bluetti devices and logs information')
        parser.add_argument(
            '--scan',
            action='store_true',
            help='Scans for devices and prints out addresses')
        parser.add_argument(
            '--broker',
            metavar='HOST',
            help='The MQTT broker host to connect to')
        parser.add_argument(
            '--interval',
            default=0,
            type=int,
            help='The polling interval - default is to poll as fast as possible')
        parser.add_argument(
            'addresses',
            metavar='ADDRESS',
            nargs='*',
            help='The device MAC(s) to connect to')
        args = parser.parse_args()
        if args.scan:
            asyncio.run(scan_devices())
        elif args.broker and len(args.addresses) > 0:
            addresses = set(args.addresses)
            asyncio.run(self.start(args.broker, args.interval, addresses))
        else:
            parser.print_help()

    async def start(self, broker: str, interval: int, addresses: Set[str]):
        loop = asyncio.get_running_loop()
        bus = EventBus()

        # Verify that we can see all the given addresses
        bluetooth_handler = BluetoothClientHandler(addresses, interval, bus)
        devices = await bluetooth_handler.check()
        if len(devices) == 0:
            sys.exit('Could not find the given devices to connect to')

        # Start bluetooth handler (manages connections)
        self.bluetooth_task = loop.create_task(bluetooth_handler.run())

        # Start MQTT client
        mqtt_client = MQTTClient(broker, devices, bus)
        self.mqtt_task = loop.create_task(mqtt_client.run())

        # Loop forever!
        await bus.run()


def main(argv=None):
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('bleak.backends.bluezdbus.scanner').setLevel(logging.INFO)
    logging.getLogger('bleak.backends.bluezdbus.client').setLevel(logging.INFO)
    warnings.simplefilter('always')
    cli = CommandLineHandler(argv)
    cli.execute()
