"""
Smacircle S1 offline control client (M0 protocol, Nordic UART Service).

This replaces the dead manufacturer app for the BLE control path. No server,
no account, no "activation" needed — the device only wants the 4-digit BLE
password (default 0000), then obeys lock/unlock/gear/light/cruise commands.

Usage:
    python ride.py scan
    python ride.py ride [--address AA:BB:..] [--name Smacircle] [--password 0000]
                        [--no-unlock] [--yes]

Interactive commands once connected:
    unlock | lock | gear N | light on|off | cruise on|off
    status | raw <hexbytes> | help | quit

============================  SAFETY  ============================
A real scooter can lurch when unlocked / when a gear is set. For the
FIRST unlock test:  put the scooter on a stand with the wheel OFF the
ground, clear of people, gear 0/1. You assume all risk.
=================================================================
"""
import argparse
import asyncio
import sys

from bleak import BleakClient, BleakScanner
from protocol import M0

WARN = __doc__[__doc__.index("==="):]


async def find_device(address=None, name=None, timeout=12.0):
    if address:
        print(f"Looking for {address} ...")
        dev = await BleakScanner.find_device_by_address(address, timeout=timeout)
        if dev:
            return dev
        print("Not found by address; falling back to a service scan.")
    print(f"Scanning {timeout:.0f}s for the Nordic UART service ...")
    found = await BleakScanner.discover(timeout=timeout, return_adv=True)
    for dev, adv in found.values():
        svcs = [u.lower() for u in (adv.service_uuids or [])]
        nm = (adv.local_name or dev.name or "")
        if M0.SERVICE in svcs or (name and name.lower() in nm.lower()):
            print(f"Found {dev.address}  ({nm or 'no name'})")
            return dev
    return None


def _write_response(client):
    """Pick with/without-response based on the characteristic's properties."""
    for svc in client.services:
        for ch in svc.characteristics:
            if ch.uuid.lower() == M0.WRITE:
                return "write" in ch.properties  # True => needs response
    return True


async def telemetry_loop(state):
    """Print telemetry only when it changes, so the REPL stays readable."""
    last = None
    while state["run"]:
        t = state.get("tele")
        if t and t != last:
            print(f"\r  [{'LOCKED' if t['locked'] else 'unlocked'}] "
                  f"{t['speed_kmh']:.1f} km/h  batt {t['battery_pct']}%  "
                  f"gear {t['gear']}  light {'on' if t['light'] else 'off'}  "
                  f"cruise {'on' if t['cruise'] else 'off'}"
                  f"{'  ERROR' if t['error'] else ''}   trip {t['trip_km']:.2f} km")
            print("> ", end="", flush=True)
            last = t
        await asyncio.sleep(0.3)


async def repl(client, response, state):
    loop = asyncio.get_event_loop()
    write = lambda data: client.write_gatt_char(M0.WRITE, data, response=response)
    help_text = ("commands: unlock | lock | gear N | light on|off | cruise on|off | "
                 "ver | sn | reset | status | raw <hex> | help | quit")
    print(help_text)
    while True:
        line = (await loop.run_in_executor(None, input, "> ")).strip()
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].lower()
        try:
            if cmd in ("quit", "exit", "q"):
                break
            elif cmd == "help":
                print(help_text)
            elif cmd == "unlock":
                await write(M0.unlock()); print("  -> unlock sent")
            elif cmd == "lock":
                await write(M0.lock(True)); print("  -> lock sent")
            elif cmd == "gear":
                await write(M0.gear(int(parts[1]))); print(f"  -> gear {parts[1]}")
            elif cmd == "light":
                await write(M0.light(parts[1].lower() == "on")); print(f"  -> light {parts[1]}")
            elif cmd == "cruise":
                await write(M0.cruise(parts[1].lower() == "on")); print(f"  -> cruise {parts[1]}")
            elif cmd == "ver":
                await write(M0.check_control_version())
                await asyncio.sleep(0.2)
                await write(M0.check_ble_version())
                print("  -> version queries sent (watch for [info] lines)")
            elif cmd == "sn":
                await write(M0.get_card_sn())
                print("  -> serial query sent (watch for [info] line)")
            elif cmd == "reset":
                ans = (await loop.run_in_executor(
                    None, input, "  Reset TOTAL mileage? irreversible [y/N] ")).strip().lower()
                if ans == "y":
                    await write(M0.clear_mileage()); print("  -> mileage reset sent")
                else:
                    print("  cancelled")
            elif cmd == "status":
                print("  ", state.get("tele") or "(no telemetry yet)")
                info = {k: state[k] for k in ("serial", "ctrl_ver", "ble_ver") if state.get(k)}
                if info:
                    print("  info:", info)
            elif cmd == "raw":
                data = bytes.fromhex("".join(parts[1:]))
                await write(data); print(f"  -> sent {data.hex(' ')}")
            else:
                print("  ?", help_text)
        except Exception as e:
            print(f"  ! error: {e}")


