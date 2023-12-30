import asyncio
import logging

from enum import Enum
from typing import Any

import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)


class IDeviceTriggerMode(Enum):
    BELOW_THRESHOLD = 0
    ABOVE_THRESHOLD = 1


class InputDevice:
    _last_value = 0
    notify_callback = None  # async func

    def __init__(self, mode: IDeviceTriggerMode, enabled: bool, bouncetime: int):
        self.mode = mode
        self.enabled = enabled
        self.bouncetime = bouncetime

    def set_notify_callback(self, callback: Any) -> None:
        self.notify_callback = callback

    def current(self) -> int:
        return self._last_value


class GPIODevice(InputDevice):
    def __init__(self, pin: int, mode: IDeviceTriggerMode, enabled: bool, bouncetime: int):
        super().__init__(mode, enabled, bouncetime)

        self.loop = asyncio.get_event_loop()
        self.pin = pin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.callback)  # , bouncetime=self.bouncetime)

    def callback(self, channel: int) -> None:
        logger.debug(f"GPIODevice.callback on {channel}")
        return None


class DigitalInputDevice(GPIODevice):
    def __init__(self, pin: int, mode: IDeviceTriggerMode, enabled: bool, bouncetime: int):
        super().__init__(pin, mode, enabled, bouncetime)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def callback(self, channel: int) -> None:
        if not self.enabled and self.notify_callback is None:
            return

        value = GPIO.input(self.pin)
        if value != self._last_value:
            logger.debug(
                f"DigitalInputDevice.callback on {channel}: value: {value}, last value: {self._last_value}, mode {self.mode}"
            )
            self._last_value = value

            return_value: bool = (
                self._last_value == 1 if self.mode == IDeviceTriggerMode.ABOVE_THRESHOLD else self._last_value == 0
            )
            asyncio.run_coroutine_threadsafe(self.notify_callback(return_value), self.loop)


# class AnalogInputDevice(InputDevice):
#     minAValue = 0
#     maxAValue = 0

#     def __init__(
#         self,
#         pin: int,
#         mode: IDeviceTriggerMode,
#         enabled: bool,
#         read_time: int,
#         threshold: int,
#     ):
#         self.threshold = threshold
#         super().__init__(pin, mode, enabled, read_time)
#         GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#     def minVal(self) -> int:
#         return min(self.minAValue, self.threshold)

#     def maxVal(self) -> int:
#         return max(self.maxAValue, self.threshold)

#     def handle(self) -> bool:
#         if not self.enabled:
#             return False

#         if not self.readTimer.tick():
#             return (
#                 self.lastValue >= self.threshold
#                 if self.mode == IDeviceTriggerMode.ABOVE_THRESHOLD
#                 else self.lastValue <= self.threshold
#             )

#         value = GPIO.input(self.pin)  # TODO: analog input

#         if value != self.lastValue:
#             self.lastValue = value
#             self.changed = True

#         if self.lastValue < self.minAValue:
#             self.minAValue = self.lastValue - 32
#         elif self.minAValue < self.lastValue - 32:
#             self.minAValue += 1

#         if self.lastValue > self.maxAValue:
#             self.maxAValue = self.lastValue + 32
#         elif self.maxAValue > self.lastValue + 32:
#             self.maxAValue -= 1

#         return (
#             self.lastValue >= self.threshold
#             if self.mode == IDeviceTriggerMode.ABOVE_THRESHOLD
#             else self.lastValue <= self.threshold
#         )
