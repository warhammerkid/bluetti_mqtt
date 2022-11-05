import asyncio
import logging
from bleak import BleakClient, BleakError
from bluetti_mqtt.core import CommandResponse, DeviceCommand
from .exc import BadConnectionError, InvalidRequestError, ParseError


class BluetoothClient:
    RESPONSE_TIMEOUT = 5
    WRITE_UUID = '0000ff02-0000-1000-8000-00805f9b34fb'
    NOTIFY_UUID = '0000ff01-0000-1000-8000-00805f9b34fb'

    current_command: DeviceCommand
    notify_future: asyncio.Future
    notify_response: CommandResponse

    def __init__(self, address: str):
        self.address = address
        self.client = BleakClient(address)
        self.command_queue = asyncio.Queue()
        self.notify_future = None
        self.loop = asyncio.get_running_loop()

    @property
    def is_connected(self):
        return self.client.is_connected

    async def perform(self, cmd: DeviceCommand):
        future = self.loop.create_future()
        await self.command_queue.put((cmd, future))
        return future

    async def perform_nowait(self, cmd: DeviceCommand):
        await self.command_queue.put((cmd, None))

    async def run(self):
        while True:
            # Try to connect
            try:
                await self.client.connect()
                logging.info(f'Connected to device: {self.address}')
            except BaseException:
                logging.exception(f'Error connecting to device {self.address}:')
                await asyncio.sleep(1)
                logging.info(f'Retrying connection to {self.address}')
                continue

            # Register for notifications and run command loop
            try:
                await self.client.start_notify(
                    self.NOTIFY_UUID,
                    self._notification_handler)
                await self._perform_commands(self.client)
            except (BleakError, asyncio.TimeoutError):
                logging.exception(f'Reconnecting to {self.address} after error:')
                continue
            except BadConnectionError:
                logging.exception(f'Delayed reconnect to {self.address} after error:')
                await asyncio.sleep(1)
            finally:
                await self.client.disconnect()

    async def _perform_commands(self, client):
        while client.is_connected:
            cmd, cmd_future = await self.command_queue.get()
            retries = 0
            while retries < 5:
                try:
                    # Prepare to make request
                    self.current_command = cmd
                    self.notify_future = self.loop.create_future()
                    self.notify_response = CommandResponse(bytearray())

                    # Make request
                    await client.write_gatt_char(
                        self.WRITE_UUID,
                        bytes(self.current_command))

                    # Wait for response
                    res = await asyncio.wait_for(
                        self.notify_future,
                        timeout=self.RESPONSE_TIMEOUT)
                    if cmd_future:
                        cmd_future.set_result(res)

                    # Success!
                    break
                except ParseError:
                    # For safety, wait the full timeout before retrying again
                    retries += 1
                    await asyncio.sleep(self.RESPONSE_TIMEOUT)
                except asyncio.TimeoutError:
                    retries += 1
                except (InvalidRequestError, BleakError) as err:
                    if cmd_future:
                        cmd_future.set_exception(err)

                    # Don't retry
                    break
                except BadConnectionError as err:
                    # Exit command loop
                    if cmd_future:
                        cmd_future.set_exception(err)
                    self.command_queue.task_done()
                    raise

            if retries == 5:
                err = BadConnectionError('too many retries')
                if cmd_future:
                    cmd_future.set_exception(err)
                self.command_queue.task_done()
                raise err
            else:
                self.command_queue.task_done()

    def _notification_handler(self, _sender: int, data: bytearray):
        # Ignore notifications we don't expect
        if not self.notify_future or self.notify_future.done():
            return

        # If something went wrong, we might get weird data.
        if data == b'AT+NAME?\r' or data == b'AT+ADV?\r':
            err = BadConnectionError('Got AT+ notification')
            self.notify_future.set_exception(err)
            return

        # Save data
        self.notify_response.extend(data)

        if len(self.notify_response) == self.current_command.response_size():
            if self.notify_response.is_valid():
                self.notify_future.set_result(self.notify_response)
            else:
                self.notify_future.set_exception(ParseError('Failed checksum'))
        elif self.notify_response.is_invalid_error():
            # We got an invalid request error response
            msg = f'Error {self.notify_response.data[2]}'
            self.notify_future.set_exception(InvalidRequestError(msg))
