from typing import Any, Literal

# Constants
OUT: Literal[0]
IN: Literal[1]

LOW: Literal[0]
HIGH: Literal[1]

BOARD: Literal[10]
BCM: Literal[11]

PUD_OFF: Literal[20]
PUD_DOWN: Literal[21]
PUD_UP: Literal[22]

RISING: Literal[31]
FALLING: Literal[32]
BOTH: Literal[33]

HARD_PWM: Literal[43]

SERIAL: Literal[40]
SPI: Literal[41]
I2C: Literal[42]

UNKNOWN: Literal[-1]

RPI_INFO: dict[str, Any]
RPI_REVISION: int
VERSION: str

# Functions
def setmode(mode: int) -> None: ...
def getmode() -> int: ...
def setwarnings(enable: bool) -> None: ...
def setup(channel: int, state: int, initial: int = ..., pull_up_down: int = ...) -> None: ...
def output(channel: int, state: int) -> None: ...
def input(channel: int) -> int: ...
def cleanup(channel: int = ...) -> None: ...
def wait_for_edge(channel: int, edge: int) -> None: ...
def add_event_detect(channel: int, edge: int, callback: Any, bouncetime: int = ...) -> None: ...
def remove_event_detect(channel: int) -> None: ...
def event_detected(channel: int) -> bool: ...
def gpio_function(channel: int) -> int: ...
def add_event_callback(channel: int, callback: Any, bouncetime: int = ...) -> None: ...
def remove_event_callback(channel: int) -> None: ...

# Classes
class PWM:
    def __init__(self, channel: int, frequency: int) -> None: ...
    def start(self, dutycycle: int) -> None: ...
    def ChangeDutyCycle(self, dutycycle: int) -> None: ...
    def ChangeFrequency(self, frequency: int) -> None: ...
    def stop(self) -> None: ...
