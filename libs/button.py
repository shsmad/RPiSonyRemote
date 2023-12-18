import asyncio
import time
from math import floor
from threading import Timer

import RPi.GPIO as GPIO


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


KEY_DOWN = 0
KEY_UP = 1


class Button:
    def __init__(
        self,
        pin,
        callback=None,
        debounce_time=50,
        hold_time=500,
        click_count_time=500,
        step_count_time=200,
    ):
        self.pin = pin
        self.callback = callback
        self.debounce_time = debounce_time
        self.hold_time = hold_time
        self.click_count_time = click_count_time
        self.step_count_time = step_count_time

        self.state = GPIO.HIGH
        self.last_change_time = floor(time.monotonic_ns() / 1000000)  # ms
        self.click_count = 0
        self.steps_count = 0

        self.is_pressed = False

        self.loop = asyncio.get_event_loop()
        self.timer = RepeatTimer(0.05, self.tick)

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.timer.start()

    def tick(self):
        new_state = GPIO.input(self.pin)
        old_state = self.state

        if new_state == KEY_UP and old_state == KEY_UP:
            return

        now = floor(time.monotonic_ns() / 1000000)  # ms

        if now - self.last_change_time < self.debounce_time:
            return

        if new_state != self.state:
            self.state = new_state
            self.last_change_time = now  # ms

            if new_state == KEY_DOWN:
                self.is_pressed = True
                if self.callback is not None:
                    asyncio.run_coroutine_threadsafe(
                        self.callback("press", [self.pin]),
                        loop=self.loop,
                    )
            else:
                self.is_pressed = False
                if self.callback is not None:
                    asyncio.run_coroutine_threadsafe(
                        self.callback("click", [self.pin]),
                        loop=self.loop,
                    )

        else:
            time_passed = now - self.last_change_time  # ms
            steps_count = floor(time_passed / self.step_count_time)

            if steps_count > 0 and steps_count != self.steps_count:
                self.steps_count = steps_count
                if self.callback is not None:
                    asyncio.run_coroutine_threadsafe(
                        self.callback("step", [self.pin, steps_count]),
                        loop=self.loop,
                    )

            if time_passed > self.hold_time and self.callback is not None:
                asyncio.run_coroutine_threadsafe(
                    self.callback("hold", [self.pin, time_passed - self.hold_time]),
                    loop=self.loop,
                )

    def cleanup(self):
        GPIO.cleanup(self.pin)
