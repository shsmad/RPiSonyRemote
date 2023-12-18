from enum import Enum
from math import floor
from time import monotonic_ns
from typing import Callable, Optional

import RPi.GPIO as GPIO


class IEvent(Enum):
    PRESS = 0  # нажатие на кнопку
    HOLD = 1  # кнопка удержана
    STEP = 2  # импульсное удержание
    RELEASE = 3  # кнопка отпущена
    CLICK = 4  # одиночный клик
    CLICKS = 5  # сигнал о нескольких кликах
    TURN = 6  # поворот энкодера
    REL_HOLD = 7  # кнопка отпущена после удержания
    REL_HOLD_C = 8  # кнопка отпущена после удержания с предв. кликами
    REL_STEP = 9  # кнопка отпущена после степа
    REL_STEP_C = 10  # кнопка отпущена после степа с предв. кликами

    # =================== PACK FLAGS ===================


EB_CLKS_R = 1 << 0
EB_PRS_R = 1 << 1
EB_HLD_R = 1 << 2
EB_STP_R = 1 << 3
EB_REL_R = 1 << 4

EB_PRS = 1 << 5
EB_HLD = 1 << 6
EB_STP = 1 << 7
EB_REL = 1 << 8

EB_BUSY = 1 << 9
EB_DEB = 1 << 10
EB_TOUT = 1 << 11
EB_INV = 1 << 12
EB_BOTH = 1 << 13
EB_BISR = 1 << 14

EB_EHLD = 1 << 15


def set_bf(flags: int, x: int):
    return flags | x


def clr_bf(flags: int, x: int):
    return flags & ~x


def read_bf(flags: int, x: int):
    return flags & x


def write_bf(flags: int, x: int, v: bool):
    return set_bf(flags, x) if v else clr_bf(flags, x)


def eq_bf(flags: int, x: int, y: int) -> bool:
    return (flags & x) == y


EB_DEB_TIME = 50  # таймаут гашения дребезга кнопки (кнопка)
EB_CLICK_TIME = 500  # таймаут ожидания кликов (кнопка)
EB_HOLD_TIME = 600  # таймаут удержания (кнопка)
EB_STEP_TIME = 200  # таймаут импульсного удержания (стэпа) (кнопка)
EB_FAST_TIME = 30  # таймаут быстрого поворота (энкодер)


