from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Event:
    pass


@dataclass(frozen=True)
class ButtonPressEvent(Event):
    pin: int


@dataclass(frozen=True)
class ButtonClickEvent(Event):
    pin: int
    steps_count: int
    hold_time: int


@dataclass(frozen=True)
class ButtonStepEvent(Event):
    pin: int
    steps_count: int


@dataclass(frozen=True)
class ButtonHoldEvent(Event):
    pin: int
    hold_time: int


@dataclass(frozen=True)
class MenuRotateEvent(Event):
    direction: int


@dataclass(frozen=True)
class MenuClickEvent(Event):
    pass


@dataclass(frozen=True)
class ConfigChangeEvent(Event):
    key: str
    param_type: Any
    new_value: Any


@dataclass(frozen=True)
class MenuHoldEvent(Event):
    pass


@dataclass(frozen=True)
class HWInfoUpdateEvent(Event):
    cpu: int
    memory: int
    voltage: float
    capacity: int
    temperature: int
    ip: str
    is_charging: int
