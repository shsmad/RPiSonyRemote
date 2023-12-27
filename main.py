import asyncio
import dbm
import functools
import logging
import signal
import sys

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import RPi.GPIO as GPIO

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

from libs.button import Button
from libs.helpers import handle_exception, shutdown
from libs.router import Router
from menu.data import get_config
from menu.oled import OledMenu

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

# define EB_HOLD 500
# define EB_FAST 50
# define ANALOG_IN_PIN A2
# define DIGITAL_IN_PIN 8
# define OPTRON_OUT_PIN LED_BUILTIN
# include <TimerMs.h>
# include "settings/settings.h"
# include "bleeeprom/EEManager.h"
# include "menu/oled.h"
# include "device/input.h"
# include "device/output.h"
# include "device/router.h"
# include "ble/utils.h"
# include "ble/RemoteStatus.h"
# include "ble/BLEScanner.h"
# include "ble/BLECamera.h"


GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

storage = dbm.open("storage", "c")
config = get_config(storage)

oled_menu = OledMenu(None, oled=device, config=config)

router = Router([], [])


async def on_btn_left(event_type: str, *args: Any) -> None:
    """
    Handle button events.

    Args:
        event_type (str): The type of button event.
        *args (Tuple): Additional arguments for the event.

    Returns:
        None
    """
    # print("on_btn_left", event_type, args)
    if event_type in {"click", "step"}:
        oled_menu.onRotate(-1, 1, False)


async def on_btn_right(event_type: str, *args: Any) -> None:
    """
    Handle button events.

    Args:
        event_type (str): The type of button event.
        *args: Additional arguments.

    Returns:
        None
    """
    # print("on_btn_right", event_type, args)
    if event_type in {"click", "step"}:
        oled_menu.onRotate(1, 1, False)


async def on_btn_press(event_type: str, *args: Any) -> None:
    """
    Handle button events.

    Args:
        event_type (str): The type of button event.
        args (tuple): Additional arguments for the event.

    Returns:
        None
    """
    # Handle button events here
    # print("on_btn_press", event_type, args)
    if event_type == "click":
        if args[2]:
            oled_menu.onKeyClickAfterHold(*args)
        else:
            oled_menu.onKeyClick()


btn_left = Button(5, callback=on_btn_left)
btn_right = Button(26, callback=on_btn_right)
btn_press = Button(13, callback=on_btn_press)


def setup() -> None:
    router.init()
    oled_menu.init()


def main() -> None:
    executor = ThreadPoolExecutor()

    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.slow_callback_duration = 0.2  # in seconds
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(loop, executor, signal=s)))

    handle_exc_func = functools.partial(handle_exception, executor)

    loop.set_exception_handler(handle_exc_func)

    setup()
    try:
        loop.create_task(oled_menu.tick())
        loop.run_forever()

    except Exception:
        print("Error:", sys.exc_info()[0])
    finally:
        storage.close()
        for button in (btn_left, btn_right, btn_press):
            button.cleanup()
        loop.close()
        logging.info("Successfully shutdown the RPiSonyRemote service.")


if __name__ == "__main__":
    main()
