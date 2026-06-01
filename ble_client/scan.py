"""
Scan for nearby BLE devices and flag the Smacircle scooter.

Run:  python scan.py
The S1 advertises the Nordic UART Service 6e400001-... (M0 protocol).
"""
import asyncio
from bleak import BleakScanner
from protocol import M0, C041


async def main(timeout=10.0):
    print(f"Scanning {timeout:.0f}s ...\n")
    found = await BleakScanner.discover(timeout=timeout, return_adv=True)
    if not found:
        print("No BLE devices seen. Is Bluetooth on? Is the scooter powered?")
        return

    rows = sorted(found.values(), key=lambda t: t[1].rssi or -999, reverse=True)
    for dev, adv in rows:
        svcs = [u.lower() for u in (adv.service_uuids or [])]
        tag = ""
        if M0.SERVICE in svcs:
            tag = "  <<< SMACIRCLE (M0 / Nordic UART)"
        elif C041.SERVICE in svcs:
            tag = "  <<< SMACIRCLE (C041)"
        name = adv.local_name or dev.name or "(no name)"
        print(f"{dev.address}  rssi={adv.rssi:>4}  {name}{tag}")
        for u in svcs:
            print(f"        svc {u}")
    print("\nUse the address above:  python ride.py ride --address <ADDR>")


if __name__ == "__main__":
    asyncio.run(main())
