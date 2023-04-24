import argparse
import asyncio
import logging
import os
import signal
from typing import List
import warnings
import sys
from bluetti_mqtt.bluetooth import scan_devices
from bluetti_mqtt.bus import EventBus
from bluetti_mqtt.device_handler import DeviceHandler
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
            '--ha-config',
            default='normal',
            choices=['normal', 'none', 'advanced'],
            help='What fields to configure in Home Assistant - defaults to most fields ("normal")')
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
            self.start(args)
        else:
            parser.print_help()

    def start(self, args: argparse.Namespace):
        loop = asyncio.get_event_loop()

        # Register signal handlers for safe shutdown
        if sys.platform != 'win32':
            signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
            for s in signals:
                loop.add_signal_handler(s, lambda: asyncio.create_task(shutdown(loop)))

        # Register a global exception handler so we don't hang
        loop.set_exception_handler(handle_global_exception)

        try:
            loop.create_task(self.run(args))
            loop.run_forever()
        finally:
            loop.close()
            logging.debug("Shut down completed")

    async def run(self, args: argparse.Namespace):
        loop = asyncio.get_running_loop()
        bus = EventBus()

        # Set up strong reference for tasks
        self.background_tasks = set()

        # Start event bus
        bus_task = loop.create_task(bus.run())
        self.background_tasks.add(bus_task)
        bus_task.add_done_callback(self.background_tasks.discard)

        # Start MQTT client
        mqtt_client = MQTTClient(
            bus=bus,
            hostname=args.hostname,
            home_assistant_mode=args.ha_config,
            port=args.port,
            username=args.username,
            password=args.password,
        )
        mqtt_task = loop.create_task(mqtt_client.run())
        self.background_tasks.add(mqtt_task)
        mqtt_task.add_done_callback(self.background_tasks.discard)

        # Start bluetooth handler (manages connections)
        addresses: List[str] = list(set(args.addresses))
        handler = DeviceHandler(addresses, args.interval, bus)
        bluetooth_task = loop.create_task(handler.run())
        self.background_tasks.add(bluetooth_task)
        bluetooth_task.add_done_callback(self.background_tasks.discard)


def handle_global_exception(loop, context):
    if 'exception' in context:
        logging.error('Crashing with uncaught exception:', exc_info=context['exception'])
    else:
        logging.error(f'Crashing with uncaught exception: {context["message"]}')
    asyncio.create_task(shutdown(loop))


async def shutdown(loop: asyncio.AbstractEventLoop):
    logging.info('Shutting down...')
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


def main(argv=None):
    debug = os.environ.get('DEBUG')
    level = logging.INFO
    if debug:
        level = logging.DEBUG
        warnings.simplefilter('always')

    logging.basicConfig(
        datefmt='%Y-%m-%d %H:%M:%S',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=level
    )

    cli = CommandLineHandler(argv)
    cli.execute()


if __name__ == "__main__":
    main(sys.argv)
