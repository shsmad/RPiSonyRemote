from .device.input import InputDevice
from .device.output import OutputDevice
from .timer import TimerMs


class Router:
    def __init__(
        self, input_devices: list[InputDevice], output_devices: list[OutputDevice]
    ):
        self.timer = TimerMs(10, 0, 0)
        self.input_devices = input_devices
        self.output_devices = output_devices

    def init(self):
        self.timer.start()

    def tick(self, menu_level: int = 0):
        if not self.timer.tick() or menu_level > 0:
            return

        trigger = any(i_device.handle() for i_device in self.input_devices)
        for o_device in self.output_devices:
            o_device.tick(trigger)
