import asyncio
from dataclasses import dataclass
import logging
from typing import Callable, List, Union
from bluetti_mqtt.core import BluettiDevice, DeviceCommand


@dataclass(frozen=True)
class ParserMessage:
    device: BluettiDevice
    parsed: dict


@dataclass(frozen=True)
class CommandMessage:
    device: BluettiDevice
    command: DeviceCommand


class EventBus:
    parser_listeners: List[Callable[[ParserMessage], None]]
    command_listeners: List[Callable[[CommandMessage], None]]
    queue: asyncio.Queue

    def __init__(self):
        self.parser_listeners = []
        self.command_listeners = []
        self.queue = None

    def add_parser_listener(self, cb: Callable[[ParserMessage], None]):
        self.parser_listeners.append(cb)

    def add_command_listener(self, cb: Callable[[CommandMessage], None]):
        self.command_listeners.append(cb)

    async def put(self, msg: Union[ParserMessage, CommandMessage]):
        if not self.queue:
            self.queue = asyncio.Queue()

        await self.queue.put(msg)

    """Reads messages and notifies listeners"""
    async def run(self):
        if not self.queue:
            self.queue = asyncio.Queue()

        while True:
            msg = await self.queue.get()
            logging.debug(f'queue size: {self.queue.qsize()}')
            if isinstance(msg, ParserMessage):
                await asyncio.gather(*[pl(msg) for pl in self.parser_listeners])
            elif isinstance(msg, CommandMessage):
                await asyncio.gather(*[cl(msg) for cl in self.command_listeners])
            self.queue.task_done()
