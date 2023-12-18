import asyncio
import time
from pathlib import Path
from typing import Optional

from luma.core.render import canvas
from luma.oled.device import device as LumaDevice
from PIL import Image, ImageFont

from libs.timer import TimerMs
from utils import circular_increment

from .data import MenuItem, ParamType, create_menu_tree

FONTS = {x: ImageFont.truetype("fonts/better-vcr-5.2.ttf", x) for x in range(4, 33, 2)}


async def process_timer(interval, callback):
    while True:
        await asyncio.sleep(interval / 1000)

        callback()


class OledMenu:
    _current_menu_position = [0, 0, 0]
    _edit_precision = 0
    # AnalogInputDevice *ameter;
    # EESettings * eesettings;
    _sub_menu_size = {7, 1, 6, 2}
    _reset_to_splashscreen_task = None

    def __init__(
        self,
        ameter,
        eesettings,
        reset_to_splash_timeout: Optional[int] = 5000,
        oled: Optional[LumaDevice] = None,
        storage=None,
    ):
        self._reset_to_splash_timeout = reset_to_splash_timeout
        self._refreshTimer = TimerMs(500, start=True, run_once=False)
        self.ameter = ameter
        self.eesettings = eesettings
        self.menuLevel = 0

        self.menuItems = create_menu_tree(storage=storage)
        self._oled = oled

    def init(self):
        self.draw_splash_screen()

    def draw_splash_screen(self):
        now = time.ctime()
        with canvas(self._oled) as draw:
            draw.rectangle(self._oled.bounding_box, outline="black", fill="black")
            draw.text((0, 1), f"RPiRemote {now}", fill="white", font=FONTS[8])

            for idx, i in enumerate(self._current_menu_position):
                draw.text((idx * 16, 16), f"{i}", fill="white", font=FONTS[8])

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

    def draw_menu_screen(self, position: int):
        with canvas(self._oled) as draw:
            draw.rectangle(self._oled.bounding_box, outline="black", fill="black")
            font_8 = FONTS[16]
            margin_x = (
                self._oled.width - font_8.getlength(self.menuItems[position].title)
            ) / 2
            draw.text(
                (margin_x, 1), self.menuItems[position].title, fill="white", font=font_8
            )

            for idx, item in enumerate(self.menuItems):
                if not item.icon:
                    continue

                icon_path = str(
                    Path(__file__)
                    .resolve()
                    .parent.parent.joinpath("images", f"{item.icon}.png")
                )

                padding_x = (self._oled.width - len(self.menuItems) * 24) / 2
                icon = Image.open(icon_path).convert("RGBA")
                draw.bitmap((idx * 24 + padding_x, 32), icon, fill="white")

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

    def draw_submenu_screen(self, parent_position: int, position: int):
        print(f"helo {parent_position} {position}")
        current_item = self.menuItems[parent_position].children[position]
        print(current_item.title, current_item.type)
        try:
            current_item.value
        except Exception as e:
            print(e)
        with canvas(self._oled) as draw:
            draw.rectangle(self._oled.bounding_box, outline="black", fill="black")

            font_8 = FONTS[8]
            draw.text((0, 0), current_item.title, fill="white", font=font_8)

            if current_item.type == ParamType.EXIT:
                return

            if current_item.type == ParamType.BOOL:
                text = "True" if current_item.value else "False"

            if current_item.type == ParamType.INT:
                text = str(current_item.value)

            if current_item.type == ParamType.FLOAT:
                text = "{:.2f}".format(current_item.value)

            x = self._oled.width - font_8.getlength(text)
            draw.text((x, 16), text, fill="white", font=font_8)

    def tick(self):
        if not self._refreshTimer.tick():
            return

        # if self._resetToSplashScreenTimer.ready() or ((self.menuLevel == 0) and ameter->isEnabled() && ameter->isChanged()))
        # {
        #    self._resetToSplashScreenTimer.stop()
        #    self.menuLevel = 0
        #    self.drawSplashScreen()
        # };

    def reset_to_splashscreen(self):
        self.menuLevel = 0
        self.draw_splash_screen()

    def onKeyClick(self):
        """
        menuLevel:
            0 - splash screen
            1 - trigger/timer/settings/
            2 - submenu
            3 - editor
        """

        print(f"onKeyClick {self.menuLevel}")

        if self.menuLevel == 0:
            self.menuLevel = 1
            self.draw_menu_screen(self._current_menu_position[self.menuLevel])
            self._reset_to_splashscreen_task = asyncio.create_task(  # TODO: rewrite to function which checks and cancel first
                process_timer(self._reset_to_splash_timeout, self.reset_to_splashscreen)
            )
            return

        if self.menuLevel == 1:
            self.menuLevel = 2
            if self._reset_to_splashscreen_task:
                self._reset_to_splashscreen_task.cancel()
            self._current_menu_position[self.menuLevel] = 0
            self.draw_submenu_screen(
                self._current_menu_position[self.menuLevel - 1],
                self._current_menu_position[self.menuLevel],
            )
            return

        if self.menuLevel == 2:
            current_item = self.menuItems[
                self._current_menu_position[self.menuLevel - 1]
            ][self._current_menu_position[self.menuLevel]]

            if current_item.type == ParamType.EXIT:
                self.menuLevel = 1
                self.draw_menu_screen(self._current_menu_position[self.menuLevel])
                self._reset_to_splashscreen_task = asyncio.create_task(
                    process_timer(
                        self._reset_to_splash_timeout, self.reset_to_splashscreen
                    )
                )
                return

            if current_item.type in (ParamType.BOOL, ParamType.INT, ParamType.FLOAT):
                self._edit_precision = 0
                self.menuLevel = 3
                drawItemEditor(self._oled, current_item, self._edit_precision)
                return

        if self.menuLevel == 3:
            self.menuLevel = 2
            self.draw_submenu_screen(
                self.currentMenuPosition[self.menuLevel - 1],
                self.currentMenuPosition[self.menuLevel],
            )
            return

    def onKeyHeld(self):
        if self.menuLevel == 3:
            self._edit_precision = circular_increment(self._edit_precision, 0, 2, 1)
            with canvas(self._oled) as draw:
                draw.line(
                    [
                        (self._oled.width - 12 * self._edit_precision - 8, 31),
                        (self._oled.width, 31),
                    ],
                    fill="black",
                )
                draw.line(
                    [(0, 31), (self._oled.width - 12 * self._edit_precision - 8, 31)],
                    fill="white",
                )

    def onRotate(self, direction: int, counter: int, fast: bool):
        menu_length = 0
        if self.menuLevel == 1:
            menu_length = len(self.menuItems) - 1
        elif self.menuLevel == 2:
            menu_length = (
                self._sub_menu_size[self._current_menu_position[self.menuLevel - 1]] - 1
            )
            # menu_length = len(self.menuItems[self.currentMenuPosition[1]]) - 1

        if self.menuLevel < 3:
            self._current_menu_position[self.menuLevel] = circular_increment(
                self._current_menu_position[self.menuLevel],
                0,
                menu_length,
                direction * (10 if fast else 1),
            )
        if self.menuLevel == 3:
            current_item = self.menuItems[
                self._current_menu_position[self.menuLevel - 2]
            ][self._current_menu_position[self.menuLevel - 1]]

            if current_item.type == ParamType.EXIT:
                return

            if current_item.type == ParamType.BOOL:
                print(f"Here we rotate {current_item.title}")
                current_item.value = not current_item.value
                drawItemEditor(self._oled, current_item, 0)
                return

            if current_item.type == ParamType.INT:
                int_delta = 1
                if self._edit_precision == 0:
                    int_delta = direction
                elif self._edit_precision == 1:
                    int_delta = direction * 10
                elif self._edit_precision == 2:
                    int_delta = direction * 100

                current_item.value = current_item.value + int_delta
                drawItemEditor(self._oled, current_item, self._edit_precision)
                return

            if current_item.type == ParamType.FLOAT:
                delta = 0.0
                if self._edit_precision == 0:
                    delta = direction * 0.01
                elif self._edit_precision == 1:
                    delta = direction * 0.1
                elif self._edit_precision == 2:
                    delta = direction

                current_item.value = current_item.value + delta
                drawItemEditor(self._oled, current_item, self._edit_precision)
                return

        if self.menuLevel == 1:
            self.draw_menu_screen(self._current_menu_position[self.menuLevel])
            self._reset_to_splashscreen_task = asyncio.create_task(
                process_timer(self._reset_to_splash_timeout, self.reset_to_splashscreen)
            )
            return

        if self.menuLevel == 2:
            self.draw_submenu_screen(
                parent_position=self._current_menu_position[self.menuLevel - 1],
                child_position=self._current_menu_position[self.menuLevel],
            )
            return


def drawItemEditor(screen: LumaDevice, item: MenuItem, precision: int = 0):
    with canvas(screen) as draw:
        font_8 = FONTS[8]
        draw.rectangle(screen.bounding_box, outline="black", fill="black")

        draw.text((0, 0), item.title, fill="white", font=font_8)

        if item.type == ParamType.BOOL:
            text = "True" if item.value else "False"

        if item.type == ParamType.INT:
            text = str(item.value)

        if item.type == ParamType.FLOAT:
            text = "{:.2f}".format(item.value)

        x = screen.width - font_8.getlength(text)
        draw.text((x, 16), text, fill="white", font=font_8)

        draw.line([(0, 31), (screen.width - 12 * precision - 8, 31)], fill="white")
