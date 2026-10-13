import asyncio
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "XRP_DOG"

RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


def notification_handler(sender, data):
    print("XRP:", data.decode(errors="ignore"))


async def main():
    print("Scanning for", DEVICE_NAME)

    devices = await BleakScanner.discover(timeout=5)

    target = None

    for d in devices:
        print(d.name, d.address)

        if d.name == DEVICE_NAME:
            target = d
            break

    if target is None:
        print("Device not found")
        return

    print("Connecting to", target.address)

    async with BleakClient(target.address) as client:
        print("Connected")

        await client.start_notify(TX_UUID, notification_handler)

        while True:
            cmd = input("Command CRAWL / STAND / TEST / PING / q: ")

            if cmd.lower() == "q":
                break

            await client.write_gatt_char(RX_UUID, cmd.encode("utf-8"))

            await asyncio.sleep(0.5)


asyncio.run(main())
