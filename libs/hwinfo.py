import asyncio
import contextlib
import logging
import struct
import subprocess

import psutil
import RPi.GPIO as GPIO
import smbus

from libs.eventbus import EventBusDefaultDict
from libs.eventtypes import HWInfoUpdateEvent
from menu.data import Config

logger = logging.getLogger(__name__)


def read_voltage(address: int, bus: smbus.SMBus) -> float:
    "This function returns as float the voltage from the Raspi UPS Hat via the provided SMBus object"
    read: int = bus.read_word_data(address, 0x02)
    swapped: int = struct.unpack("<H", struct.pack(">H", read))[0]
    return swapped * 1.25 / 1000 / 16


def readCapacity(address: int, bus: smbus.SMBus) -> float:
    "This function returns as a float the remaining capacity of the battery connected to the Raspi UPS Hat via the provided SMBus object"
    read: int = bus.read_word_data(address, 0x04)
    swapped: int = struct.unpack("<H", struct.pack(">H", read))[0]
    return swapped / 256


def quick_start(address: int, bus: smbus.SMBus) -> None:
    bus.write_word_data(address, 0x06, 0x4000)


def power_on_reset(address: int, bus: smbus.SMBus) -> None:
    bus.write_word_data(address, 0xFE, 0x0054)


def get_ip() -> str:
    arg = "ip route list"
    p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
    data = p.communicate()
    split_data = data[0].decode().split()
    return split_data[split_data.index("src") + 1]


class HWInfo:
    __cpu = 0
    __memory = 0
    __voltage = 0.0
    __capacity = 0
    __temperature = 0
    __ip = ""
    __is_charging = 0
    __changed = False
    __ups_address = 0x32

    def __init__(self, config: Config) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(4, GPIO.IN)
        self.config = config
        self.bus = EventBusDefaultDict()
        self.smbus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
        power_on_reset(self.__ups_address, self.smbus)
        quick_start(self.__ups_address, self.smbus)

    @property
    def cpu(self) -> int:
        return self.__cpu

    @cpu.setter
    def cpu(self, value: int) -> None:
        if self.__cpu != value:
            self.__changed = True
        self.__cpu = value

    @property
    def memory(self) -> int:
        return self.__memory

    @memory.setter
    def memory(self, value: int) -> None:
        if self.__memory != value:
            self.__changed = True
        self.__memory = value

    @property
    def voltage(self) -> float:
        return self.__voltage

    @voltage.setter
    def voltage(self, value: float) -> None:
        if self.__voltage != value:
            self.__changed = True
        self.__voltage = value

    @property
    def capacity(self) -> int:
        return self.__capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        if self.__capacity != value:
            self.__changed = True
        self.__capacity = value

    @property
    def temperature(self) -> int:
        return self.__temperature

    @temperature.setter
    def temperature(self, value: int) -> None:
        if self.__temperature != value:
            self.__changed = True
        self.__temperature = value

    @property
    def ip(self) -> str:
        return self.__ip

    @ip.setter
    def ip(self, value: str) -> None:
        if self.__ip != value:
            self.__changed = True
        self.__ip = value

    @property
    def is_charging(self) -> int:
        return self.__is_charging

    @is_charging.setter
    def is_charging(self, value: int) -> None:
        if self.__is_charging != value:
            self.__changed = True
        self.__is_charging = value

    def is_changed(self) -> bool:
        return self.__changed

    async def read_and_reset(self, interval: int) -> None:
        while True:
            await asyncio.sleep(interval / 1000)
            if not self.config.hwinfo_enable.value:
                continue

            try:
                self.update()

                if self.is_changed():
                    self.__changed = False
                    self.bus.emit(
                        HWInfoUpdateEvent(
                            cpu=self.cpu,
                            memory=self.memory,
                            voltage=self.voltage,
                            capacity=self.capacity,
                            temperature=self.temperature,
                            ip=self.ip,
                            is_charging=self.is_charging,
                        ),
                        no_log=True,
                    )
            except Exception as e:
                logger.exception(e)

    def update(self) -> None:
        self.cpu = round(psutil.cpu_percent())
        self.memory = round(psutil.virtual_memory().percent)
        self.voltage = read_voltage(self.__ups_address, self.smbus)
        self.capacity = round(readCapacity(self.__ups_address, self.smbus))
        self.is_charging = GPIO.input(4)
        with contextlib.suppress(Exception):
            s = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
            self.temperature = round(float(s.split("=")[1][:-3]))
            self.ip = get_ip()
