import asyncio
import logging

from collections import defaultdict
from collections.abc import Coroutine
from typing import Any, Callable

from typing_extensions import Never

from libs.eventtypes import Event
from utils import Singleton

"""
Here's a breakdown of the Coroutine[Any, Any, Any]:

    Any: This is the type of the arguments that the coroutine takes. Any means that the coroutine can take arguments of any type.

    Any: This is the type of the values that the coroutine yields. Any means that the coroutine can yield values of any type.

    Any: This is the type of the value that the coroutine returns. Any means that the coroutine can return a value of any type.
    Never: This is a type hint that indicates that the coroutine will never raise an exception.
"""
logger = logging.getLogger(__name__)


CallbackType = Callable[[Event], Coroutine[Any, Any, Never]]


class EventBusDefaultDict(metaclass=Singleton):
    def __init__(self) -> None:
        self.listeners: defaultdict[type, set[CallbackType]] = defaultdict(set)  # type: ignore

    def add_listener(self, event_type: type, listener: CallbackType) -> None:
        self.listeners[event_type].add(listener)

    def remove_listener(self, event_type: type, listener: CallbackType) -> None:
        self.listeners[event_type].remove(listener)
        if len(self.listeners[event_type]) == 0:
            del self.listeners[event_type]

    def emit(self, event: Event, no_log: bool = False) -> None:
        if not no_log:
            logger.info(f"Event was emited: {event}")
        listeners = self.listeners.get(type(event)) or set()
        for listener in listeners:
            asyncio.create_task(listener(event))
