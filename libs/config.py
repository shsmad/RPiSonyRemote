import logging

from enum import Enum
from typing import Any, Generic, Optional, TypeVar, cast

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


T = TypeVar("T")


class ConfigItem(Generic[T]):
    def __init__(self, title: str, param_type: ParamType, default_value: T, icon: Optional[str] = None) -> None:
        self.key: Optional[str] = None
        self.title = title
        self.param_type = param_type
        self.default_value = default_value
        self.icon = icon
        self.storage: Any = None
        self.bus = EventBusDefaultDict()  # noqa: F821

    @property
    def value(self) -> T:
        try:
            from_db = self.storage.get(self.key)
            if from_db is None:
                return self.default_value

            if self.param_type == ParamType.BOOL:
                return cast(T, bool(from_db))
            elif self.param_type == ParamType.INT:
                return cast(T, int(from_db))
            elif self.param_type == ParamType.FLOAT:
                return cast(T, float(from_db))
            else:
                return cast(T, None)
        except Exception as e:
            logger.exception(e)

        return self.default_value

    @value.setter
    def value(self, new_value: T) -> None:
        if not self.key:
            return

        try:
            if self.param_type == ParamType.BOOL:
                self.storage[self.key] = "1" if new_value else ""
            elif self.param_type in (ParamType.INT, ParamType.FLOAT):
                self.storage[self.key] = str(new_value)

            self.bus.emit(ConfigChangeEvent(key=self.key, param_type=self.param_type, new_value=new_value))
        except Exception as e:
            logger.exception(e)


class DummyConfigItem(ConfigItem[T]):
    def __init__(self, title: str, param_type: ParamType, default_value: T, icon: Optional[str] = None) -> None:
        super().__init__(title, param_type, default_value, icon)

    @property
    def value(self) -> T:
        return self.default_value

    @value.setter
    def value(self, new_value: T) -> None:
        pass


class Config(metaclass=ConfigMeta):
    # inputs
    # analog_trigger_enable = ConfigItem("A.Enable", ParamType.BOOL, False, "wave-sine")
    # analog_trigger_threshold = ConfigItem("A.Barrier", ParamType.INT, 200, "dial")
    # analog_trigger_direction = ConfigItem("A.Above", ParamType.BOOL, False, "arrow-up-from-dotted-line")
    digital_trigger_enable = ConfigItem[bool]("D.Enable", ParamType.BOOL, True, "wave-square")
    digital_trigger_direction = ConfigItem[bool]("D.Above", ParamType.BOOL, True, "arrow-up-from-dotted-line")
    digital_emmitter_enable = ConfigItem[bool]("Emmitter", ParamType.BOOL, False, "signal-stream")

    # outputs
    optron_enable = ConfigItem[bool]("Pin Out", ParamType.BOOL, False, "outlet")
    oled_blink_enable = ConfigItem[bool]("Blink Screen", ParamType.BOOL, False, "display")
    led_timer_enable = ConfigItem[bool]("Screen Timer", ParamType.BOOL, False, "input-numeric")
    led_blink_enable = ConfigItem[bool]("Blink LED", ParamType.BOOL, False, "lightbulb")
    console_enable = ConfigItem[bool]("Console Log", ParamType.BOOL, False, "terminal")
    gphoto_enable = ConfigItem[bool]("USB GPhoto", ParamType.BOOL, False, "plug")

    # timer
    shutter_lag = ConfigItem[int]("Shut.Delay", ParamType.INT, 0, "chess-clock-flip")
    release_lag = ConfigItem[int]("Relz.Delay", ParamType.INT, 60, "chess-clock")
    trigger_read_timer = ConfigItem[int]("ReadTimer", ParamType.INT, 60, "clock")

    # macro
    macro_enable = ConfigItem[bool]("Use Macro", ParamType.BOOL, False, "flower-tulip")
    macro_f = ConfigItem[int]("Aperture", ParamType.INT, 0, "aperture")
    macro_ratio = ConfigItem[float]("Ratio", ParamType.FLOAT, 0, "magnifying-glass")
    macro_step = ConfigItem[float]("Step", ParamType.FLOAT, 0, "shoe-prints")
    macro_start = ConfigItem[float]("Start", ParamType.FLOAT, 0, "backward-step")
    macro_end = ConfigItem[float]("End", ParamType.FLOAT, 0, "forward-step")
    macro_microstep = ConfigItem[float]("Microstep", ParamType.FLOAT, 0, "stairs")
    macro_pitch = ConfigItem[float]("Pitch", ParamType.FLOAT, 0, "reel")
    macro_delay = ConfigItem[float]("Delay", ParamType.FLOAT, 0, "clock")

    # settings
    night_mode = ConfigItem[bool]("Night Mode", ParamType.BOOL, False, "moon")
    hwinfo_enable = ConfigItem[bool]("HWInfo", ParamType.BOOL, False, "microchip")

    # bt
    bt_enable = ConfigItem[bool]("Enable BT", ParamType.BOOL, False, "bluetooth-b")
    bt_bulb = ConfigItem[bool]("BULB mode", ParamType.BOOL, False, "hand-point-down")
    bt_af_enable = ConfigItem[bool]("Enable AF", ParamType.BOOL, False, "users-viewfinder")

    def __init__(self, storage: Any) -> None:
        self.storage = storage
        for item in self.__class__.__dict__.values():
            if isinstance(item, ConfigItem):
                item.storage = self.storage

    def __getattr__(self, name: str) -> Any:
        return DummyConfigItem[bool](title=name, param_type=ParamType.BOOL, default_value=False)
