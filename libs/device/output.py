import asyncio
import logging

import RPi.GPIO as GPIO

from luma.core.render import canvas as Canvas

from libs.fontawesome import fa

logger = logging.getLogger(__name__)


class OutputDevice:
    def __init__(self, shutter_lag: int = 0, release_lag: int = 0, enabled: bool = True):
        self.shutter_lag = shutter_lag
        self.release_lag = release_lag
        self.enabled = enabled
        self.can_release = True

    async def shutter(self) -> None:
        pass

    async def release(self) -> None:
        pass


class ConsoleOutputDevice(OutputDevice):
    def __init__(self, shutter_lag: int = 0, release_lag: int = 0, enabled: bool = True):
        super().__init__(shutter_lag, release_lag, enabled)

    async def shutter(self) -> None:
        self.can_release = False
        logger.info(f"-> ConsoleOutputDevice Shutter {self.shutter_lag}")
        await asyncio.sleep(self.shutter_lag / 1000)
        logger.info(f"<- ConsoleOutputDevice Shutter {self.shutter_lag}")
        self.can_release = True

    async def release(self) -> None:
        while not self.can_release:
            await asyncio.sleep(0.01)
        logger.info(f"-> ConsoleOutputDevice Release {self.release_lag}")
        await asyncio.sleep(self.release_lag / 1000)
        logger.info(f"<- ConsoleOutputDevice Release {self.release_lag}")


class ScreenOutputDevice(OutputDevice):
    def __init__(self, canvas: Canvas, shutter_lag: int = 0, release_lag: int = 0, enabled: bool = True):
        super().__init__(shutter_lag, release_lag, enabled)
        self.draw = canvas

    async def shutter(self) -> None:
        self.can_release = False
        logger.info(f"-> ScreenOutputDevice Shutter {self.shutter_lag}")
        with self.draw as draw:
            text, font = fa("hourglass", 16)
            draw.text((0, 16), text, font=font, fill="white")
        await asyncio.sleep(self.shutter_lag / 1000)
        with self.draw as draw:
            text, font = fa("camera", 16)
            draw.text((16, 16), text, font=font, fill="white")
        logger.info(f"<- ScreenOutputDevice Shutter {self.shutter_lag}")
        self.can_release = True

    async def release(self) -> None:
        while not self.can_release:
            await asyncio.sleep(0.01)
        logger.info(f"-> ScreenOutputDevice Release {self.release_lag}")
        with self.draw as draw:
            draw.rectangle((0, 16, 16, 32), fill="black", outline="black")
            text, font = fa("hourglass-end", 16)
            draw.text((0, 16), text, font=font, fill="white")
        await asyncio.sleep(self.release_lag / 1000)
        with self.draw as draw:
            draw.rectangle((0, 16, 32, 32), fill="black", outline="black")
        logger.info(f"<- ScreenOutputDevice Release {self.release_lag}")


class LedOutputDevice(OutputDevice):
    def __init__(self, pin: int = 29, shutter_lag: int = 0, release_lag: int = 0, enabled: bool = True):
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT)
        super().__init__(shutter_lag, release_lag, enabled)

    async def shutter(self) -> None:
        self.can_release = False
        logger.info(f"-> LedOutputDevice Shutter {self.shutter_lag}")
        await asyncio.sleep(self.shutter_lag / 1000)
        GPIO.output(self.pin, GPIO.LOW)  # rpi0 led is inverted
        logger.info(f"<- LedOutputDevice Shutter {self.shutter_lag}")
        self.can_release = True

    async def release(self) -> None:
        while not self.can_release:
            await asyncio.sleep(0.01)
        logger.info(f"-> LedOutputDevice Release {self.release_lag}")
        await asyncio.sleep(self.release_lag / 1000)
        GPIO.output(self.pin, GPIO.HIGH)  # rpi0 led is inverted
        logger.info(f"<- LedOutputDevice Release {self.release_lag}")


# class PinOutputDevice(OutputDevice):
#     def __init__(self, activateDelay: int, deactivateDelay: int, enabled: bool, pin: int):
#         super().__init__(activateDelay, deactivateDelay, enabled)
#         self.pin = pin
#         GPIO.setup(self.pin, GPIO.OUT)

#     def tick(self, trigger: bool) -> None:
#         if self.enabled and trigger and not self.activateTimer.active() and not self.active:
#             self.activateTimer.setTimerMode()
#             self.activateTimer.setTime(self.activateDelay)
#             self.activateTimer.start()

#         if self.activateTimer.tick() and self.enabled:
#             self.active = True
#             GPIO.output(self.pin, GPIO.HIGH)

#             self.deactivateTimer.setTimerMode()
#             self.deactivateTimer.setTime(self.deactivateDelay)
#             self.deactivateTimer.start()

#         if self.enabled and self.active and trigger:
#             self.deactivateTimer.setTimerMode()
#             self.deactivateTimer.setTime(self.deactivateDelay)
#             self.deactivateTimer.start()

#         if self.active and self.deactivateTimer.tick():
#             GPIO.output(self.pin, GPIO.LOW)
#             self.active = False
#             self.activateTimer.stop()
#             self.deactivateTimer.stop()


# class OledOutputDevice(OutputDevice):
#     def __init__(self, activateDelay: int, deactivateDelay: int, enabled: bool, oled: LumaDevice):
#         super().__init__(activateDelay, deactivateDelay, enabled)
#         self.screen = oled

#     def tick(self, trigger: bool) -> None:
#         if self.enabled and trigger and not self.activateTimer.active() and not self.active:
#             self.activateTimer.setTimerMode()
#             self.activateTimer.setTime(self.activateDelay)
#             self.activateTimer.start()

#         if self.activateTimer.tick() and self.enabled:
#             self.active = True
#             self.screen.invertDisplay(True)  # TODO
#             self.screen.update()
#             self.deactivateTimer.setTimerMode()
#             self.deactivateTimer.setTime(self.deactivateDelay)
#             self.deactivateTimer.start()

#         if self.enabled and self.active and trigger:
#             self.deactivateTimer.setTimerMode()
#             self.deactivateTimer.setTime(self.deactivateDelay)
#             self.deactivateTimer.start()

#         if self.active and self.deactivateTimer.tick():
#             self.screen.invertDisplay(False)  # TODO
#             self.screen.update()
#             self.active = False
#             self.activateTimer.stop()
#             self.deactivateTimer.stop()
