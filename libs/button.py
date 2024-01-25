import asyncio
import time

import RPi.GPIO as GPIO

from libs.eventbus import EventBusDefaultDict
from libs.eventtypes import ButtonClickEvent, ButtonHoldEvent, ButtonPressEvent, ButtonStepEvent, Event
from libs.utils import RepeatTimer

KEY_DOWN = GPIO.LOW  # type: ignore
KEY_UP = GPIO.HIGH  # type: ignore
MS_CONVERSION_FACTOR = 1000000  # constant to convert ns to ms


class Button:
    def __init__(
        self,
        pin: int,
        debounce_time: int = 50,
        hold_time: int = 500,
        click_count_time: int = 500,
        step_count_time: int = 200,
    ):
        self.pin = pin
        self.debounce_time = debounce_time
        self.hold_time = hold_time
        self.click_count_time = click_count_time
        self.step_count_time = step_count_time

        self.state = GPIO.HIGH  # type: ignore
        self.last_change_time = time.monotonic_ns() // MS_CONVERSION_FACTOR  # ms
        self.click_count = 0
        self.steps_count = 0

        self.is_pressed = False

        self.bus = EventBusDefaultDict()

        self.loop = asyncio.get_event_loop()

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # type: ignore
        self.timer = RepeatTimer(0.05, self.tick)

        self.timer.start()

    async def callback(self, event: Event) -> None:
        self.bus.emit(event)

    def _emit_event(self, event: Event) -> None:
        # https://raspberrypi.stackexchange.com/questions/54514/implement-a-gpio-function-with-a-callback-calling-a-asyncio-method
        asyncio.run_coroutine_threadsafe(
            self.callback(event),
            loop=self.loop,
        )

    def tick(self) -> None:
        new_state = GPIO.input(self.pin)  # type: ignore
        old_state = self.state

        if new_state == KEY_UP and old_state == KEY_UP:
            return

        now = time.monotonic_ns() // MS_CONVERSION_FACTOR  # ms

        if now - self.last_change_time < self.debounce_time:
            return

        if new_state != self.state:
            self.state = new_state

            if new_state == KEY_DOWN:
                self.is_pressed = True
                self._emit_event(ButtonPressEvent(self.pin))
            else:
                time_passed = now - self.last_change_time  # ms
                steps_count = time_passed // self.step_count_time
                self.is_pressed = False
                self._emit_event(
                    ButtonClickEvent(
                        pin=self.pin, steps_count=steps_count, hold_time=max(time_passed - self.hold_time, 0)
                    )
                )

            self.last_change_time = now  # ms

        else:
            time_passed = now - self.last_change_time  # ms
            steps_count = time_passed // self.step_count_time

            if steps_count > 0 and steps_count != self.steps_count:
                self.steps_count = steps_count
                self._emit_event(ButtonStepEvent(pin=self.pin, steps_count=steps_count))

            if time_passed > self.hold_time:
                self._emit_event(ButtonHoldEvent(pin=self.pin, hold_time=time_passed - self.hold_time))

    def cleanup(self) -> None:
        GPIO.cleanup(self.pin)  # type: ignore
