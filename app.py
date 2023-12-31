import asyncio
import dbm
import functools
import logging
import signal

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

from libs.button import Button
from libs.device.input import DigitalInputDevice
from libs.device.output import BluetoothOuputDevice, PinOutputDevice, ScreenOutputDevice
from libs.eventbus import EventBusDefaultDict
from libs.helpers import handle_exception, shutdown
from libs.router import Router
from menu.data import get_config
from menu.oled import OledMenu

logger = logging.getLogger(__name__)


class Application:
    def __init__(self, loop_debug: bool = False, loop_slow_callback_duration: float = 0.2) -> None:
        self.storage = dbm.open("storage", "c")
        self.config = get_config(self.storage)
        self.bus = EventBusDefaultDict()
        self.executor = ThreadPoolExecutor()

        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(loop_debug)
        self.loop.slow_callback_duration = loop_slow_callback_duration  # in seconds

        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            self.loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(shutdown(self.loop, self.executor, signal=s))
            )

        handle_exc_func = functools.partial(handle_exception, self.executor)

        self.loop.set_exception_handler(handle_exc_func)

        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial)
        self.oled_menu = OledMenu(None, oled=device, config=self.config)

        di_i = DigitalInputDevice(self.config, 22)

        # ConsoleOutputDevice(
        #     shutter_lag=config.shutter_lag.value,
        #     release_lag=config.release_lag.value,
        # ),
        scr_o = ScreenOutputDevice(config=self.config, canvas=self.oled_menu.draw)
        # rpi0 led
        pin_o = PinOutputDevice(config=self.config, pin=29, inverted=True)
        self.bt_o = BluetoothOuputDevice(config=self.config)

        self.router = Router(input_devices=[di_i], output_devices=[scr_o, pin_o, self.bt_o])

        self.btn_left = Button(5, callback=self.on_btn_left)
        self.btn_right = Button(26, callback=self.on_btn_right)
        self.btn_press = Button(13, callback=self.on_btn_press)

    async def on_btn_left(self, event_type: str, *args: Any) -> None:
        # print("on_btn_left", event_type, args)
        if event_type in {"click", "step"}:
            self.oled_menu.onRotate(-1, 1, False)

    async def on_btn_right(self, event_type: str, *args: Any) -> None:
        # print("on_btn_right", event_type, args)
        if event_type in {"click", "step"}:
            self.oled_menu.onRotate(1, 1, False)

    async def on_btn_press(self, event_type: str, *args: Any) -> None:
        # Handle button events here
        # print("on_btn_press", event_type, args)
        if event_type == "click":
            if args[2]:
                self.oled_menu.onKeyClickAfterHold(*args)
            else:
                self.oled_menu.onKeyClick()

    def run(self) -> None:
        self.oled_menu.init()

        try:
            self.loop.create_task(self.oled_menu.tick())
            self.loop.create_task(self.bt_o.search())
            self.loop.run_forever()

        except Exception as e:
            logger.exception(e)
        finally:
            self.storage.close()
            for button in (self.btn_left, self.btn_right, self.btn_press):
                button.cleanup()
            self.loop.close()
            logging.info("Successfully shutdown the RPiSonyRemote service.")
