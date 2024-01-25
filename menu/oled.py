import logging

from datetime import datetime
from typing import Any, Union

from luma.core.render import canvas
from luma.oled.device import device as LumaDevice
from PIL import ImageFont

from libs.eventbus import EventBusDefaultDict
from libs.eventtypes import ConfigChangeEvent, HWInfoUpdateEvent, MenuClickEvent, MenuHoldEvent, MenuRotateEvent
from libs.fontawesome import fa

# from libs.hwinfo import HWInfo
from libs.utils import TaskTimer, circular_increment, split_list

from .data import Config, MenuItem, ParamType, create_menu_tree

logger = logging.getLogger(__name__)

FONTS = {x: ImageFont.truetype("fonts/better-vcr-5.2.ttf", x) for x in range(4, 33, 2)}


class OledMenu:
    _current_menu_position = [0, 0, 0]
    _edit_precision = 0
    # AnalogInputDevice *ameter;

    def __init__(
        self,
        ameter: Any,  # Replace Any with the appropriate type
        oled: LumaDevice,
        config: Config,  # Replace Any with the appropriate type
        reset_to_splash_timeout: int = 3000,
    ) -> None:
        """
        Initialize MyClass.

        Args:
            ameter: The ameter object.
            oled: The LumaDevice object.
            reset_to_splash_timeout: The timeout for resetting to splash screen.
            config: The config object.
        """
        self._reset_to_splash_timeout = reset_to_splash_timeout
        self.ameter = ameter
        self.config = config
        self.menuLevel = 0

        self.menu_root = create_menu_tree(config=self.config)
        self.menu_current: MenuItem = self.menu_root
        self.menu_items = None
        self._oled = oled
        self.draw = canvas(self._oled)

        self._t_reset_to_splashscreen = TaskTimer(interval=reset_to_splash_timeout, callback=self.reset_to_splashscreen)

        self.bus = EventBusDefaultDict()
        self.bus.add_listener(MenuRotateEvent, self.on_menu_rotate)
        self.bus.add_listener(MenuClickEvent, self.on_menu_click)
        self.bus.add_listener(MenuHoldEvent, self.on_menu_hold)
        self.bus.add_listener(HWInfoUpdateEvent, self.on_update_hwinfo)
        self.bus.add_listener(ConfigChangeEvent, self.on_config_change)

    def init(self) -> None:
        """
        Initializes the object and draws the splash screen.
        """
        self._oled.contrast(10 if self.config.night_mode.value else 255)
        self.draw_splash_screen()

    async def on_config_change(self, event: ConfigChangeEvent) -> None:
        if event.key == "night_mode":
            self._oled.contrast(10 if event.new_value else 255)

    async def on_update_hwinfo(self, event: HWInfoUpdateEvent) -> None:
        if self.menuLevel != 0:
            return

        try:
            with self.draw as draw:
                draw.rectangle((0, 47, self._oled.width, self._oled.height), outline="black", fill="black")
                charge_sign = "+" if event.is_charging else "-"
                draw.text(
                    (0, 48),
                    f"C{event.cpu:2d} M{event.memory:2d} V{event.voltage:3.1f}{charge_sign}{event.capacity:2d}% {event.temperature:2d}℃",
                    font=FONTS[8],
                    fill=255,
                )
                draw.text((0, 57), event.ip, font=FONTS[8], fill=255)
        except Exception as e:
            logger.exception(e)

    def draw_splash_screen(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        with self.draw as draw:
            draw.rectangle(self._oled.bounding_box, outline="black", fill="black")
            draw.text((0, 1), f"RPiRemote {now}", fill="white", font=FONTS[8])

            if self.config.analog_trigger_enable.value:
                text, font = fa("wave-sine", 8)
                draw.text((64, 16), text, fill="white", font=font)
                text, font = fa(
                    "arrow-up-from-dotted-line"
                    if self.config.analog_trigger_direction.value
                    else "arrow-down-from-dotted-line",
                    8,
                )
                draw.text((64 + 16, 16), text, fill="white", font=font)

            if self.config.digital_trigger_enable.value:
                text, font = fa("wave-square", 8)
                draw.text((64 + 32, 16), text, fill="white", font=font)
                text, font = fa(
                    "arrow-up-from-dotted-line"
                    if self.config.digital_trigger_direction.value
                    else "arrow-down-from-dotted-line",
                    8,
                )
                draw.text((64 + 32 + 16, 16), text, fill="white", font=font)

            if self.config.digital_emmitter_enable.value:
                text, font = fa("signal-stream", 8)
                draw.text((64, 32), text, fill="white", font=font)

            if self.config.optron_enable.value:
                text, font = fa("outlet", 8)
                draw.text((64 + 16, 32), text, fill="white", font=font)
            if self.config.oled_blink_enable.value:
                text, font = fa("display", 8)
                draw.text((64 + 32, 32), text, fill="white", font=font)
            if self.config.bt_enable.value:
                text, font = fa("bluetooth-b", 8)
                draw.text((64 + 32 + 16, 32), text, fill="white", font=font)

        # // if (eesettings->analog_trigger_enable){
        # //     int oledLevel = map(ameter->current(), ameter->minVal(), ameter->maxVal(), 0, 64);
        # //     int oledThreshold = map(*(ameter->threshold), ameter->minVal(), ameter->maxVal(), 0, 64);
        # //     // oled.println(String(oledLevel) + ":" + String(oledThreshold) + " (" + String(ameter->minVal()) + ":" + String(ameter->current()) + ":" + String(ameter->maxVal()) + ")");
        # //     oled.println(String(ameter->current()) + "[" + String(*(ameter->threshold)) + "]");
        # //     oled.setCursor(0, 2);
        # //     oled.fastLineH(31, 0, 64, OLED_STROKE);
        # //     oled.fastLineV(oledThreshold, 16, 23, OLED_STROKE);
        # //     oled.fastLineV(oledLevel, 25, 31, OLED_STROKE);
        # // }

    def draw_menu_screen_ex(self, current_item: MenuItem) -> None:
        with self.draw as draw:
            draw.rectangle(self._oled.bounding_box, outline="black", fill="black")
            font_14 = FONTS[14]
            margin_x = (self._oled.width - font_14.getlength(current_item.get_title())) / 2
            draw.text(
                (margin_x, 1),
                current_item.get_title(),
                fill="white",
                font=font_14,
            )

            padding_x = (self._oled.width - 3 * 24) / 2
            icon_items = [item for item in current_item.parent.children if item.get_icon()]

            icon_items_rows = split_list(icon_items, 3)

            for row_id, row in enumerate(icon_items_rows):
                for item_id, item in enumerate(row):
                    text, font = fa(item.get_icon(), 16)
                    draw.text((item_id * 24 + padding_x + 6, 16 + 4 + 24 * row_id), text, fill="white", font=font)

                    if item is current_item:
                        draw.rounded_rectangle(
                            (
                                item_id * 24 + padding_x,
                                16 + 24 * row_id,
                                item_id * 24 + 24 + padding_x,
                                16 + 24 - 1 + 24 * row_id,
                            ),
                            radius=4,
                            outline="white",
                        )

    def draw_submenu_screen(self, current_item: MenuItem) -> None:
        try:
            with canvas(self._oled) as draw:
                draw.rectangle(self._oled.bounding_box, outline="black", fill="black")

                font_16 = FONTS[16]
                draw.text((0, 0), current_item.get_title(), fill="white", font=font_16)

                if current_item.get_icon():
                    text, font = fa(current_item.get_icon(), 24)
                    draw.text((0, 40), text, fill="white", font=font)

                param_type = current_item.get_param_type()

                if param_type in (ParamType.EXIT, ParamType.FOLDER):
                    return

                if param_type == ParamType.BOOL:
                    text = "True" if current_item.config_item.value else "False"

                if param_type == ParamType.INT:
                    text = str(current_item.config_item.value)

                if param_type == ParamType.FLOAT:
                    text = f"{current_item.config_item.value:.2f}"

                x = self._oled.width - font_16.getlength(text)
                draw.text((x, 48), text, fill="white", font=font_16)
        except Exception as e:
            logger.exception(e)

    def reset_to_splashscreen(self) -> None:
        self._t_reset_to_splashscreen.stop()
        self.menuLevel = 0
        while self.menu_current.parent:
            self.menu_current = self.menu_current.parent
        self.draw_splash_screen()

    async def on_menu_click(self, event: MenuClickEvent) -> None:
        """
        menuLevel:
            0 - splash screen
            1 - trigger/timer/settings/
            2 - submenu
            3 - editor
        """

        if self.menuLevel == 0:
            self.on_key_press_splashscreen()
            return

        if self.menuLevel == 1:
            self.menuLevel = 2
            self._t_reset_to_splashscreen.stop()
            self.menu_current = self.menu_current.children[0]
            self.draw_submenu_screen(self.menu_current)
            return

        if self.menuLevel == 2:
            current_item = self.menu_current

            param_type = current_item.get_param_type()

            if param_type == ParamType.EXIT:
                self.menuLevel = 1
                self.menu_current = self.menu_current.parent
                self.draw_menu_screen_ex(self.menu_current)
                self._t_reset_to_splashscreen.start()
                return

            if param_type in (ParamType.BOOL, ParamType.INT, ParamType.FLOAT):
                self._edit_precision = 0
                self.menuLevel = 3
                draw_item_editor(self._oled, current_item, self._edit_precision)
                return

        if self.menuLevel == 3:
            current_item = self.menu_current
            self.menuLevel = 2
            self.draw_submenu_screen(self.menu_current)
            return

    def on_key_press_splashscreen(self) -> None:
        self.menuLevel = 1
        self.menu_current = self.menu_current.children[0]
        self.draw_menu_screen_ex(self.menu_current)
        self._t_reset_to_splashscreen.start()

    async def on_menu_hold(self, event: MenuHoldEvent) -> None:
        # [pin, steps, hold] = event

        current_item = self.menu_current
        if self.menuLevel == 3 and current_item.get_param_type() in (ParamType.INT, ParamType.FLOAT):
            self._edit_precision = circular_increment(self._edit_precision, 0, 2, 1)
            try:
                if current_item.get_param_type() in (
                    ParamType.BOOL,
                    ParamType.INT,
                    ParamType.FLOAT,
                ):
                    draw_item_editor(self._oled, current_item, self._edit_precision)
            except Exception as e:
                logger.exception(e)

    async def on_menu_rotate(self, event: MenuRotateEvent) -> None:
        if self.menuLevel == 3:
            current_item = self.menu_current

            param_type = current_item.get_param_type()

            if param_type == ParamType.EXIT:
                return

            if param_type == ParamType.BOOL:
                logger.info(f"Here we rotate {current_item.get_title()} with {current_item.config_item.value}")
                current_item.config_item.value = not current_item.config_item.value
                draw_item_editor(self._oled, current_item, 0)
                return

            delta: Union[int, float] = 0

            if param_type == ParamType.INT:
                delta = int_delta(event.direction, self._edit_precision)
                try:
                    current_item.config_item.value = current_item.config_item.value + delta
                except Exception as e:
                    logger.exception(e)
                draw_item_editor(self._oled, current_item, self._edit_precision)
                return

            if param_type == ParamType.FLOAT:
                delta = float_delta(event.direction, self._edit_precision)
                current_item.config_item.value = current_item.config_item.value + delta
                draw_item_editor(self._oled, current_item, self._edit_precision)
                return

        if self.menuLevel == 1:
            self.menu_current = self.menu_current.next if event.direction == 1 else self.menu_current.prev
            self.draw_menu_screen_ex(self.menu_current)
            self._t_reset_to_splashscreen.start()
            return

        if self.menuLevel == 2:
            self.menu_current = self.menu_current.next if event.direction == 1 else self.menu_current.prev
            self.draw_submenu_screen(self.menu_current)
            return


def int_delta(value: int, precision: int) -> int:
    fix_multiply = [1, 10, 100]
    if 0 <= precision < len(fix_multiply):
        return value * fix_multiply[precision]
    return value


def float_delta(value: int, precision: int) -> float:
    fix_multiply = [0.01, 0.1, 1]
    if 0 <= precision < len(fix_multiply):
        return value * fix_multiply[precision]
    return value


def draw_item_editor(screen: LumaDevice, item: MenuItem, precision: int = 0) -> None:
    with canvas(screen) as draw:
        font_16 = FONTS[16]
        draw.rectangle(screen.bounding_box, outline="black", fill="black")

        draw.text((0, 0), item.get_title(), fill="white", font=font_16)

        param_type = item.get_param_type()

        if param_type == ParamType.BOOL:
            text = "True" if item.config_item.value else "False"

        if param_type == ParamType.INT:
            text = str(item.config_item.value)

        if param_type == ParamType.FLOAT:
            text = f"{item.config_item.value:.2f}"

        x = screen.width - font_16.getlength(text)
        letter_width = font_16.getlength("0")
        draw.rectangle(
            [(min(x, screen.width - letter_width * precision), 48), (screen.width - letter_width * precision, 63)],
            outline="white",
            fill="white",
        )

        if precision:
            selected_part = text[:-precision]
            rest_part = text[-precision:]
        else:
            selected_part = text
            rest_part = None

        draw.text((x, 48), selected_part, fill="black", outline="white", font=font_16)
        if rest_part:
            draw.text(
                (screen.width - letter_width * len(rest_part), 48),
                rest_part,
                fill="white",
                font=font_16,
            )
