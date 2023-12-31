import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

logger = logging.getLogger(__name__)

SHU = b"\x01\x06"  # Shutter Half Up
SHD = b"\x01\x07"  # Shutter Half Down
SFU = b"\x01\x08"  # Shutter Fully Up
SFD = b"\x01\x09"  # Shutter Fully Down
RET = b"\x01\x0e"  # Record Up
REC = b"\x01\x0f"  # Record Down
AFU = b"\x01\x14"  # AF-On Up
AFD = b"\x01\x15"  # AF-On Down
C1U = b"\x01\x20"  # Custom Up 1
C1D = b"\x01\x21"  # Custom Down 1
# commands with step size
OZT = b"\x02\x44\x00"  # optical zoom tele?
DZT = b"\x02\x45\x10"  # digital zoom tele?
OZW = b"\x02\x46\x00"  # optical zoom wide?
DZW = b"\x02\x47\x10"  # digital zoom wide?
ZIB = b"\x02\x6a\x00"  # Zoom In??
FIB = b"\x02\x6b\x00"  # Focus In
ZOB = b"\x02\x6c\x00"  # Zoom Out??
FOB = b"\x02\x6d\x00"  # Focus Out
# signals
F_ACQUIRED = b"\x02\x3F\x20"  # Focus Acquired (half pressed)
S_ACTIVE = b"\x02\xA0\x20"  # Shutter Active (full pressed)
S_READY = b"\x02\xA0\x00"  # Shutter Ready (half up in bulb or done in fixed shutter speed)
F_LOST = b"\x02\x3F\x00"  # Focus Lost (up)


async def get_sony_device(timeout: int = 5) -> list[tuple[BLEDevice, AdvertisementData]]:
    res = []

    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)

    for device, adv in devices.values():
        logger.debug(f"{device.name} [{device.address}]")
        if device.name == "ILCE-7C":
            logger.debug(f"device: {device}")
            logger.debug(f"\taddress: {device.address}")
            logger.debug(f"\tdetails: {device.details}")
            logger.debug(f"\tname: {device.name}")
            logger.debug(f"\tadv: {adv}")
            logger.debug(f"\t\tlocal_name: {adv.local_name}")
            logger.debug(f"\t\tmanufacturer_data: {adv.manufacturer_data}")
            logger.debug(f"\t\tplatform_data: {adv.platform_data}")
            logger.debug(f"\t\trssi: {adv.rssi}")
            logger.debug(f"\t\tservice_data: {adv.service_data}")
            logger.debug(f"\t\tservice_uuids: {adv.service_uuids}")
            logger.debug(f"\t\ttx_power: {adv.tx_power}")

            res.append((device, adv))

    return res


async def take_shot(client: BleakClient, handle: int, af_enabled: bool = False) -> None:
    # TODO: MF mode
    # Hence in order to take a picture, you start by sending 0x0106 to the camera and then 0x0107.
    await client.write_gatt_char(handle, SHU)
    if af_enabled:
        await client.write_gatt_char(handle, SHD)
    # If the camera is set to “autofocus” the camera will first send back 0x02 0x3F 0x00 followed by 0x02 0x3F 0x20 with manual focus skipping this.
    # You then proceed to send the camera 0x0109 and then 0x0108 which takes the picture.
    await client.write_gatt_char(handle, SFD)
    await client.write_gatt_char(handle, SFU)
    # Camera will indicate that the picture has been taken by first sending 0x02 0xA0 0x00 followed by 0x02 0xA0 0x20.
    # From here you need to send 0x0106 for the camera to reset, otherwise the menu system on the A7 III seems to lock up (???).
    await client.write_gatt_char(handle, SHU)
