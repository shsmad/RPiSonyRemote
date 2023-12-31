import asyncio

from collections import defaultdict
from typing import Any


class EventBusDefaultDict:
    def __init__(self) -> None:
        self.listeners: defaultdict[str, set[Any]] = defaultdict(set)

    def add_listener(self, event_name: str, listener: Any) -> None:
        self.listeners[event_name].add(listener)

    def remove_listener(self, event_name: str, listener: Any) -> None:
        self.listeners[event_name].remove(listener)
        if len(self.listeners[event_name]) == 0:
            del self.listeners[event_name]

    def emit(self, event_name: str, event: Any) -> None:
        listeners = self.listeners.get(event_name) or set()
        for listener in listeners:
            asyncio.create_task(listener(event))


"""
Here's a breakdown of the Coroutine[Any, Any, Any]:

    Any: This is the type of the arguments that the coroutine takes. Any means that the coroutine can take arguments of any type.

    Any: This is the type of the values that the coroutine yields. Any means that the coroutine can yield values of any type.

    Any: This is the type of the value that the coroutine returns. Any means that the coroutine can return a value of any type.
"""
