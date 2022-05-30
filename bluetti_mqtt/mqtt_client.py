import asyncio
import logging
from asyncio_mqtt import Client
from bluetti_mqtt.bus import ParserMessage
from bluetti_mqtt.parser import (
    ControlPageParser,
    LowerStatusPageParser,
    MidStatusPageParser,
)


class MQTTClient:
    def __init__(self, host: str, bus: asyncio.Queue):
        self.host = host
        self.bus = bus

    async def run(self):
        async with Client(self.host) as client:
            while True:
                logging.debug(f'queue size: {self.bus.qsize()}')
                msg = await self.bus.get()
                if isinstance(msg, ParserMessage):
                    await self._handle(client, msg)
                self.bus.task_done()

    async def _handle(self, client: Client, msg: ParserMessage):
        logging.debug(f'Got a message from {msg.device}: {msg.parser}')
        topic_prefix = f'bluetti/state/{msg.device.type}{msg.device.sn}/'
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
