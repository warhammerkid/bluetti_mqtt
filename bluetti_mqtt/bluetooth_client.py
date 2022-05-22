import asyncio
from bleak import BleakClient, BleakError
from .utils import modbus_crc
from .commands import DeviceCommand
from .exc import BadConnectionError, ParseError


class BluetoothClient:
    RESPONSE_TIMEOUT = 5
    WRITE_UUID = '0000ff02-0000-1000-8000-00805f9b34fb'
    NOTIFY_UUID = '0000ff01-0000-1000-8000-00805f9b34fb'

    current_command: DeviceCommand
    notify_future: asyncio.Future
    notify_data: bytearray

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
            try:
                await self.client.connect()
                await self.client.start_notify(
                    self.NOTIFY_UUID,
                    self._notification_handler)
                await self._perform_commands(self.client)
            except (BleakError, asyncio.TimeoutError):
                continue
            except BadConnectionError:
                # Something went wrong somewhere
                await self.client.disconnect()
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
                    self.notify_data = bytearray()

                    # Make request
                    await client.write_gatt_char(
                        self.WRITE_UUID,
                        self.current_command)

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
                except BleakError as err:
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
        self.notify_data.extend(data)

        # Check if we're done reading the data we expected
        if len(self.notify_data) == self.current_command.response_size():
            # Validate the CRC
            crc = modbus_crc(self.notify_data[0:-2])
            crc_bytes = crc.to_bytes(2, byteorder='little')
            if self.notify_data[-2:] == crc_bytes:
                self.notify_future.set_result(self.notify_data)
            else:
                self.notify_future.set_exception(ParseError('Failed checksum'))
