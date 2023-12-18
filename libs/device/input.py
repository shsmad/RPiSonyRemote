from enum import Enum

import RPi.GPIO as GPIO

from libs.timer import TimerMs


class IDeviceTriggerMode(Enum):
    BELOW_THRESHOLD = 0
    ABOVE_THRESHOLD = 1


class InputDevice:
    lastValue = 0
    changed = False

    def __init__(self, pin: int, mode: IDeviceTriggerMode, enabled: bool, read_time: int):
        self.pin = pin
        self.mode = mode  # from settings
        self.enabled = enabled  # from settings

        self.readTimer = TimerMs(read_time, 1, 0)

    def handle(self) -> bool:
        return False

    def current(self) -> int:
        return self.lastValue

    def is_changed(self) -> bool:
        _changed = self.changed
        self.changed = False
        return _changed


class DigitalInputDevice(InputDevice):
    def __init__(self, pin: int, mode: IDeviceTriggerMode, enabled: bool, read_time: int):
        super().__init__(pin, mode, enabled, read_time)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def handle(self) -> bool:
        if not self.enabled:
            return False

        if not self.readTimer.tick():
            return self.lastValue == 1 if self.mode == IDeviceTriggerMode.ABOVE_THRESHOLD else self.lastValue == 0

        value = GPIO.input(self.pin)

        if value != self.lastValue:
            self.lastValue = value
            self.changed = True

        return self.lastValue == 1 if self.mode == IDeviceTriggerMode.ABOVE_THRESHOLD else self.lastValue == 0


class AnalogInputDevice(InputDevice):
    minAValue = 0
    maxAValue = 0

    def __init__(
        self,
        pin: int,
        mode: IDeviceTriggerMode,
        enabled: bool,
        read_time: int,
        threshold: int,
    ):
        self.threshold = threshold
        super().__init__(pin, mode, enabled, read_time)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def minVal(self) -> int:
        return min(self.minAValue, self.threshold)

    def maxVal(self) -> int:
        return max(self.maxAValue, self.threshold)

    def handle(self) -> bool:
        if not self.enabled:
            return False

        if not self.readTimer.tick():
            return (
                self.lastValue >= self.threshold
                if self.mode == IDeviceTriggerMode.ABOVE_THRESHOLD
                else self.lastValue <= self.threshold
            )

        value = GPIO.input(self.pin)  # TODO: analog input

        if value != self.lastValue:
            self.lastValue = value
            self.changed = True

        if self.lastValue < self.minAValue:
            self.minAValue = self.lastValue - 32
        elif self.minAValue < self.lastValue - 32:
            self.minAValue += 1

        if self.lastValue > self.maxAValue:
            self.maxAValue = self.lastValue + 32
        elif self.maxAValue > self.lastValue + 32:
            self.maxAValue -= 1

        return (
            self.lastValue >= self.threshold
            if self.mode == IDeviceTriggerMode.ABOVE_THRESHOLD
            else self.lastValue <= self.threshold
        )
