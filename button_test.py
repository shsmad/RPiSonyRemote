import asyncio
import sys

import RPi.GPIO as GPIO

from libs.button import Button

GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)


async def button_callback(event_type, *args):
    # Handle button events here
    print(event_type, args)


PINS = (21, 20, 16, 5, 6, 13, 19, 26)
buttons = [Button(pin, callback=button_callback) for pin in PINS]

try:
    loop = asyncio.get_event_loop()
    loop.run_forever()
except Exception:
    print("Error:", sys.exc_info()[0])
finally:
    for button in buttons:
        button.cleanup()
    loop.close()
