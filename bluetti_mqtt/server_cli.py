import argparse
import asyncio
import logging
import os
import signal
from typing import Set
import warnings
import sys
from bluetti_mqtt.bluetooth import BluetoothClientHandler, check_addresses, scan_devices
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
            dest='hostname',
            help='The MQTT broker host to connect to')
        parser.add_argument(
            '--port',
            default=1883,
            type=int,
            help='The MQTT broker port to connect to - defaults to %(default)s')
        parser.add_argument(
            '--username',
            type=str,
            help='The optional MQTT broker username')
        parser.add_argument(
            '--password',
            type=str,
            help='The optional MQTT broker password')
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

        # The default event loop on windows doesn't support add_reader, which
        # is required by asyncio-mqtt
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        args = parser.parse_args()
        if args.scan:
            asyncio.run(scan_devices())
        elif args.hostname and len(args.addresses) > 0:
            asyncio.run(self.start(args))
        else:
            parser.print_help()

    async def start(self, args: argparse.Namespace):
        loop = asyncio.get_running_loop()
        bus = EventBus()

        # Verify that we can see all the given addresses
        addresses = set(args.addresses)
        devices = await check_addresses(addresses)
        if len(devices) == 0:
            sys.exit('Could not find the given devices to connect to')

        # Start bluetooth handler (manages connections)
        bluetooth_handler = BluetoothClientHandler(devices, args.interval, bus)
        self.bluetooth_task = loop.create_task(bluetooth_handler.run())

        # Start MQTT client
        mqtt_client = MQTTClient(
            devices=devices,
            bus=bus,
            hostname=args.hostname,
            port=args.port,
            username=args.username,
            password=args.password,
        )
        self.mqtt_task = loop.create_task(mqtt_client.run())

        # Register signal handlers for safe shutdown
        if sys.platform != 'win32':
            signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
            for s in signals:
                loop.add_signal_handler(s, lambda: asyncio.create_task(self.shutdown()))

        # Run until cancelled
        try:
            await bus.run()
        except asyncio.CancelledError:
            logging.debug('Event bus run cancelled')

    async def shutdown(self):
        logging.info('Shutting down...')
        loop = asyncio.get_running_loop()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()


def main(argv=None):
    debug = os.environ.get('DEBUG')
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        warnings.simplefilter('always')
    else:
        logging.basicConfig(level=logging.INFO)

    cli = CommandLineHandler(argv)
    cli.execute()

if __name__ == "__main__":
    main(sys.argv)