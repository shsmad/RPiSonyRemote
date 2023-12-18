import asyncio
import dbm
import sys

import RPi.GPIO as GPIO

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
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

from libs.button import Button
from libs.router import Router
from menu.oled import OledMenu

GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

storage = dbm.open("storage", "c")

oled_menu = OledMenu(None, None, oled=device, storage=storage)

router = Router([], [])


async def on_btn_left(event_type, *args):
    # Handle button events here
    print("on_btn_left", event_type, args)
    if event_type == "click":
        oled_menu.onRotate(-1, 1, False)


async def on_btn_right(event_type, *args):
    # Handle button events here
    print("on_btn_right", event_type, args)
    if event_type == "click":
        oled_menu.onRotate(1, 1, False)


async def on_btn_press(event_type, *args):
    # Handle button events here
    print("on_btn_press", event_type, args)
    if event_type == "click":
        oled_menu.onKeyClick()
    elif event_type in ("hold", "step"):
        oled_menu.onKeyHeld()


btn_left = Button(5, callback=on_btn_left)
btn_right = Button(26, callback=on_btn_right)
btn_press = Button(13, callback=on_btn_press)


def setup():
    router.init()
    oled_menu.init()


setup()

try:
    loop = asyncio.get_event_loop()
    loop.run_forever()
except Exception:
    print("Error:", sys.exc_info()[0])
finally:
    for button in (btn_left, btn_right, btn_press):
        button.cleanup()
    loop.close()
