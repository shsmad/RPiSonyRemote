import datetime
import time

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)
font = ImageFont.load_default()


font = ImageFont.load_default()
font2 = ImageFont.truetype("fonts/C&C Red Alert [INET].ttf", 16)
font3 = ImageFont.truetype("fonts/better-vcr-5.2.ttf", 16)
font5 = ImageFont.truetype("fonts/PixeloidSans.ttf", 16)

# draw.text((0, 0), "Hello world 123", font=font3, fill=255)
# draw.text((0, 20), "Hello world 123", font=font2, fill=255)
# draw.text((0, 40), "Hello world 123", font=font5, fill=255)
while True:
    now = datetime.datetime.now()
    today_date = now.strftime("%d %b %y")
    today_time = now.strftime("%H:%M:%S")

    with canvas(device) as draw:
        margin = 4
        cx = 0
        cy = min(device.height, 64) / 2

        draw.text((2 * (cx + margin), cy - 24), today_date, fill="white", font=font5)
        draw.text((2 * (cx + margin), cy), today_time, fill="yellow", font=font5)


time.sleep(5)
