import time

import RPi.GPIO as GPIO

from libs.inputs import Button

GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)
PINS = (21,)  #  20, 16, 5, 6, 13, 19, 26)
buttons = [Button(pin) for pin in PINS]

while True:
    for button in buttons:
        print(button.tick())
        # if button.turn():
        #     print(
        #         f"turn: dir {button.dir()}, fast {button.fast()}, hold {button.pressing()}, counter {button.counter}, clicks {button.getClicks()}"
        #     )

        # обработка поворота раздельная
        # if button.left():
        #     print("left")
        # if button.right():
        #     print("right")
        # if button.leftH():
        #     print("leftH")
        # if button.rightH():
        #     print("rightH")

        # кнопка
        if button.press():
            print("press")
        # if button.click():
        #     print("click")

        # if button.release():
        #     print("release")
        #     print(
        #         f"clicks: {button.getClicks()}, steps: {button.getSteps()}, press for: {button.pressFor()}, hold for: {button.holdFor()}, step for: {button.stepFor()}"
        #     )

        # # состояния
        # print(button.pressing())
        # print(button.holding())
        # print(button.busy())
        # print(button.waiting())

        # # таймаут
        # if button.timeout(1000):
        #     print("timeout!")

        # # удержание
        # if button.hold():
        #     print("hold")
        # if button.hold(3):
        #     print("hold 3")

        # # импульсное удержание
        # if button.step():
        #     print("step")
        # if button.step(3):
        #     print("step 3")

        # # отпущена после импульсного удержания
        # if button.releaseStep():
        #     print("release step")
        # if button.releaseStep(3):
        #     print("release step 3")

        # # отпущена после удержания
        # if button.releaseHold():
        #     print("release hold")
        # if button.releaseHold(2):
        #     print("release hold 2")

        # # проверка на количество кликов
        # if button.hasClicks(3):
        #     print("has 3 clicks")

        # # вывести количество кликов
        # if button.hasClicks():
        #     print(f"has clicks: {button.getClicks()}")

    time.sleep(0.2)
