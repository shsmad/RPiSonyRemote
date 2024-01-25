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
        config_item: Optional[ConfigItem] = None,
    ):
        self.parent: Optional["MenuItem"] = None
        self.title = title
        self.item_type = item_type
        self.icon = icon
        self.config_item = config_item
        self.children: list["MenuItem"] = []
        self.prev: Optional["MenuItem"] = None
        self.next: Optional["MenuItem"] = None

    def append_child(self, child: "MenuItem") -> None:
        child.parent = self
        if self.children:
            self.children[-1].next = child
            self.children[0].prev = child
            child.prev = self.children[-1]
            child.next = self.children[0]

        self.children.append(child)

    def append_children(self, children: list["MenuItem"]) -> None:
        for child in children:
            self.append_child(child)

    def get_title(self) -> str:
        return (self.config_item.title if self.config_item else self.title) or ""

    def get_icon(self) -> str:
        return (self.config_item.icon if self.config_item else self.icon) or ""

    def get_param_type(self) -> ParamType:
        return (self.config_item.param_type if self.config_item else self.item_type) or ParamType.FOLDER


def create_menu_tree(config: Config) -> MenuItem:
    root = MenuItem(ParamType.FOLDER, "root")

    trigger_folder = MenuItem(ParamType.FOLDER, "Trigger", icon="arrow-right-to-bracket")
    # MenuItem(config_item=config.analog_trigger_enable),
    # MenuItem(config_item=config.analog_trigger_threshold),
    # MenuItem(config_item=config.analog_trigger_direction),
    trigger_folder.append_child(MenuItem(config_item=config.digital_trigger_enable))
    trigger_folder.append_child(MenuItem(config_item=config.digital_trigger_direction))
    trigger_folder.append_child(MenuItem(config_item=config.digital_emmitter_enable))
    trigger_folder.append_child(MenuItem(ParamType.EXIT, "Exit", "arrow-turn-down-left"))

    emitter_folder = MenuItem(ParamType.FOLDER, "Emitter", icon="arrow-right-from-bracket")
    emitter_folder.append_child(MenuItem(config_item=config.optron_enable))
    emitter_folder.append_child(MenuItem(config_item=config.oled_blink_enable))
    emitter_folder.append_child(MenuItem(config_item=config.led_timer_enable))
    emitter_folder.append_child(MenuItem(config_item=config.led_blink_enable))
    emitter_folder.append_child(MenuItem(config_item=config.console_enable))
    emitter_folder.append_child(MenuItem(config_item=config.gphoto_enable))
    emitter_folder.append_child(MenuItem(ParamType.EXIT, "Exit", "arrow-turn-down-left"))

    timer_folder = MenuItem(ParamType.FOLDER, "Timer", icon="stopwatch")
    timer_folder.append_child(MenuItem(config_item=config.shutter_lag))
    timer_folder.append_child(MenuItem(config_item=config.release_lag))
    timer_folder.append_child(MenuItem(config_item=config.trigger_read_timer))
    timer_folder.append_child(MenuItem(ParamType.EXIT, "Exit", "arrow-turn-down-left"))

    macro_folder = MenuItem(ParamType.FOLDER, "Macro", icon="flower-tulip")
    macro_folder.append_child(MenuItem(config_item=config.macro_enable))
    macro_folder.append_child(MenuItem(config_item=config.macro_f))
    macro_folder.append_child(MenuItem(config_item=config.macro_ratio))
    macro_folder.append_child(MenuItem(config_item=config.macro_step))
    macro_folder.append_child(MenuItem(config_item=config.macro_start))
    macro_folder.append_child(MenuItem(config_item=config.macro_end))
    macro_folder.append_child(MenuItem(config_item=config.macro_microstep))
    macro_folder.append_child(MenuItem(config_item=config.macro_pitch))
    macro_folder.append_child(MenuItem(config_item=config.macro_delay))
    macro_folder.append_child(MenuItem(ParamType.EXIT, "Exit", "arrow-turn-down-left"))

    settings_folder = MenuItem(ParamType.FOLDER, "Settings", icon="screwdriver-wrench")
    settings_folder.append_child(MenuItem(config_item=config.night_mode))
    settings_folder.append_child(MenuItem(config_item=config.hwinfo_enable))
    settings_folder.append_child(MenuItem(ParamType.EXIT, "Exit", "arrow-turn-down-left"))

    bluetooth_folder = MenuItem(ParamType.FOLDER, "Bluetooth", icon="bluetooth")
    bluetooth_folder.append_child(MenuItem(config_item=config.bt_enable))
    bluetooth_folder.append_child(MenuItem(config_item=config.bt_bulb))
    bluetooth_folder.append_child(MenuItem(config_item=config.bt_af_enable))
    bluetooth_folder.append_child(MenuItem(ParamType.EXIT, "Exit", "arrow-turn-down-left"))

    root.append_children(
        [trigger_folder, emitter_folder, timer_folder, macro_folder, settings_folder, bluetooth_folder]
    )

    return root
