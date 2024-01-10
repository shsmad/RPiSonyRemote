import asyncio

from enum import Enum
from threading import Timer
from typing import Any, Callable, Optional, Union


def circular_increment(value: int, minimum: int, maximum: int, increment: int) -> int:
    """
    Increments a value within a circular range.

    Args:
        value (int): The initial value to be incremented.
        minimum (int): The minimum value of the circular range.
        maximum (int): The maximum value of the circular range.
        increment (int): The amount by which the value should be incremented.

    Returns:
        int: The incremented value, wrapped around within the circular range.

    Raises:
        None.
    """

    return (value - minimum + increment) % (maximum - minimum + 1) + minimum


class TextAlign(Enum):
    TA_LEFT = 0
    TA_CENTER = 1
    TA_RIGHT = 2


def get_x_position(max_width: int, align: TextAlign, letter_width: int, value: Union[int, float, str]) -> int:
    """
    Gets the x position of the text.

    Args:
        max_width (int): The maximum width of the text.
        align (TextAlign): The alignment of the text.
        letter_width (int): The width of each letter in the font.
        value (int, float, str): The value to be displayed.

    Returns:
        int: The x position of the text.

    Raises:
        None.
    """

    if align == TextAlign.TA_LEFT:
        return 0

    value_str = ""
    if isinstance(value, str):
        value_str = value
    elif isinstance(value, int):
        value_str = str(value)
    elif isinstance(value, float):
        value_str = f"{value:.2f}"

    if align == TextAlign.TA_CENTER:
        return round((max_width - len(value_str)) * letter_width / 2)

    if align == TextAlign.TA_RIGHT:
        return (max_width - len(value_str)) * letter_width


class Singleton(type):
    _instances: dict[type, Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self not in self._instances:
            # self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)
            self._instances[self] = super().__call__(*args, **kwargs)
        return self._instances[self]


class RepeatTimer(Timer):
    def run(self) -> None:
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class TaskTimer:
    def __init__(self, interval: int, callback: Callable[[], None]) -> None:
        self.interval = interval
        self.callback = callback
        self.task: Optional[asyncio.Task] = None

    async def process_timer(self, interval: int, callback: Callable[[], None]) -> None:
        while True:
            await asyncio.sleep(interval / 1000)
            callback()

    def start(self) -> None:
        if self.task:
            self.task.cancel()

        self.task = asyncio.create_task(self.process_timer(self.interval, self.callback))

    def stop(self) -> None:
        if self.task:
            self.task.cancel()
            self.task = None

    def __repr__(self) -> str:
        return f"TaskTimer(interval={self.interval}, callback={self.callback})"
