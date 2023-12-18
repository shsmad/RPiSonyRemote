import RPi.GPIO as GPIO

from luma.oled.device import device as LumaDevice

from libs.timer import TimerMs


class OutputDevice:
    def __init__(self, activateDelay: int, deactivateDelay: int, enabled: bool):
        self.activateDelay = activateDelay
        self.deactivateDelay = deactivateDelay
        self.enabled = enabled

        self.active = False
        self.activateTimer = TimerMs(activateDelay, 0, 0)
        self.deactivateTimer = TimerMs(deactivateDelay, 0, 0)

    def tick(self, trigger: bool) -> None:
        pass


class PinOutputDevice(OutputDevice):
    def __init__(self, activateDelay: int, deactivateDelay: int, enabled: bool, pin: int):
        super().__init__(activateDelay, deactivateDelay, enabled)
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)

    def tick(self, trigger: bool) -> None:
        if self.enabled and trigger and not self.activateTimer.active() and not self.active:
            self.activateTimer.setTimerMode()
            self.activateTimer.setTime(self.activateDelay)
            self.activateTimer.start()

        if self.activateTimer.tick() and self.enabled:
            self.active = True
            GPIO.output(self.pin, GPIO.HIGH)

            self.deactivateTimer.setTimerMode()
            self.deactivateTimer.setTime(self.deactivateDelay)
            self.deactivateTimer.start()

        if self.enabled and self.active and trigger:
            self.deactivateTimer.setTimerMode()
            self.deactivateTimer.setTime(self.deactivateDelay)
            self.deactivateTimer.start()

        if self.active and self.deactivateTimer.tick():
            GPIO.output(self.pin, GPIO.LOW)
            self.active = False
            self.activateTimer.stop()
            self.deactivateTimer.stop()


class OledOutputDevice(OutputDevice):
    def __init__(self, activateDelay: int, deactivateDelay: int, enabled: bool, oled: LumaDevice):
        super().__init__(activateDelay, deactivateDelay, enabled)
        self.screen = oled

    def tick(self, trigger: bool) -> None:
        if self.enabled and trigger and not self.activateTimer.active() and not self.active:
            self.activateTimer.setTimerMode()
            self.activateTimer.setTime(self.activateDelay)
            self.activateTimer.start()

        if self.activateTimer.tick() and self.enabled:
            self.active = True
            self.screen.invertDisplay(True)  # TODO
            self.screen.update()
            self.deactivateTimer.setTimerMode()
            self.deactivateTimer.setTime(self.deactivateDelay)
            self.deactivateTimer.start()

        if self.enabled and self.active and trigger:
            self.deactivateTimer.setTimerMode()
            self.deactivateTimer.setTime(self.deactivateDelay)
            self.deactivateTimer.start()

        if self.active and self.deactivateTimer.tick():
            self.screen.invertDisplay(False)  # TODO
            self.screen.update()
            self.active = False
            self.activateTimer.stop()
            self.deactivateTimer.stop()
