import asyncio

from menu.data import Config

from .device.input import GPIODevice
from .device.output import OutputDevice
from .timer import TimerMs


class Router:
    def __init__(self, input_devices: list[GPIODevice], output_devices: list[OutputDevice], config: Config) -> None:
        self.timer = TimerMs(10, 0, 0)
        self.input_devices = input_devices
        self.output_devices = output_devices

        for device in self.input_devices:
            device.set_notify_callback(self.notify_callback)

    async def notify_callback(self, value: bool) -> None:
        for o_device in self.output_devices:
            if value:
                asyncio.create_task(o_device.shutter())
            else:
                asyncio.create_task(o_device.release())

    def set_shutter_lag(self, lag: int) -> None:
        for o_device in self.output_devices:
            o_device.shutter_lag = lag

    def set_release_lag(self, lag: int) -> None:
        for o_device in self.output_devices:
            o_device.release_lag = lag

    def set_bouncetime(self, bouncetime: int) -> None:
        for i_device in self.input_devices:
            i_device.bouncetime = bouncetime
