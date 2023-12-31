import logging

import RPi.GPIO as GPIO

from app import Application

logging.basicConfig(
    level=logging.INFO,
    # format="%(asctime)s,%(msecs)d %(levelname)s %(filename)s:%(lineno)d\n\t%(message)s",
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

app = Application()


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
