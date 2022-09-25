from ast import Str
import asyncio
from email import message
import json
import logging
import re
from typing import List, Optional
from asyncio_mqtt import Client, MqttError
from paho.mqtt.client import MQTTMessage
from bluetti_mqtt.bus import CommandMessage, EventBus, ParserMessage
from bluetti_mqtt.core import BluettiDevice, DeviceCommand


COMMAND_TOPIC_RE = re.compile(r'^bluetti/command/(\w+)-(\d+)/([a-z_]+)$')


class MQTTClient:
    message_queue: asyncio.Queue
    value_cache = {}

    messageParsers = {'ac_input_power': lambda key, msg: str(msg.parsed[key]).encode(),
                      'dc_input_power': lambda key, msg: str(msg.parsed[key]).encode(),
                      'ac_output_power': lambda key, msg: str(msg.parsed[key]).encode(),
                      'dc_output_power': lambda key, msg: str(msg.parsed[key]).encode(),
                      'total_battery_percent': lambda key, msg: str(msg.parsed[key]).encode(),
                      'ac_output_on': lambda key, msg: str(msg.parsed[key]).encode(),
                      'dc_output_on': lambda key, msg: str('ON' if msg.parsed[key] else 'OFF').encode(),
                      'ac_output_mode': lambda key, msg: msg.parsed[key].name.encode(),
                      'internal_ac_voltage': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_current_one': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_power_one': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_ac_frequency': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_current_two': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_power_two': lambda key, msg: str(msg.parsed[key]).encode(),
                      'ac_input_voltage': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_current_three': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_power_three': lambda key, msg: str(msg.parsed[key]).encode(),
                      'ac_input_frequency': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_dc_input_voltage': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_dc_input_power': lambda key, msg: str(msg.parsed[key]).encode(),
                      'internal_dc_input_current': lambda key, msg: str(msg.parsed[key]).encode(),
                      'ups_mode': lambda key, msg: str(msg.parsed[key].name.encode()),
                      'grid_charge_on': lambda key, msg: str('ON' if msg.parsed[key] else 'OFF').encode(),
                      'time_control_on': lambda key, msg: str('ON' if msg.parsed[key] else 'OFF').encode(),
                      'battery_range_start': lambda key, msg: str(msg.parsed[key]).encode(),
                      'battery_range_end': lambda key, msg:  str(msg.parsed[key]).encode(),
                      'auto_sleep_mode': lambda key, msg: msg.parsed[key].name.encode(),
                      'led_mode': lambda key, msg: msg.parsed[key].name.encode()
                      }

    def __init__(
        self,
        devices: List[BluettiDevice],
        bus: EventBus,
        hostname: str,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.devices = devices
        self.bus = bus
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

    async def run(self):
        while True:
            logging.info('Connecting to MQTT broker...')
            try:
                async with Client(hostname=self.hostname, port=self.port, username=self.username, password=self.password) as client:
                    logging.info('Connected to MQTT broker')

                    # Connect to event bus
                    self.message_queue = asyncio.Queue()
                    self.bus.add_parser_listener(self.handle_message)

                    # Announce device to Home Assistant
                    await self._send_discovery_message(client)

                    # Handle pub/sub
                    await asyncio.gather(
                        self._handle_commands(client),
                        self._handle_messages(client)
                    )
            except MqttError as error:
                logging.error(f'MQTT error: {error}')
                await asyncio.sleep(5)

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
        device = next((d for d in self.devices if d.type ==
                      m[1] and d.sn == m[2]), None)
        if not device:
            logging.warn(f'unknown device: {m[1]} {m[2]}')
            return

        # Check if the device supports setting this field
        if not device.has_field_setter(m[3]):
            logging.warn(
                f'Recevied command for unknown topic: {m[3]} - {mqtt_message.topic}')
            return

        cmd: DeviceCommand = None
        if m[3] == 'ups_mode' or m[3] == 'auto_sleep_mode' or m[3] == 'led_mode':
            value = mqtt_message.payload.decode('ascii')
            cmd = device.build_setter_command(m[3], value)
        elif m[3] == 'ac_output_on' or m[3] == 'dc_output_on' or m[3] == 'grid_charge_on' or m[3] == 'time_control_on':
            value = mqtt_message.payload == b'ON'
            cmd = device.build_setter_command(m[3], value)
        else:
            logging.warn(
                f'Recevied command for unhandled topic: {m[3]} - {mqtt_message.topic}')
            return

        await self.bus.put(CommandMessage(device, cmd))

    async def _send_discovery_message(self, client: Client):

        def payload(id: str, device: BluettiDevice, **kwargs) -> str:
            # Unknown keys are allowed but ignored by Home Assistant
            payload_dict = {
                'state_topic': f'bluetti/state/{device.type}-{device.sn}/{id}',
                'command_topic': f'bluetti/command/{device.type}-{device.sn}/{id}',
                'device': {
                    'identifiers': [
                        f'{device.sn}'
                    ],
                    'manufacturer': 'Bluetti',
                    'name': f'{device.type} {device.sn}',
                    'model': device.type
                },
                'unique_id': f'{device.sn}_{id}',
                'object_id': f'{device.type}_{id}',
            }

            for key, value in kwargs.items():
                payload_dict[key] = value

            return json.dumps(payload_dict)

        # Loop through devices
        for d in self.devices:
            await client.publish(f'homeassistant/sensor/{d.sn}_ac_input_power/config',
                                 payload=payload(
                                     id='ac_input_power',
                                     device=d,
                                     name='AC Input Power',
                                     unit_of_measurement='W',
                                     device_class='power',
                                     state_class='measurement',
                                     force_update=True)
                                 .encode(),
                                 retain=True
                                 )

            await client.publish(f'homeassistant/sensor/{d.sn}_dc_input_power/config',
                                 payload=payload(
                                     id='dc_input_power',
                                     device=d,
                                     name='DC Input Power',
                                     unit_of_measurement='W',
                                     device_class='power',
                                     state_class='measurement',
                                     force_update=True)
                                 .encode(),
                                 retain=True
                                 )

            await client.publish(f'homeassistant/sensor/{d.sn}_ac_output_power/config',
                                 payload=payload(
                                     id='ac_output_power',
                                     device=d,
                                     name='AC Output Power',
                                     unit_of_measurement='W',
                                     device_class='power',
                                     state_class='measurement',
                                     force_update=True)
                                 .encode(),
                                 retain=True
                                 )

            await client.publish(f'homeassistant/sensor/{d.sn}_dc_output_power/config',
                                 payload=payload(
                                     id='dc_output_power',
                                     device=d,
                                     name='DC Output Power',
                                     unit_of_measurement='W',
                                     device_class='power',
                                     state_class='measurement',
                                     force_update=True)
                                 .encode(),
                                 retain=True
                                 )

            await client.publish(f'homeassistant/sensor/{d.sn}_total_battery_percent/config',
                                 payload=payload(
                                     id='total_battery_percent',
                                     device=d,
                                     name='Total Battery Percent',
                                     unit_of_measurement='%',
                                     device_class='battery',
                                     state_class='measurement')
                                 .encode(),
                                 retain=True
                                 )

            await client.publish(f'homeassistant/switch/{d.sn}_ac_output_on/config',
                                 payload=payload(
                                     id='ac_output_on',
                                     device=d,
                                     name='AC Output',
                                     device_class='outlet')
                                 .encode(),
                                 retain=True
                                 )

            await client.publish(f'homeassistant/switch/{d.sn}_dc_output_on/config',
                                 payload=payload(
                                     id='dc_output_on',
                                     device=d,
                                     name='DC Output',
                                     device_class='outlet')
                                 .encode(),
                                 retain=True
                                 )

            logging.info(
                f'Sent discovery message of {d.type}-{d.sn} to Home Assistant')

    async def _update_value(self, client: Client, topic, key, value):
        if self.value_cache.get(key, None) != value:
            self.value_cache[key] = value
            logging.debug(f'publishing new value for: {key}, value: {value}')
            await client.publish(
                topic,
                payload=value
            )

    async def _handle_message(self, client: Client, msg: ParserMessage):
        topic_prefix = f'bluetti/state/{msg.device.type}-{msg.device.sn}/'
        logging.debug(f'Got a message from {msg.device}: {msg.parsed}')

        if 'pack_battery_percent' in msg.parsed:
            pack_details = {
                'percent': msg.parsed['pack_battery_percent'],
                'voltages': [float(d) for d in msg.parsed['cell_voltages']],
            }
            packKey = f'pack_details{msg.parsed["pack_num"]}'
            self._update_value(client, topic_prefix + packKey, packKey,
                               json.dumps(pack_details, separators=(',', ':')).encode())

        for key, formatLambda in self.messageParsers.items():
            if key in msg.parsed:
                # logging.info(f'calling _update_value for: {key}')
                await self._update_value(client, topic_prefix + key, key, formatLambda(key, msg))
