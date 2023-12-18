import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
PINS = (21, 20, 16, 5, 6, 13, 19, 26)

GPIO.setup(PINS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# B1
# B2
# B3
# L
# U
# P
# D
# R


def my_callback(channel):
    print(f"This is a edge event callback function! {channel}")


for pin in PINS:
    GPIO.add_event_detect(pin, GPIO.BOTH)

    GPIO.add_event_callback(pin, my_callback)


# async def listen_for_key_press():
#     while True:
#         for pin in PINS:
#             if GPIO.input(pin) == GPIO.LOW:
#                 print(f"Key was pressed {pin}")
#         await asyncio.sleep(0.1)


# loop = asyncio.get_event_loop()
# loop.create_task(listen_for_key_press())
# loop.run_forever()
while True:
    ...
GPIO.cleanup()
