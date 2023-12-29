import contextlib
import os
import struct
import subprocess
import time

from typing import Union

import psutil
import RPi.GPIO as GPIO
import smbus


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
    __changed = False
    __ups_address = 0x32

    def __init__(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(4, GPIO.IN)
        self.bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
        power_on_reset(self.__ups_address, self.bus)
        quick_start(self.__ups_address, self.bus)

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

    def is_changed(self) -> bool:
        return self.__changed

    def read_and_reset(self) -> dict[str, Union[str, float, int]]:
        self.__changed = False
        return {
            "cpu": self.cpu,
            "memory": self.memory,
            "voltage": self.voltage,
            "capacity": self.capacity,
            "temperature": self.temperature,
            "ip": self.ip,
            "is_charging": GPIO.input(4),
        }

    def update(self) -> None:
        self.cpu = round(psutil.cpu_percent())
        self.memory = round(psutil.virtual_memory().percent)
        self.voltage = read_voltage(self.__ups_address, self.bus)
        self.capacity = round(readCapacity(self.__ups_address, self.bus))
        with contextlib.suppress(Exception):
            s = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
            self.temperature = round(float(s.split("=")[1][:-3]))
            self.ip = get_ip()


if __name__ == "__main__":
    hwinfo = HWInfo()
    print("CPU usage %: ", psutil.cpu_percent(), "%")
    print("Mem Usage %:", psutil.virtual_memory().percent, "%")
    print(os.uname())
    while True:
        hwinfo.update()
        time.sleep(0.1)
        if hwinfo.is_changed():
            print(hwinfo.read_and_reset())

# https://github.com/linshuqin329/UPS-Lite/blob/master/UPS-Lite_V1.3_CW2015/UPS_Lite_V1.3_CW2015.py
# vcgencmd measure_temp
