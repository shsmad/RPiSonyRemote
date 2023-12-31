import asyncio
import logging

from typing import Optional, Union

import RPi.GPIO as GPIO

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from luma.core.render import canvas as Canvas

from libs.ble.utils import F_ACQUIRED, F_LOST, S_ACTIVE, S_READY, SFD, SFU, SHD, SHU, get_sony_device
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


class PinOutputDevice(OutputDevice):
    def __init__(
        self, pin: int = 29, shutter_lag: int = 0, release_lag: int = 0, enabled: bool = True, inverted: bool = False
    ):
        super().__init__(shutter_lag, release_lag, enabled)
        self.pin = pin
        self.inverted = inverted
        GPIO.setup(pin, GPIO.OUT)

    async def shutter(self) -> None:
        self.can_release = False
        logger.info(f"-> LedOutputDevice Shutter {self.shutter_lag}")
        await asyncio.sleep(self.shutter_lag / 1000)
        GPIO.output(self.pin, GPIO.LOW if self.inverted else GPIO.HIGH)  # rpi0 led is inverted
        logger.info(f"<- LedOutputDevice Shutter {self.shutter_lag}")
        self.can_release = True

    async def release(self) -> None:
        while not self.can_release:
            await asyncio.sleep(0.01)
        logger.info(f"-> LedOutputDevice Release {self.release_lag}")
        await asyncio.sleep(self.release_lag / 1000)
        GPIO.output(self.pin, GPIO.HIGH if self.inverted else GPIO.LOW)  # rpi0 led is inverted
        logger.info(f"<- LedOutputDevice Release {self.release_lag}")


class BluetoothOuputDevice(OutputDevice):
    def __init__(self, shutter_lag: int = 0, release_lag: int = 0, enabled: bool = True):
        super().__init__(shutter_lag, release_lag, enabled)
        self.device: Optional[Union[str, BLEDevice]] = None
        self.client: Optional[BleakClient] = None
        self.command_handle = None
        self.notify_handle = None
        self.af_enabled = False
        self._focus_acquired = False
        self._shutter_active = False

    def notification_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        logger.info("BLE notification_handler %s: %r", characteristic, data)
        if data == F_ACQUIRED:
            self._focus_acquired = True
        if data == S_ACTIVE:
            self._shutter_active = True
        if data == S_READY:
            self._shutter_active = False
        if data == F_LOST:
            self._focus_acquired = False

    async def search(self) -> None:
        logger.debug("BluetoothOuputDevice.search")
        devices = await get_sony_device()
        if len(devices):
            self.client = BleakClient(devices[0][0])
            await self.client.connect()
            logger.debug(f"Connected: {self.client.is_connected}")

            for service in self.client.services:
                print(service.uuid)
                if service.uuid.lower() != "8000FF00-FF00-FFFF-FFFF-FFFFFFFFFFFF".lower():
                    continue

                for char in service.characteristics:
                    if char.uuid.startswith("0000ff01"):
                        self.command_handle = char.handle

                    if char.uuid.startswith("0000ff02"):
                        self.notify_handle = char.handle

        if self.notify_handle:
            await self.client.start_notify(self.notify_handle, self.notification_handler)

    async def shutter(self, bulb_mode: bool = True) -> None:
        if not self.client or not self.command_handle or self._shutter_active:
            return

        self.can_release = False
        await self.client.write_gatt_char(self.command_handle, SHU)
        if self.af_enabled:
            await self.client.write_gatt_char(self.command_handle, SHD)
            while not self._focus_acquired:
                await asyncio.sleep(0.01)

        if self.shutter_lag:
            await asyncio.sleep(self.shutter_lag / 1000)

        await self.client.write_gatt_char(self.command_handle, SFD)
        await self.client.write_gatt_char(self.command_handle, SFU)

        if self.af_enabled:
            while not bulb_mode and self._shutter_active:
                await asyncio.sleep(0.01)
            await self.client.write_gatt_char(self.command_handle, SHU)

        logger.info(f"<- BluetoothOuputDevice Shutter {self.shutter_lag}")
        self.can_release = True

    async def release(self, bulb_mode: bool = True) -> None:
        logger.info(f"-> BluetoothOuputDevice Release {self.release_lag}")
        logger.info(f"\t{bulb_mode} {self._shutter_active}")
        if not self.client or not self.command_handle or not bulb_mode:
            return

        max_limit = 100
        while not self.can_release and not self._shutter_active and max_limit:
            max_limit -= 1
            await asyncio.sleep(0.01)

        logger.info(f"-> BluetoothOuputDevice Release {self.release_lag} {max_limit}")
        await asyncio.sleep(self.release_lag / 1000)
        # in bulb mode to release the shutter you should press button again (see https://github.com/coral/freemote/issues/6)
        await self.client.write_gatt_char(self.command_handle, SFD)
        await self.client.write_gatt_char(self.command_handle, SFU)
        logger.info(f"<- BluetoothOuputDevice Release {self.release_lag}")
