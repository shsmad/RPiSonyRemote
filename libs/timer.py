"""
    Многофункциональный программный таймер на системном таймере monotonic_ns()

    Переписано с версии для Arduino https://github.com/GyverLibs/TimerMs

    Возможности:
    - Режим таймера и периодичного выполнения
    - Подключение функции-обработчика
    - Сброс/запуск/перезапуск/остановка/пауза/продолжение отсчёта
    - Возможность форсировать переполнение таймера
    - Возврат оставшегося времени в мс и нс
    - Несколько функций получения текущего статуса таймера
    - Алгоритм держит стабильный период и не боится переполнения
"""

from time import monotonic_ns
from typing import Callable, Optional


class TimerMs:
    _started_at: int = 0
    _prd: int = 1000
    _passed_delta: int = 0
    _is_running: bool = False
    _run_once: bool = False
    _ready: bool = False

    _handler: Optional[Callable] = None

    def __init__(self, prd_ms: int = 1000, start: bool = False, run_once: bool = False):
        """Initialize the TimerMs object.

        Args:
            prd_ms (int): The period of the timer in milliseconds. Default is 1000.
            start (bool): Whether to start the timer immediately. Default is False.
            run_once (bool): Whether the timer should run only once. Default is False.
        """

        self.set_time(prd_ms)
        if start:
            self.start()
        self._run_once = run_once

    def set_timer_mode(self):
        """Set the timer to run only once."""

        self._run_once = True

    def set_period_mode(self):
        """Set the timer to run periodically."""

        self._run_once = False

    # установить время
    def set_time(self, prd_ms: int):
        """Set the time period of the timer.

        Args:
            prd_ms (int): The period of the timer in milliseconds.

        """

        self._prd = prd_ms or 1

    def attach(self, handler: Callable):
        """Attach a callback function to the timer.

        Args:
            handler (Callable): The callback function to attach.

        """

        self._handler = handler

    def detach(self):
        """Detach the callback function from the timer."""

        self._handler = None

    def start(self):
        """Start or restart the timer."""

        self._is_running = True
        self._started_at = self.uptime()
        self._passed_delta = 0

    def restart(self):
        """Restart the timer by calling the start method."""

        self.start()

    def resume(self):
        """Resume the timer after it has been stopped.

        If the timer is not running, the start time is adjusted to account for the time passed during the pause.

        """

        if not self._is_running:
            self._started_at = self.uptime() - self._passed_delta
        self._is_running = True

    def stop(self):
        """Stop or pause the timer.

        If the timer is running, the elapsed time is calculated and stored.

        """

        if self._is_running:
            self._passed_delta = self.uptime() - self._started_at
        self._is_running = False

    def force(self):
        """Forcefully reset the timer.

        The start time is adjusted to simulate the timer reaching its period.

        """

        self._started_at = self.uptime() - self._prd

    def tick(self) -> bool:
        """Check if the timer has reached its period or has elapsed.

        В режиме периода однократно вернёт true при каждом периоде.
        В режиме таймера будет возвращать true при срабатывании.

        Returns:
            bool: True if the timer has reached its period or has elapsed, False otherwise.

        """

        if self._is_running:
            self._passed_delta = self.uptime() - self._started_at

        if self._is_running and self._passed_delta >= self._prd:
            if not self._run_once:
                self._started_at += self._passed_delta - (
                    self._passed_delta % self._prd
                )
            else:
                self.stop()

            if self._handler:
                self._handler()

            self._ready = True
            return True

        return False

    #
    def ready(self) -> bool:
        """Check if the timer has just elapsed.

            Однократно вернёт true при срабатывании (флаг) и сбросит self._ready

        Returns:
            bool: True if the timer has just elapsed, False otherwise.

        """

        if self._ready:
            self._ready = False
            return True
        return False

    def elapsed(self) -> bool:
        """Check if the timer has elapsed.

        Returns:
            bool: True if the timer has elapsed, False otherwise.

        """

        return self.uptime() - self._started_at >= self._prd

    def active(self) -> bool:
        """Check if the timer is running (start/resume).

        Returns:
            bool: True if the timer is running, False otherwise.

        """

        return self._is_running

    def status(self) -> bool:
        """Check if the timer is running and has not elapsed.

        Returns:
            bool: True if the timer is running and has not elapsed, False otherwise.

        """
        return self._is_running and not self.elapsed()

    def time_left(self, as_ns=False) -> int:
        """Get the remaining time of the timer.

        Args:
            as_ns (bool): Whether to return the time left in nanoseconds. Default is False.

        Returns:
            int: The remaining time of the timer in milliseconds, or nanoseconds if as_ns is True.

        """

        left = max(self._prd - self._passed_delta, 0)
        return left if as_ns else left * 1000

    def uptime(self) -> int:
        """Get the current uptime of the timer.

        Returns:
            int: The current uptime of the timer in nanoseconds.

        """

        return monotonic_ns()
