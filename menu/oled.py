import asyncio

from datetime import datetime
from typing import Any, Callable, Optional, Union

from luma.core.render import canvas
from luma.oled.device import device as LumaDevice
from PIL import ImageFont

from libs.fontawesome import fa
from libs.hwinfo import HWInfo
from libs.timer import TimerMs
from utils import circular_increment

from .data import MenuItem, ParamType, create_menu_tree

FONTS = {x: ImageFont.truetype("fonts/better-vcr-5.2.ttf", x) for x in range(4, 33, 2)}


async def process_timer(interval: int, callback: Callable[[], None]) -> None:
    """
    Run a timer that calls a callback function repeatedly at a given interval.

    Args:
        interval (int): The interval in milliseconds.
        callback (Callable[[], None]): The callback function to be called.

    Returns:
        None
    """
    while True:
        await asyncio.sleep(interval / 1000)
        callback()


class OledMenu:
    _current_menu_position = [0, 0, 0]
    _edit_precision = 0
    # AnalogInputDevice *ameter;
    _t_reset_to_splashscreen: Optional[asyncio.Task] = None
    _t_update_hwinfo: Optional[asyncio.Task] = None

    def __init__(
        self,
        ameter: Any,  # Replace Any with the appropriate type
        oled: LumaDevice,
        settingsstorage: Any,  # Replace Any with the appropriate type
        reset_to_splash_timeout: int = 3000,
    ) -> None:
        """
        Initialize MyClass.

        Args:
            ameter: The ameter object.
            oled: The LumaDevice object.
            reset_to_splash_timeout: The timeout for resetting to splash screen.
            settingsstorage: The settings storage object.
        """
        self._reset_to_splash_timeout = reset_to_splash_timeout
        self._refreshTimer = TimerMs(500, start=True, run_once=False)
        self.ameter = ameter
        self.settingsstorage = settingsstorage
        self.menuLevel = 0

        self.menuItems = create_menu_tree(storage=self.settingsstorage)
        self._oled = oled
        self.draw = canvas(self._oled)
        self.hwinfo = HWInfo()

    def init(self) -> None:
        """
        Initializes the object and draws the splash screen.
        """
        self.draw_splash_screen()

    def update_hwinfo(self) -> None:
        """
        Update the hardware info.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        self.hwinfo.update()
        if self.hwinfo.is_changed() and self.menuLevel == 0:
            data = self.hwinfo.read_and_reset()

            try:
                with self.draw as draw:
                    draw.rectangle((0, 47, self._oled.width, self._oled.height), outline="black", fill="black")
                    draw.text(
                        (0, 48),
                        f"C{data['cpu']:2d} M{data['memory']:2d} V{data['voltage']:3.1f} {data['capacity']:2d}% {data['temperature']:2d}℃",
                        font=FONTS[8],
                        fill=255,
                    )
                    draw.text((0, 57), data["ip"], font=FONTS[8], fill=255)
            except Exception as e:
                print(e)

        self._hwinfo_timer_stop()
        self._hwinfo_timer_start()

    def _hwinfo_timer_start(self) -> None:
        """
        Start the hardware info timer.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        if self._t_update_hwinfo:
            self._t_update_hwinfo.cancel()

        self._t_update_hwinfo = asyncio.create_task(process_timer(100, self.update_hwinfo))

    def _hwinfo_timer_stop(self) -> None:
        """
        Stop the hardware info timer.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        if self._t_update_hwinfo:
            self._t_update_hwinfo.cancel()
            self._t_update_hwinfo = None

    def _splashscreen_timer_start(self) -> None:
        """
        Start the splashscreen timer.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        if self._t_reset_to_splashscreen:
            self._t_reset_to_splashscreen.cancel()

        self._t_reset_to_splashscreen = asyncio.create_task(
            process_timer(self._reset_to_splash_timeout, self.reset_to_splashscreen)
        )

    def _splashscreen_timer_stop(self) -> None:
        """
        Stop the splash screen timer.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        if self._t_reset_to_splashscreen:
            self._t_reset_to_splashscreen.cancel()
            self._t_reset_to_splashscreen = None

    def draw_splash_screen(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        with self.draw as draw:
            draw.rectangle(self._oled.bounding_box, outline="black", fill="black")
            draw.text((0, 1), f"RPiRemote {now}", fill="white", font=FONTS[8])

            for idx, i in enumerate(self._current_menu_position):
                draw.text((idx * 16, 16), f"{i}", fill="white", font=FONTS[12])

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

    def draw_menu_screen(self, position: int) -> None:
        with self.draw as draw:
            draw.rectangle(self._oled.bounding_box, outline="black", fill="black")
            font_16 = FONTS[16]
            margin_x = (self._oled.width - font_16.getlength(self.menuItems[position].title)) / 2
            draw.text(
                (margin_x, 1),
                self.menuItems[position].title,
                fill="white",
                font=font_16,
            )

            padding_x = (self._oled.width - len(self.menuItems) * 24) / 2
            icon_items = [(idx, item) for idx, item in enumerate(self.menuItems) if item.icon]

            for idx, item in icon_items:
                text, font = fa(item.icon, 16)
                draw.text((idx * 24 + padding_x + 6, 32 + 4), text, fill="white", font=font)

                if idx == position:
                    draw.rounded_rectangle(
                        (
                            idx * 24 + padding_x,
                            32,
                            idx * 24 + 24 + padding_x,
                            32 + 24 - 1,
                        ),
                        radius=4,
                        outline="white",
                    )

    def draw_submenu_screen(self, parent_position: int, position: int) -> None:
        current_item = self.menuItems[parent_position].children[position]

        with canvas(self._oled) as draw:
            draw.rectangle(self._oled.bounding_box, outline="black", fill="black")

            font_16 = FONTS[16]
            draw.text((0, 0), current_item.title, fill="white", font=font_16)

            if current_item.type == ParamType.EXIT:
                return

            if current_item.type == ParamType.BOOL:
                text = "True" if current_item.value else "False"

            if current_item.type == ParamType.INT:
                text = str(current_item.value)

            if current_item.type == ParamType.FLOAT:
                text = f"{current_item.value:.2f}"

            x = self._oled.width - font_16.getlength(text)
            draw.text((x, 48), text, fill="white", font=font_16)

    async def tick(self) -> None:
        # print("oled tick")
        self._hwinfo_timer_start()
        # if not self._refreshTimer.tick():
        #     return

        # if self._resetToSplashScreenTimer.ready() or ((self.menuLevel == 0) and ameter->isEnabled() && ameter->isChanged()))
        # {
        #    self._resetToSplashScreenTimer.stop()
        #    self.menuLevel = 0
        #    self.drawSplashScreen()
        # };

    def reset_to_splashscreen(self) -> None:
        self._splashscreen_timer_stop()
        self.menuLevel = 0
        self.draw_splash_screen()

    def onKeyClick(self) -> None:
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
            self._splashscreen_timer_stop()
            self._current_menu_position[self.menuLevel] = 0
            self.draw_submenu_screen(
                self._current_menu_position[self.menuLevel - 1],
                self._current_menu_position[self.menuLevel],
            )
            return

        if self.menuLevel == 2:
            current_item = self.menuItems[self._current_menu_position[self.menuLevel - 1]].children[
                self._current_menu_position[self.menuLevel]
            ]

            if current_item.type == ParamType.EXIT:
                self.menuLevel = 1
                self.draw_menu_screen(self._current_menu_position[self.menuLevel])
                self._splashscreen_timer_start()
                return

            if current_item.type in (ParamType.BOOL, ParamType.INT, ParamType.FLOAT):
                self._edit_precision = 0
                self.menuLevel = 3
                draw_item_editor(self._oled, current_item, self._edit_precision)
                return

        if self.menuLevel == 3:
            self.menuLevel = 2
            self.draw_submenu_screen(
                self._current_menu_position[self.menuLevel - 1],
                self._current_menu_position[self.menuLevel],
            )
            return

    def on_key_press_splashscreen(self) -> None:
        self.menuLevel = 1
        self.draw_menu_screen(self._current_menu_position[self.menuLevel])
        self._splashscreen_timer_start()

    def onKeyClickAfterHold(self, pin: int, steps: int, hold: int) -> None:
        if self.menuLevel == 3:
            self._edit_precision = circular_increment(self._edit_precision, 0, 2, 1)
            try:
                current_item = self.menuItems[self._current_menu_position[self.menuLevel - 2]].children[
                    self._current_menu_position[self.menuLevel - 1]
                ]
                if current_item.type in (
                    ParamType.BOOL,
                    ParamType.INT,
                    ParamType.FLOAT,
                ):
                    draw_item_editor(self._oled, current_item, self._edit_precision)
            except Exception as e:
                print(e)

    def onRotate(self, direction: int, counter: int, fast: bool) -> None:
        menu_length = 0
        if self.menuLevel == 1:
            menu_length = len(self.menuItems) - 1
        elif self.menuLevel == 2:
            parent_menu_item = self.menuItems[self._current_menu_position[self.menuLevel - 1]]
            menu_length = len(parent_menu_item.children) - 1

        if self.menuLevel < 3:
            self._current_menu_position[self.menuLevel] = circular_increment(
                self._current_menu_position[self.menuLevel],
                0,
                menu_length,
                direction * (10 if fast else 1),
            )
        if self.menuLevel == 3:
            current_item = self.menuItems[self._current_menu_position[self.menuLevel - 2]].children[
                self._current_menu_position[self.menuLevel - 1]
            ]

            if current_item.type == ParamType.EXIT:
                return

            if current_item.type == ParamType.BOOL:
                print(f"Here we rotate {current_item.title}")
                current_item.value = not current_item.value
                draw_item_editor(self._oled, current_item, 0)
                return

            delta: Union[int, float] = 0

            if current_item.type == ParamType.INT:
                delta = int_delta(direction, self._edit_precision)
                current_item.value = current_item.value + delta
                draw_item_editor(self._oled, current_item, self._edit_precision)
                return

            if current_item.type == ParamType.FLOAT:
                delta = float_delta(direction, self._edit_precision)
                current_item.value = current_item.value + delta
                draw_item_editor(self._oled, current_item, self._edit_precision)
                return

        if self.menuLevel == 1:
            self.draw_menu_screen(self._current_menu_position[self.menuLevel])
            self._splashscreen_timer_start()
            return

        if self.menuLevel == 2:
            self.draw_submenu_screen(
                parent_position=self._current_menu_position[self.menuLevel - 1],
                position=self._current_menu_position[self.menuLevel],
            )
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

        draw.text((0, 0), item.title, fill="white", font=font_16)

        if item.type == ParamType.BOOL:
            text = "True" if item.value else "False"

        if item.type == ParamType.INT:
            text = str(item.value)

        if item.type == ParamType.FLOAT:
            text = f"{item.value:.2f}"

        x = screen.width - font_16.getlength(text)
        letter_width = font_16.getlength("0")
        draw.rectangle(
            [(x, 48), (screen.width - letter_width * precision, 63)],
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
                (screen.width - letter_width * precision, 48),
                rest_part,
                fill="white",
                font=font_16,
            )
