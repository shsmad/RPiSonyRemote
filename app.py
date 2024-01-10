import asyncio
import dbm
import functools
import logging
import signal

from concurrent.futures import ThreadPoolExecutor

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

from libs.button import Button
from libs.device.input import DigitalInputDevice
from libs.device.output import BluetoothOuputDevice, GPhotoOutputDevice, ScreenCounterOutputDevice
from libs.eventbus import EventBusDefaultDict
from libs.eventtypes import (
    ButtonClickEvent,
    ButtonHoldEvent,
    ButtonPressEvent,
    ButtonStepEvent,
    Event,
    MenuClickEvent,
    MenuHoldEvent,
    MenuRotateEvent,
)
from libs.helpers import handle_exception, shutdown
from libs.hwinfo import HWInfo
from libs.router import Router
from menu.data import Config
from menu.oled import OledMenu

logger = logging.getLogger(__name__)

BUTTON_LEFT = 5
BUTTON_RIGHT = 26
BUTTON_ENTER = 13
DIGITAL_INPUT = 22
RPI0_LED = 29


class Application:
    def __init__(self, loop_debug: bool = False, loop_slow_callback_duration: float = 0.2) -> None:
        self.storage = dbm.open("storage", "c")
        self.config = Config(self.storage)

        self.bus = EventBusDefaultDict()
        self.executor = ThreadPoolExecutor()

        self.setup_loop(loop_debug, loop_slow_callback_duration)

        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial)
        self.oled_menu = OledMenu(None, oled=device, config=self.config)

        self.setup_devices()
        self.setup_buttons()

        self.hwinfo = HWInfo(config=self.config)

    def setup_loop(self, loop_debug: bool = False, loop_slow_callback_duration: float = 0.2) -> None:
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

    def setup_devices(self) -> None:
        di_i = DigitalInputDevice(self.config, DIGITAL_INPUT)
        # ConsoleOutputDevice(
        #     shutter_lag=config.shutter_lag.value,
        #     release_lag=config.release_lag.value,
        # ),
        # scr_o = ScreenOutputDevice(config=self.config, canvas=self.oled_menu.draw)
        scrc_o = ScreenCounterOutputDevice(config=self.config, canvas=self.oled_menu.draw)
        # pin_o = PinOutputDevice(config=self.config, pin=RPI0_LED, inverted=True)
        self.bt_o = BluetoothOuputDevice(config=self.config)

        gphoto_o = GPhotoOutputDevice(config=self.config)

        self.router = Router(input_devices=[di_i], output_devices=[scrc_o, gphoto_o])

    def setup_buttons(self) -> None:
        self.buttons = [Button(BUTTON_LEFT), Button(BUTTON_RIGHT), Button(BUTTON_ENTER)]

        for event_type in (ButtonPressEvent, ButtonClickEvent, ButtonStepEvent, ButtonHoldEvent):
            self.bus.add_listener(event_type, self.on_button_event)

    async def on_button_event(self, event: Event) -> None:
        if isinstance(event, (ButtonClickEvent, ButtonStepEvent)) and event.pin in (BUTTON_LEFT, BUTTON_RIGHT):
            self.bus.emit(MenuRotateEvent(direction=-1 if event.pin == BUTTON_LEFT else 1))

        if isinstance(event, ButtonClickEvent) and event.pin == BUTTON_ENTER:
            self.bus.emit(MenuHoldEvent() if event.hold_time else MenuClickEvent())

    def run(self) -> None:
        self.oled_menu.init()

        try:
            self.loop.create_task(self.hwinfo.read_and_reset(1000))
            self.loop.create_task(self.bt_o.search())
            logging.info("Starting the RPiSonyRemote service.")
            self.loop.run_forever()

        except Exception as e:
            logger.exception(e)
        finally:
            self.storage.close()
            for button in self.buttons:
                button.cleanup()
            self.loop.close()
            logging.info("Successfully shutdown the RPiSonyRemote service.")