async def ride(args):
    print(WARN)
    dev = await find_device(args.address, args.name)
    if not dev:
        print("No scooter found. Power it on and keep it close.")
        return 1

    state = {"run": True, "tele": None}

    def on_notify(_char, data):
        kind, val = M0.parse_frame(bytes(data))
        if kind == "status" and val:
            state["tele"] = val
        elif kind == "control_version":
            state["ctrl_ver"] = val; print(f"\r  [info] controller FW: {val}\n> ", end="", flush=True)
        elif kind == "ble_version":
            state["ble_ver"] = val;  print(f"\r  [info] bluetooth FW: {val}\n> ", end="", flush=True)
        elif kind == "serial":
            state["serial"] = val;   print(f"\r  [info] serial: {val}\n> ", end="", flush=True)
        elif kind == "handshake_ok":
            print("\r  [handshake OK]\n> ", end="", flush=True)
        elif kind == "handshake_fail":
            print("\r  [handshake FAILED — wrong password for this unit]\n> ", end="", flush=True)

    async with BleakClient(dev) as client:
        print(f"Connected: {client.address}")
        response = _write_response(client)
        await client.start_notify(M0.NOTIFY, on_notify)

        print(f"Handshake: sending password '{args.password}' ...")
        await client.write_gatt_char(M0.WRITE, M0.password(args.password), response=response)
        await asyncio.sleep(1.5)

        # Read-only device info (firmware + serial) — prints as [info] lines.
        for q in (M0.check_control_version(), M0.check_ble_version(), M0.get_card_sn()):
            await client.write_gatt_char(M0.WRITE, q, response=response)
            await asyncio.sleep(0.25)

        if not args.no_unlock:
            if not args.yes:
                ans = await asyncio.get_event_loop().run_in_executor(
                    None, input, "Send UNLOCK now? wheel off ground! [y/N] ")
                if ans.strip().lower() != "y":
                    print("Skipped unlock.")
                    args.no_unlock = True
            if not args.no_unlock:
                await client.write_gatt_char(M0.WRITE, M0.unlock(), response=response)
                print("Unlock sent.")

        tele_task = asyncio.create_task(telemetry_loop(state))
        try:
            await repl(client, response, state)
        finally:
            state["run"] = False
            tele_task.cancel()
            try:
                await client.write_gatt_char(M0.WRITE, M0.lock(True), response=response)
                print("Re-locked on exit.")
            except Exception:
                pass
    return 0


def main():
    ap = argparse.ArgumentParser(description="Smacircle S1 offline BLE client")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan", help="scan for the scooter")
    r = sub.add_parser("ride", help="connect, handshake, control")
    r.add_argument("--address", help="BLE MAC/address from scan")
    r.add_argument("--name", default="sma", help="name substring to match")
    r.add_argument("--password", default=M0.DEFAULT_PASSWORD)
    r.add_argument("--no-unlock", action="store_true", help="connect only, don't unlock")
    r.add_argument("--yes", action="store_true", help="skip the unlock confirmation prompt")
    args = ap.parse_args()

    if args.cmd == "scan":
        import scan
        asyncio.run(scan.main())
    else:
        try:
            sys.exit(asyncio.run(ride(args)))
        except KeyboardInterrupt:
            # Let the BleakClient context manager unwind so the OS hangs up
            # the GATT link cleanly. Do NOT just close the window.
            print("\nInterrupted — disconnecting cleanly. (Tip: type 'quit' next time.)")


if __name__ == "__main__":
    main()
