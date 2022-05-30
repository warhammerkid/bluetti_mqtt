import asyncio
import logging
import re
from typing import List
from asyncio_mqtt import Client
from paho.mqtt.client import MQTTMessage
from bluetti_mqtt.bus import CommandMessage, EventBus, ParserMessage
from bluetti_mqtt.commands import DeviceCommand, UpdateFieldCommand
from bluetti_mqtt.device import BluettiDevice
from bluetti_mqtt.parser import (
    AutoSleepMode,
    ControlPageParser,
    LowerStatusPageParser,
    MidStatusPageParser,
    UpsMode,
)


COMMAND_TOPIC_RE = re.compile(r'^bluetti/command/(\w+)-(\d+)/([a-z_]+)$')


class MQTTClient:
    message_queue: asyncio.Queue

    def __init__(self, host: str, devices: List[BluettiDevice], bus: EventBus):
        self.host = host
        self.devices = devices
        self.bus = bus

    async def run(self):
        async with Client(self.host) as client:
            # Connect to event bus
            self.message_queue = asyncio.Queue()
            self.bus.add_parser_listener(self.handle_message)

            # Handle pub/sub
            await asyncio.gather(
                self._handle_commands(client),
                self._handle_messages(client)
            )

    async def handle_message(self, msg: ParserMessage):
        await self.message_queue.put(msg)

    async def _handle_commands(self, client: Client):
        async with client.filtered_messages('bluetti/command/#') as messages:
            await client.subscribe('bluetti/command/#')
            async for mqtt_message in messages:
                await self._handle_command(mqtt_message)

    async def _handle_messages(self, client: Client):
            while True:
                msg: ParserMessage = await self.message_queue.get()
                await self._handle_message(client, msg)
                self.message_queue.task_done()
    
    async def _handle_command(self, mqtt_message: MQTTMessage):
        # Parse the mqtt_message.topic
        m = COMMAND_TOPIC_RE.match(mqtt_message.topic)
        if not m:
            logging.warn(f'unknown command topic: {mqtt_message.topic}')
            return

        # Find the matching device for the command
        device = next((d for d in self.devices if d.type == m[1] and d.sn == m[2]), None)
        if not device:
            logging.warn(f'unknown device: {m[1]} {m[2]}')
            return

        # Build the command
        cmd: DeviceCommand = None
        if m[3] == 'ups_mode':
            mode = UpsMode[str(mqtt_message.payload)]
            cmd = UpdateFieldCommand(0x0B, 0xB9, mode.value)
        elif m[3] == 'ac_output_on':
            value = 1 if mqtt_message.payload == b'ON' else 0
            cmd = UpdateFieldCommand(0x0B, 0xBF, value)
        elif m[3] == 'dc_output_on':
            value = 1 if mqtt_message.payload == b'ON' else 0
            cmd = UpdateFieldCommand(0x0B, 0xC0, value)
        elif m[3] == 'grid_charge_on':
            value = 1 if mqtt_message.payload == b'ON' else 0
            cmd = UpdateFieldCommand(0x0B, 0xC3, value)
        elif m[3] == 'time_control_on':
            value = 1 if mqtt_message.payload == b'ON' else 0
            cmd = UpdateFieldCommand(0x0B, 0xC5, value)
        elif m[3] == 'auto_sleep_mode':
            mode = AutoSleepMode[str(mqtt_message.payload)]
            cmd = UpdateFieldCommand(0x0B, 0xF5, mode.value)
        else:
            logging.debug(f'Recevied command for unknown topic: {m[3]} - {mqtt_message.topic}')
            return

        await self.bus.put(CommandMessage(device, cmd))

    async def _handle_message(self, client: Client, msg: ParserMessage):
        logging.debug(f'Got a message from {msg.device}: {msg.parser}')
        topic_prefix = f'bluetti/state/{msg.device.type}-{msg.device.sn}/'
        if isinstance(msg.parser, LowerStatusPageParser):
            await client.publish(
                topic_prefix + 'ac_input_power',
                payload=str(msg.parser.ac_input_power).encode()
            )
            await client.publish(
                topic_prefix + 'dc_input_power',
                payload=str(msg.parser.dc_input_power).encode()
            )
            await client.publish(
                topic_prefix + 'ac_output_power',
                payload=str(msg.parser.ac_output_power).encode()
            )
            await client.publish(
                topic_prefix + 'dc_output_power',
                payload=str(msg.parser.dc_output_power).encode()
            )
            await client.publish(
                topic_prefix + 'total_battery_percent',
                payload=str(msg.parser.total_battery_percent).encode()
            )
            await client.publish(
                topic_prefix + 'ac_output_on',
                payload=('ON' if msg.parser.ac_output_on else 'OFF').encode()
            )
            await client.publish(
                topic_prefix + 'dc_output_on',
                payload=('ON' if msg.parser.dc_output_on else 'OFF').encode()
            )
        elif isinstance(msg.parser, MidStatusPageParser):
            await client.publish(
                topic_prefix + 'ac_output_mode',
                payload=msg.parser.ac_output_mode.name.encode()
            )
            await client.publish(
                topic_prefix + 'ac_input_voltage',
                payload=str(msg.parser.ac_input_voltage).encode()
            )
            await client.publish(
                topic_prefix + 'ac_input_frequency',
                payload=str(msg.parser.ac_input_frequency).encode()
            )
        elif isinstance(msg.parser, ControlPageParser):
            await client.publish(
                topic_prefix + 'ups_mode',
                payload=msg.parser.ups_mode.name.encode()
            )
            await client.publish(
                topic_prefix + 'ac_output_on',
                payload=('ON' if msg.parser.ac_output_on else 'OFF').encode()
            )
            await client.publish(
                topic_prefix + 'dc_output_on',
                payload=('ON' if msg.parser.dc_output_on else 'OFF').encode()
            )
            await client.publish(
                topic_prefix + 'grid_charge_on',
                payload=('ON' if msg.parser.grid_charge_on else 'OFF').encode()
            )
            await client.publish(
                topic_prefix + 'time_control_on',
                payload=('ON' if msg.parser.time_control_on else 'OFF').encode()
            )
            await client.publish(
                topic_prefix + 'battery_range_start',
                payload=str(msg.parser.battery_range_start).encode()
            )
            await client.publish(
                topic_prefix + 'battery_range_end',
                payload=str(msg.parser.battery_range_end).encode()
            )
            await client.publish(
                topic_prefix + 'auto_sleep_mode',
                payload=msg.parser.auto_sleep_mode.name.encode()
            )
