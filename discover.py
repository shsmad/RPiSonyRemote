import argparse
import asyncio
import time

import logging
logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)

from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

shu = b'\x01\x06'   # Shutter Half Up
shd = b'\x01\x07'   # Shutter Half Down
sfu = b'\x01\x08'   # Shutter Fully Up
sfd = b'\x01\x09'   # Shutter Fully Down
ret = b'\x01\x0e'   # Record Up
rec = b'\x01\x0f'   # Record Down
afu = b'\x01\x14'   # AF-On Up
afd = b'\x01\x15'   # AF-On Down
c1u = b'\x01\x20'   # Custom Up 1
c1d = b'\x01\x21'   # Custom Down 1
# commands with step size
ozt = b'\x02\x44\x00'   # optical zoom tele?
dzt = b'\x02\x45\x10'   # digital zoom tele?
ozw = b'\x02\x46\x00'   # optical zoom wide?
dzw = b'\x02\x47\x10'   # digital zoom wide?
zib = b'\x02\x6a\x00'   # Zoom In??
fib = b'\x02\x6b\x00'   # Focus In
zob = b'\x02\x6c\x00'   # Zoom Out??
fob = b'\x02\x6d\x00'   # Focus Out




async def get_sony_device(timeout: int = 5):
    devices = await BleakScanner.discover(
        timeout=timeout,
        return_adv=True
    )

    for device, adv in devices.values():
        print(device.name)
        if device.name == "ILCE-7C":
            print("device: ", device)
            print("\taddress: ", device.address)
            print("\tdetails: ", device.details)
            # print("metadata: ", device.metadata)
            print("\tname: ", device.name)
            # print("rssi: ", device.rssi)

            print("\tadv: ", adv)
            print("\t\tlocal_name: ", adv.local_name)
            print("\t\tmanufacturer_data: ", adv.manufacturer_data)
            print("\t\tplatform_data: ", adv.platform_data)
            print("\t\trssi: ", adv.rssi)
            print("\t\tservice_data: ", adv.service_data)
            print("\t\tservice_uuids: ", adv.service_uuids)
            print("\t\ttx_power: ", adv.tx_power)

            return device, adv

    return None, None

def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    logging.info("%r: %r", characteristic, data)

async def main(args: argparse.Namespace):
    print("scanning for 5 seconds, please wait...")

    # device, adv = await get_sony_device()
    # if not device:
    #     print("no devices")
    #     return
    device = "DC:FE:23:DC:D0:DA"

    async with BleakClient(device) as client:
        print(f"Connected: {client.is_connected}")
        # paired = await client.pair(protection_level=2)
        # print(f"Paired: {paired}")

        # [Service] 8000ff00-ff00-ffff-ffff-ffffffffffff (Handle: 94): Unknown
        # [Characteristic] 0000ff02-0000-1000-8000-00805f9b34fb (Handle: 95): Vendor specific (notify)
        # [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 97): Client Characteristic Configuration, Value: bytearray(b'\x01\x00')
        # [Characteristic] 0000ff01-0000-1000-8000-00805f9b34fb (Handle: 98): Vendor specific (write)

        handle = None
        for service in client.services:
            if service.uuid.lower() != "8000FF00-FF00-FFFF-FFFF-FFFFFFFFFFFF".lower():
                continue

            for char in service.characteristics:
                if char.uuid.startswith("0000ff01"):
                    handle = char.handle

        if not handle:
            return

        await client.start_notify("0000ff02-0000-1000-8000-00805f9b34fb", notification_handler)

        # test shutter button to take picture
        print("shd")
        await client.write_gatt_char(handle, shd)
        await asyncio.sleep(0.2)
        print("sfd")
        await client.write_gatt_char(handle, sfd)
        await asyncio.sleep(0.2)
        print("shu")
        await client.write_gatt_char(handle, shu)
        await asyncio.sleep(0.2)
        print("sfu")
        await client.write_gatt_char(handle, sfu)
        # actually can subscribe to ff02 and wait for shutter complete
        await asyncio.sleep(2)

        await client.stop_notify("0000ff02-0000-1000-8000-00805f9b34fb")


            # print(f"[Service] {service}" )
            # # print(f"\tadd_characteristic: {service.add_characteristic}")
            # print(f"\tcharacteristics: {service.characteristics}")
            # # print(f"\tget_characteristic: {service.get_characteristic}")
            # print(f"\thandle: {service.handle}")
            # print(f"\tuuid: {service.uuid}")


            # for char in service.characteristics:
            #     print(f"\tchar {char}")
            #     # print(f"\t\tadd_descriptor: {char.add_descriptor}")
            #     print(f"\t\tdescription: {char.description}")
            #     print(f"\t\tdescriptors: {char.descriptors}")
            #     # print(f"\t\tget_descriptor: {char.get_descriptor}")
            #     print(f"\t\thandle: {char.handle}")
            #     print(f"\t\tmax_write_without_response_size: {char.max_write_without_response_size}")
            #     print(f"\t\tobj: {char.obj}")
            #     print(f"\t\tpath: {char.path}")
            #     print(f"\t\tproperties: {char.properties}")
            #     print(f"\t\tservice_handle: {char.service_handle}")
            #     print(f"\t\tservice_uuid: {char.service_uuid}")
            #     print(f"\t\tuuid: {char.uuid}")
        print("disconnecting...")

    print("disconnected")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )

    args = parser.parse_args()

    asyncio.run(main(args))
