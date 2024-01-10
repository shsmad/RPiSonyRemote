import logging

from typing import Optional

from libs.config import Config, ConfigItem, ParamType

logger = logging.getLogger(__name__)


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


def create_menu_tree(config: Config) -> list[MenuItem]:
    exit_item = MenuItem(ParamType.EXIT, "Exit", "arrow-turn-down-left")
    return [
        MenuItem(
            ParamType.FOLDER,
            "Trigger",
            icon="bell",
            children=[
                MenuItem(config_item=config.analog_trigger_enable),
                MenuItem(config_item=config.analog_trigger_threshold),
                MenuItem(config_item=config.analog_trigger_direction),
                MenuItem(config_item=config.digital_trigger_enable),
                MenuItem(config_item=config.digital_trigger_direction),
                MenuItem(config_item=config.digital_emmitter_enable),
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
            "Macro",
            icon="flower-tulip",
            children=[
                MenuItem(config_item=config.macro_enable),
                MenuItem(config_item=config.macro_f),
                MenuItem(config_item=config.macro_ratio),
                MenuItem(config_item=config.macro_step),
                MenuItem(config_item=config.macro_start),
                MenuItem(config_item=config.macro_end),
                MenuItem(config_item=config.macro_microstep),
                MenuItem(config_item=config.macro_pitch),
                MenuItem(config_item=config.macro_delay),
                exit_item,
            ],
        ),
        MenuItem(
            ParamType.FOLDER,
            "Settings",
            icon="screwdriver-wrench",
            children=[
                MenuItem(config_item=config.shutter_lag),
                MenuItem(config_item=config.release_lag),
                MenuItem(config_item=config.optron_enable),
                MenuItem(config_item=config.oled_blink_enable),
                MenuItem(config_item=config.led_blink_enable),
                MenuItem(config_item=config.trigger_read_timer),
                MenuItem(config_item=config.night_mode),
                MenuItem(config_item=config.hwinfo_enable),
                exit_item,
            ],
        ),
        MenuItem(
            ParamType.FOLDER,
            "Bluetooth",
            icon="bluetooth",
            children=[
                MenuItem(config_item=config.bt_enable),
                MenuItem(config_item=config.bt_bulb),
                MenuItem(config_item=config.bt_af_enable),
                exit_item,
            ],
        ),
    ]
