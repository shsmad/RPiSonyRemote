import logging

from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ParamType(Enum):
    EXIT = 0
    INT = 1
    FLOAT = 2
    BOOL = 3
    FOLDER = 4


class ConfigItem:
    def __init__(
        self,
        storage: Any,
        key: str,
        title: str,
        param_type: ParamType,
        default_value: Any,
        icon: Optional[str] = None,
    ):
        self.storage = storage
        self.key = key
        self.title = title
        self.param_type = param_type
        self.default_value = default_value
        self.icon = icon

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
    def value(self, v: Any) -> None:
        try:
            if self.param_type == ParamType.BOOL:
                self.storage[self.key] = "1" if v else ""
            elif self.param_type in (ParamType.INT, ParamType.FLOAT):
                self.storage[self.key] = str(v)
            else:
                return
        except Exception as e:
            logger.exception(e)


class Config:
    def __init__(self, storage: Any):
        self.storage = storage
        self.options: dict[str, ConfigItem] = {}

    def add_option(
        self, key: str, title: str, param_type: ParamType, default_value: Any, icon: Optional[str] = None
    ) -> None:
        self.options[key] = ConfigItem(self.storage, key, title, param_type, default_value, icon)

    def get_option(self, key: str) -> ConfigItem:
        return self.options[key]

    def get_value(self, key: str) -> Any:
        return self.options[key].value

    def set_value(self, key: str, value: Any) -> None:
        self.options[key].value = value


class MenuItem:
    def __init__(
        self,
        item_type: Optional[ParamType] = ParamType.FOLDER,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        children: Optional[list["MenuItem"]] = None,
        config_item: Optional[ConfigItem] = None,
    ):
        self.title = title
        self.item_type = item_type
        self.icon = icon
        self.config_item = config_item
        self.children: list[MenuItem] = children or []

    def get_title(self) -> str:
        return (self.config_item.title if self.config_item else self.title) or ""

    def get_icon(self) -> str:
        return (self.config_item.icon if self.config_item else self.icon) or ""

    def get_param_type(self) -> ParamType:
        return (self.config_item.param_type if self.config_item else self.item_type) or ParamType.FOLDER


def get_config(storage: Any) -> Config:
    config = Config(storage)
    config.add_option("analog_trigger_enable", "A.Enable", ParamType.BOOL, False, "wave-sine")
    config.add_option("analog_trigger_threshold", "AThreshold", ParamType.INT, 200, "dial")
    config.add_option("analog_trigger_direction", "A.Above", ParamType.BOOL, False, "arrow-up-from-dotted-line")
    config.add_option("digital_trigger_enable", "D.Enable", ParamType.BOOL, True, "wave-square")
    config.add_option("digital_trigger_direction", "D.Above", ParamType.BOOL, True, "arrow-up-from-dotted-line")
    config.add_option("digital_emmitter_enable", "Emmitter", ParamType.BOOL, False, "signal-stream")

    config.add_option("shutter_lag", "Shut.Delay", ParamType.INT, 0, "chess-clock-flip")
    config.add_option("release_lag", "Relz.Delay", ParamType.INT, 60, "chess-clock")
    config.add_option("optron_enable", "Optron Out", ParamType.BOOL, True, "outlet")
    config.add_option("oled_blink_enable", "Blink Screen", ParamType.BOOL, True, "display")
    config.add_option("led_blink_enable", "Blink LED", ParamType.BOOL, True, "lightbulb")
    config.add_option("trigger_read_timer", "ReadTimer", ParamType.INT, 60, "clock")

    config.add_option("bt_enable", "Enable BT", ParamType.BOOL, False, "bluetooth-b")
    config.add_option("bt_bulb", "BULB mode", ParamType.BOOL, False, "hand-point-down")
    config.add_option("bt_af_enable", "Enable AF", ParamType.BOOL, False, "users-viewfinder")

    return config


def create_menu_tree(config: Config) -> list[MenuItem]:
    exit_item = MenuItem(ParamType.EXIT, "Exit", "arrow-turn-down-left")
    return [
        MenuItem(
            ParamType.FOLDER,
            "Trigger",
            icon="bell",
            children=[
                MenuItem(config_item=config.get_option("analog_trigger_enable")),
                MenuItem(config_item=config.get_option("analog_trigger_threshold")),
                MenuItem(config_item=config.get_option("analog_trigger_direction")),
                MenuItem(config_item=config.get_option("digital_trigger_enable")),
                MenuItem(config_item=config.get_option("digital_trigger_direction")),
                MenuItem(config_item=config.get_option("digital_emmitter_enable")),
                exit_item,
            ],
        ),
        MenuItem(
            ParamType.FOLDER,
            "Timer",
            icon="stopwatch",
            children=[exit_item],
        ),
        MenuItem(
            ParamType.FOLDER,
            "Settings",
            icon="screwdriver-wrench",
            children=[
                MenuItem(config_item=config.get_option("shutter_lag")),
                MenuItem(config_item=config.get_option("release_lag")),
                MenuItem(config_item=config.get_option("optron_enable")),
                MenuItem(config_item=config.get_option("oled_blink_enable")),
                MenuItem(config_item=config.get_option("led_blink_enable")),
                MenuItem(config_item=config.get_option("trigger_read_timer")),
                exit_item,
            ],
        ),
        MenuItem(
            ParamType.FOLDER,
            "Bluetooth",
            icon="bluetooth",
            children=[
                MenuItem(config_item=config.get_option("bt_enable")),
                MenuItem(config_item=config.get_option("bt_bulb")),
                MenuItem(config_item=config.get_option("bt_af_enable")),
                exit_item,
            ],
        ),
    ]
