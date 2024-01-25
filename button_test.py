import RPi.GPIO as GPIO

GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)


def button_callback(*args):
    print(args)


PINS = (21, 20, 16, 5, 6, 13, 19, 26)
for pin in PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(pin, GPIO.BOTH, callback=button_callback)

while True:
    pass
