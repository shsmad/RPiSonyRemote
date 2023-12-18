from enum import Enum
from typing import Union


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
