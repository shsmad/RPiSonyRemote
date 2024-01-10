import logging

from enum import Enum
from typing import Any, Optional

from libs.eventbus import EventBusDefaultDict
from libs.eventtypes import ConfigChangeEvent

logger = logging.getLogger(__name__)


class ParamType(Enum):
    EXIT = 0
    INT = 1
    FLOAT = 2
    BOOL = 3
    FOLDER = 4


class ConfigMeta(type):
    _instances: dict[type, Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self not in self._instances:
            # self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)
            self._instances[self] = super().__call__(*args, **kwargs)
        return self._instances[self]

    def __init__(self, name: str, bases: tuple[type], attrs: dict[str, Any]) -> None:
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, ConfigItem):
                attr_value.key = attr_name


class ConfigItem:
    def __init__(self, title: str, param_type: ParamType, default_value: Any, icon: Optional[str] = None) -> None:
        self.key: Optional[str] = None
        self.title = title
        self.param_type = param_type
        self.default_value = default_value
        self.icon = icon
        self.storage: Any = None
        self.bus = EventBusDefaultDict()  # noqa: F821

    @property
    def value(self) -> Any:
        try:
            from_db = self.storage.get(self.key)
            if from_db is None:
                return self.default_value

            if self.param_type == ParamType.BOOL:
                return bool(from_db)
            elif self.param_type == ParamType.INT:
                return int(from_db)
            elif self.param_type == ParamType.FLOAT:
                return float(from_db)
            else:
                return None
        except Exception as e:
            logger.exception(e)

        return self.storage.get(self.key, self.default_value)

    @value.setter
    def value(self, new_value: Any) -> None:
        try:
            if self.param_type == ParamType.BOOL:
                self.storage[self.key] = "1" if new_value else ""
            elif self.param_type in (ParamType.INT, ParamType.FLOAT):
                self.storage[self.key] = str(new_value)

            self.bus.emit(ConfigChangeEvent(key=self.key, param_type=self.param_type, new_value=new_value))
        except Exception as e:
            logger.exception(e)


class Config(metaclass=ConfigMeta):
    analog_trigger_enable = ConfigItem("A.Enable", ParamType.BOOL, False, "wave-sine")
    analog_trigger_threshold = ConfigItem("A.Barrier", ParamType.INT, 200, "dial")
    analog_trigger_direction = ConfigItem("A.Above", ParamType.BOOL, False, "arrow-up-from-dotted-line")
    digital_trigger_enable = ConfigItem("D.Enable", ParamType.BOOL, True, "wave-square")
    digital_trigger_direction = ConfigItem("D.Above", ParamType.BOOL, True, "arrow-up-from-dotted-line")
    digital_emmitter_enable = ConfigItem("Emmitter", ParamType.BOOL, False, "signal-stream")

    shutter_lag = ConfigItem("Shut.Delay", ParamType.INT, 0, "chess-clock-flip")
    release_lag = ConfigItem("Relz.Delay", ParamType.INT, 60, "chess-clock")
    optron_enable = ConfigItem("Optron Out", ParamType.BOOL, True, "outlet")
    oled_blink_enable = ConfigItem("Blink Screen", ParamType.BOOL, True, "display")
    led_blink_enable = ConfigItem("Blink LED", ParamType.BOOL, True, "lightbulb")
    trigger_read_timer = ConfigItem("ReadTimer", ParamType.INT, 60, "clock")
    night_mode = ConfigItem("Night Mode", ParamType.BOOL, False, "moon")
    hwinfo_enable = ConfigItem("HWInfo", ParamType.BOOL, False, "microchip")
    bt_enable = ConfigItem("Enable BT", ParamType.BOOL, False, "bluetooth-b")
    bt_bulb = ConfigItem("BULB mode", ParamType.BOOL, False, "hand-point-down")
    bt_af_enable = ConfigItem("Enable AF", ParamType.BOOL, False, "users-viewfinder")

    macro_enable = ConfigItem("Use Macro", ParamType.BOOL, False, "flower-tulip")
    macro_f = ConfigItem("Aperture", ParamType.INT, 0, "aperture")
    macro_ratio = ConfigItem("Ratio", ParamType.FLOAT, 0, "magnifying-glass")
    macro_step = ConfigItem("Step", ParamType.FLOAT, 0, "shoe-prints")
    macro_start = ConfigItem("Start", ParamType.FLOAT, 0, "backward-step")
    macro_end = ConfigItem("End", ParamType.FLOAT, 0, "forward-step")
    macro_microstep = ConfigItem("Microstep", ParamType.FLOAT, 0, "stairs")
    macro_pitch = ConfigItem("Pitch", ParamType.FLOAT, 0, "reel")
    macro_delay = ConfigItem("Delay", ParamType.FLOAT, 0, "clock")

    def __init__(self, storage: Any) -> None:
        self.storage = storage
        for item in self.__class__.__dict__.values():
            if isinstance(item, ConfigItem):
                item.storage = self.storage
