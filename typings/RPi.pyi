from typing import Any, Callable, Optional

class GPIO:
    BCM = 0
    BOARD = 1
    OUT = 0
    IN = 1
    PUD_UP = 2
    PUD_DOWN = 3
    RISING = 0
    FALLING = 1
    BOTH = 2

    @staticmethod
    def setup(pin: int, direction: int, initial: Optional[int] = None) -> None: ...
    @staticmethod
    def output(pin: int, value: int) -> None: ...
    @staticmethod
    def input(pin: int) -> int: ...
    @staticmethod
    def cleanup(pin: Optional[int]) -> None: ...
    @staticmethod
    def add_event_detect(pin: int, edge: int, callback: Callable[[Any], None], bouncetime: int = 200) -> None: ...
    @staticmethod
    def remove_event_detect(pin: int) -> None: ...
    @staticmethod
    def setwarnings(warn: bool = True) -> None: ...
    @staticmethod
    def setmode(mode: int) -> None: ...
