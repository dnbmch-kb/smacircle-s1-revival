"""
Minimal example — connect to a Smacircle S1 and unlock it.

This is the *entire* unlock path. The "security" is a 4-digit BLE password
(default 0000) sent over the Nordic UART Service — no server, no account, no
"activation". `unlock` is just `lock(false)`, a plain characteristic write.

Run:
    python unlock.py <BLE-ADDRESS> [password]

Get the address from a scan first:  `python ../ride.py scan`
After unlocking, kick off with your foot — the S1 is non-zero-start.
"""
import asyncio
import os
import sys

from bleak import BleakClient

# protocol.py lives one directory up
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol import M0


async def unlock(address: str, password: str = "0000"):
    async with BleakClient(address) as client:
        print(f"Connected to {client.address}")
        await client.write_gatt_char(M0.WRITE, M0.password(password))  # handshake
        await asyncio.sleep(1.0)
        await client.write_gatt_char(M0.WRITE, M0.unlock())            # lock(false)
        print("Unlock sent. Kick off to ride.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python unlock.py <BLE-ADDRESS> [password]")
    addr = sys.argv[1]
    pw = sys.argv[2] if len(sys.argv) > 2 else "0000"
    asyncio.run(unlock(addr, pw))