# базовый класс кнопки
class VirtButton:
    def __init__(
        self,
        deb_time: Optional[int] = None,
        click_time: Optional[int] = None,
        hold_time: Optional[int] = None,
        step_time: Optional[int] = None,
        fast_time: Optional[int] = None,
    ):
        self.deb_time = deb_time or EB_DEB_TIME
        self.click_time = click_time or EB_CLICK_TIME
        self.hold_time = hold_time or EB_HOLD_TIME
        self.step_time = step_time or EB_STEP_TIME
        self.fast_time = fast_time or EB_FAST_TIME

        self.flags = 0
        self.clicks = 0
        self.tmr = 0
        self.ftmr = 0
        self.cb = None

    # ====================== SET ======================

    # установить уровень кнопки (HIGH - кнопка замыкает VCC, LOW - замыкает GND)
    def setBtnLevel(self, level: bool):
        self.flags = write_bf(self.flags, EB_INV, not level)

    # кнопка нажата в прерывании (не учитывает btnLevel!)
    def pressISR(self):
        if not read_bf(self.flags, EB_DEB):
            self.tmr = floor(monotonic_ns() / 1000)
        self.flags = set_bf(self.flags, EB_DEB | EB_BISR)

    # сбросить системные флаги (принудительно закончить обработку)
    def reset(self):
        self.clicks = 0
        self.flags = clr_bf(self.flags, ~EB_INV)

    # принудительно сбросить флаги событий
    def clear(self):
        if read_bf(self.flags, EB_CLKS_R):
            self.clicks = 0

        if read_bf(self.flags, EB_CLKS_R | EB_STP_R | EB_PRS_R | EB_HLD_R | EB_REL_R):
            self.flags = clr_bf(
                self.flags, EB_CLKS_R | EB_STP_R | EB_PRS_R | EB_HLD_R | EB_REL_R
            )

    # подключить функцию-обработчик событий (вида void f())
    def attach(self, handler: Callable):
        self.cb = handler

    # отключить функцию-обработчик событий
    def detach(self):
        self.cb = None

    # ====================== GET ======================

    # кнопка нажата [событие]
    def press(self) -> bool:
        return read_bf(self.flags, EB_PRS_R)

    # кнопка отпущена (в любом случае) [событие]
    def release(self) -> bool:
        return eq_bf(self.flags, EB_REL_R | EB_REL, EB_REL_R | EB_REL)

    # клик по кнопке (отпущена без удержания) [событие]
    def click(self) -> bool:
        return eq_bf(self.flags, EB_REL_R | EB_REL | EB_HLD, EB_REL_R)

    # кнопка зажата (между press() и release()) [состояние]
    def pressing(self) -> bool:
        return read_bf(self.flags, EB_PRS)

    # кнопка была удержана (больше таймаута) [событие]
    # кнопка была удержана (больше таймаута) с предварительными кликами [событие]
    def hold(self, num: Optional[int] = None) -> bool:
        if num is None:
            return read_bf(self.flags, EB_HLD_R)

        return self.clicks == num and read_bf(self.flags, EB_HLD_R)

    # кнопка удерживается (больше таймаута) [состояние]
    # кнопка удерживается (больше таймаута) с предварительными кликами [состояние]
    def holding(self, num: Optional[int] = None) -> bool:
        if num is None:
            return eq_bf(self.flags, EB_PRS | EB_HLD, EB_PRS | EB_HLD)

        return self.clicks == num and eq_bf(
            self.flags, EB_PRS | EB_HLD, EB_PRS | EB_HLD
        )

    # импульсное удержание [событие]
    # импульсное удержание с предварительными кликами [событие]
    def step(self, num: Optional[int] = None) -> bool:
        if num is None:
            return read_bf(self.flags, EB_STP_R)

        return self.clicks == num and read_bf(self.flags, EB_STP_R)

    # зафиксировано несколько кликов [событие]
    # зафиксировано указанное количество кликов [событие]
    def hasClicks(self, num: Optional[int] = None) -> bool:
        if num is None:
            return eq_bf(self.flags, EB_CLKS_R | EB_HLD, EB_CLKS_R)

        return self.clicks == num and eq_bf(self.flags, EB_CLKS_R | EB_HLD, EB_CLKS_R)

    # получить количество степов
    def getSteps(self) -> int:
        if self.step_time:
            return (
                (self.stepFor() + self.step_time - 1) / self.step_time
                if self.ftmr
                else 0
            )
        else:
            return 0

    # кнопка отпущена после удержания [событие]
    # кнопка отпущена после удержания с предварительными кликами [событие]
    def releaseHold(self, num: Optional[int] = None) -> bool:
        if num is None:
            return eq_bf(
                self.flags, EB_REL_R | EB_REL | EB_HLD | EB_STP, EB_REL_R | EB_HLD
            )

        return self.clicks == num and eq_bf(
            self.flags, EB_CLKS_R | EB_HLD | EB_STP, EB_CLKS_R | EB_HLD
        )

    # кнопка отпущена после импульсного удержания [событие]
    # кнопка отпущена после импульсного удержания с предварительными кликами [событие]
    def releaseStep(self, num: Optional[int] = None) -> bool:
        if num is None:
            return eq_bf(self.flags, EB_REL_R | EB_REL | EB_STP, EB_REL_R | EB_STP)

        return self.clicks == num and eq_bf(
            self.flags, EB_CLKS_R | EB_STP, EB_CLKS_R | EB_STP
        )

    # кнопка ожидает повторных кликов [состояние]
    def waiting(self) -> bool:
        return self.clicks > 0 and eq_bf(self.flags, EB_PRS | EB_REL, 0)

    # идёт обработка [состояние]
    def busy(self) -> bool:
        return read_bf(self.flags, EB_BUSY)

    #  было действие с кнопки, вернёт код события [событие]
    def action(self) -> int:
        res = self.flags & 0b111111111

        if res == (EB_PRS | EB_PRS_R):
            return IEvent.PRESS

        if res == (EB_PRS | EB_HLD | EB_HLD_R):
            return IEvent.HOLD

        if res == (EB_PRS | EB_HLD | EB_STP | EB_STP_R):
            return IEvent.STEP

        if res in (
            EB_REL | EB_REL_R,
            EB_REL | EB_REL_R | EB_HLD,
            EB_REL | EB_REL_R | EB_HLD | EB_STP,
        ):
            return IEvent.RELEASE

        if res == EB_REL_R:
            return IEvent.CLICK

        if res == EB_CLKS_R:
            return IEvent.CLICKS

        if res == (EB_REL_R | EB_HLD):
            return IEvent.REL_HOLD

        if res == (EB_CLKS_R | EB_HLD):
            return IEvent.REL_HOLD_C

        if res == (EB_REL_R | EB_HLD | EB_STP):
            return IEvent.REL_STEP

        if res == (EB_CLKS_R | EB_HLD | EB_STP):
            return IEvent.REL_STEP_C

        return 0

    # ====================== TIME ======================

    # после взаимодействия с кнопкой (или энкодером EncButton) прошло указанное время, мс [событие]
    def timeout(self, tout: int) -> bool:
        if (
            read_bf(self.flags, EB_TOUT)
            and (floor(monotonic_ns() / 1000) - self.tmr) > tout
        ):
            self.flags = clr_bf(self.flags, EB_TOUT)
            return True

        return False

    # время, которое кнопка удерживается (с начала нажатия), мс
    # кнопка удерживается дольше чем (с начала нажатия), мс [состояние]
    def pressFor(self, ms: Optional[int] = None) -> int:
        if self.ftmr:
            res = floor(monotonic_ns() / 1000) - self.ftmr
            return res > ms if ms is not None else res
        return 0

    # время, которое кнопка удерживается (с начала удержания), мс
    # кнопка удерживается дольше чем (с начала удержания), мс [состояние]
    def holdFor(self, ms: Optional[int] = None) -> int:
        if read_bf(self.flags, EB_HLD):
            res = self.pressFor() - self.hold_time
            return res > ms if ms is not None else res
        return 0

    # время, которое кнопка удерживается (с начала степа), мс
    # кнопка удерживается дольше чем (с начала степа), мс [состояние]
    def stepFor(self, ms: Optional[int] = None) -> int:
        if read_bf(self.flags, EB_STP):
            res = self.pressFor() - self.hold_time * 2
            return res > ms if ms is not None else res
        return 0

    # ====================== POLL ======================
    # обработка кнопки значением
    def tick(self, s: bool) -> int:
        self.clear()
        s = self.pollBtn(s)
        if self.cb and s:
            self.cb()

        return s

    # обработка виртуальной кнопки как одновременное нажатие двух других кнопок
    # def tick(self, b0: "VirtButton", b1: "VirtButton") -> bool:
    #     if read_bf(self.flags, EB_BOTH):
    #         if not b0.pressing() and not b1.pressing():
    #             self.flags = clr_bf(self.flags, EB_BOTH)

    #         if not b0.pressing():
    #             b0.reset()

    #         if not b1.pressing():
    #             b1.reset()

    #         b0.clear()
    #         b1.clear()
    #         return self.tick(1)
    #     else:
    #         if b0.pressing() and b1.pressing():
    #             self.flags = set_bf(self.flags, EB_BOTH)
    #         return self.tick(0)

    # обработка кнопки без сброса событий и вызова коллбэка
    def tickRaw(self, s: bool) -> int:
        return self.pollBtn(s)

    # ====================== PRIVATE ======================

    def pollBtn(self, s: bool) -> int:
        if read_bf(self.flags, EB_BISR):
            self.flags = clr_bf(self.flags, EB_BISR)
            s = 1
        else:
            s ^= read_bf(self.flags, EB_INV)

        if not read_bf(self.flags, EB_BUSY):
            if s:
                self.flags = set_bf(self.flags, EB_BUSY)
            else:
                return 0

        ms = floor(monotonic_ns() / 1000)
        deb = ms - self.tmr

        if s:  # кнопка нажата
            if not read_bf(self.flags, EB_PRS):  # кнопка не была нажата ранее
                if (
                    not read_bf(self.flags, EB_DEB) and self.deb_time
                ):  # дебаунс ещё не сработал
                    self.flags = set_bf(self.flags, EB_DEB)  # будем ждать дебаунс
                    self.tmr = ms  # сброс таймаута
                else:  # первое нажатие
                    if deb >= self.deb_time or not self.deb_time:  # ждём EB_DEB_TIME
                        self.flags = set_bf(
                            self.flags, EB_PRS | EB_PRS_R
                        )  # флаг на нажатие
                        self.ftmr = ms
                        self.tmr = ms  # сброс таймаута
            else:  # кнопка уже была нажата
                if not read_bf(self.flags, EB_EHLD):
                    if not read_bf(
                        self.flags, EB_HLD
                    ):  # удержание ещё не зафиксировано
                        if deb >= self.hold_time:
                            self.flags = set_bf(
                                self.flags, EB_HLD_R | EB_HLD
                            )  # флаг что было удержание
                            self.tmr = ms  # сброс таймаута
                    else:  # удержание зафиксировано
                        if deb >= (
                            self.step_time
                            if read_bf(self.flags, EB_STP)
                            else self.hold_time
                        ):
                            self.flags = set_bf(
                                self.flags, EB_STP | EB_STP_R
                            )  # флаг степ
                            self.tmr = ms  # сброс таймаута

        else:  # кнопка не нажата
            if read_bf(self.flags, EB_PRS):  # но была нажата
                if deb >= self.deb_time:  # ждём EB_DEB_TIME
                    if not read_bf(self.flags, EB_HLD):
                        self.clicks += 1  # не удерживали - это клик

                    if read_bf(self.flags, EB_EHLD):
                        self.clicks = 0  #

                    self.flags = set_bf(self.flags, EB_REL | EB_REL_R)  # флаг release
                    self.flags = clr_bf(self.flags, EB_PRS)  # кнопка отпущена
            elif read_bf(self.flags, EB_REL):
                if not read_bf(self.flags, EB_EHLD):
                    self.flags = set_bf(
                        self.flags, EB_REL_R
                    )  # флаг releaseHold / releaseStep

                self.flags = clr_bf(self.flags, EB_REL | EB_EHLD)
                self.tmr = ms  # сброс таймаута
            elif self.clicks > 0:  # есть клики, ждём EB_CLICK_TIME
                if read_bf(self.flags, EB_HLD | EB_STP) or deb >= self.click_time:
                    self.flags = set_bf(self.flags, EB_CLKS_R)
                elif self.ftmr:
                    self.ftmr = 0
            elif read_bf(self.flags, EB_BUSY):
                self.flags = clr_bf(self.flags, EB_HLD | EB_STP | EB_BUSY)
                self.flags = set_bf(self.flags, EB_TOUT)
                self.ftmr = 0
                self.tmr = ms  # test!!

            if read_bf(self.flags, EB_DEB):
                self.flags = clr_bf(
                    self.flags, EB_DEB
                )  # сброс ожидания нажатия (дебаунс)

        return read_bf(
            self.flags, EB_CLKS_R | EB_PRS_R | EB_HLD_R | EB_STP_R | EB_REL_R
        )


class Button(VirtButton):
    def __init__(self, npin=0, mode=GPIO.PUD_UP, btnLevel=GPIO.HIGH):
        super().__init__()

        self.pin = npin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=mode)
        self.setBtnLevel(btnLevel)

    # прочитать текущее значение кнопки (без дебаунса)
    def read(self):
        return GPIO.input(self.pin) ^ read_bf(EB_INV)

    # функция обработки, вызывать в loop
    def tick(self):
        # print(f"{self.pin}: {GPIO.input(self.pin)}")
        return super().tick(GPIO.input(self.pin))

    # обработка кнопки без сброса событий и вызова коллбэка
    def tickRaw(self):
        return super().tickRaw(GPIO.input(self.pin))
