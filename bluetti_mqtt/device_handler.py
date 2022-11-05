import asyncio
from bleak import BleakError
import logging
import time
from typing import List, cast
from bluetti_mqtt.bluetooth import BadConnectionError, MultiDeviceManager, ParseError
from bluetti_mqtt.bluetooth.exc import InvalidRequestError
from bluetti_mqtt.bus import CommandMessage, EventBus, ParserMessage
from bluetti_mqtt.core import BluettiDevice, CommandResponse, QueryRangeCommand


class DeviceHandler:
    def __init__(self, devices: List[BluettiDevice], interval: int, bus: EventBus):
        self.manager = MultiDeviceManager(devices)
        self.interval = interval
        self.bus = bus

    async def run(self):
        loop = asyncio.get_running_loop()

        # Start manager
        manager_task = loop.create_task(self.manager.run())

        # Connect to event bus
        self.bus.add_command_listener(self.handle_command)

        # Poll the clients
        logging.info('Starting to poll clients...')
        polling_tasks = [self._poll(d) for d in self.manager.devices]
        pack_polling_tasks = [self._pack_poll(d) for d in self.manager.devices if len(d.pack_logging_commands) > 0]
        await asyncio.gather(*(polling_tasks + pack_polling_tasks + [manager_task]))

    async def handle_command(self, msg: CommandMessage):
        if self.manager.is_connected(msg.device):
            logging.debug(f'Performing command {msg.device}: {msg.command}')
            await self.manager.perform_nowait(msg.device, msg.command)

    async def _poll(self, device: BluettiDevice):
        while True:
            if not self.manager.is_connected(device):
                logging.debug(f'Waiting for connection to {device.address} to start polling...')
                await asyncio.sleep(1)
                continue

            # Send all polling commands
            start_time = time.monotonic()
            for command in device.polling_commands:
                await self._poll_with_command(device, command)
            elapsed = time.monotonic() - start_time

            # Limit polling rate if interval provided
            if self.interval > 0 and self.interval > elapsed:
                await asyncio.sleep(self.interval - elapsed)

    async def _pack_poll(self, device: BluettiDevice):
        while True:
            if not self.manager.is_connected(device):
                logging.debug(f'Waiting for connection to {device.address} to start pack polling...')
                await asyncio.sleep(1)
                continue

            start_time = time.monotonic()
            for pack in range(1, device.pack_num_max + 1):
                # Send pack set command if the device supports more than 1 pack
                if device.pack_num_max > 1:
                    command = device.build_setter_command('pack_num', pack)
                    await self.manager.perform_nowait(device, command)
                    await asyncio.sleep(10)  # We need to wait after switching packs for the data to be available

                # Poll
                for command in device.pack_logging_commands:
                    await self._poll_with_command(device, command)
            elapsed = time.monotonic() - start_time

            # Limit polling rate if interval provided
            if self.interval > 0 and self.interval > elapsed:
                await asyncio.sleep(self.interval - elapsed)

    async def _poll_with_command(self, device: BluettiDevice, command: QueryRangeCommand):
        response_future = await self.manager.perform(device, command)
        try:
            response = cast(CommandResponse, await response_future)
            parsed = device.parse(command.page, command.offset, response.body)
            await self.bus.put(ParserMessage(device, parsed))
        except ParseError:
            logging.debug('Got a parse exception...')
        except InvalidRequestError as err:
            logging.debug(f'Got an invalid request error for {command}: {err}')
        except (BadConnectionError, BleakError) as err:
            logging.debug(f'Needed to disconnect due to error: {err}')
