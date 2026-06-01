# Smacircle S1 — Offline Revival

Reverse-engineered, **server-free** control for the **Smacircle S1** folding e-bike —
a Python BLE client and a Qt 6 desktop/mobile app that let you actually *use* a
device the manufacturer abandoned.

> **Status:** working. The S1 connects, unlocks, streams live telemetry, and rides —
> with **no account, no server, no "activation."** Roadmap in [BACKLOG.md](BACKLOG.md).

---

## Why this exists

The Smacircle S1 is a "connected" scooter: out of the box it demands to be
**activated through the vendor's phone app** before the wheel will unlock. By
**2026 that path is dead**:

- The official app is **gone from both the App Store and Google Play** — you simply
  cannot install it anymore.
- Track down an **old APK** and you get stuck at sign-up: the **SMS verification code
  never arrives.** The app routes verification through MobTech's `SMSSDK`, tied to the
  vendor's now-defunct backend — no live backend, no code, no account, no unlock.
- So a **brand-new, never-activated** unit is, *by the vendor's own design*, a
  **paperweight.**

Except it never had to be. The "activation" was never real protection — and this
project proves it on real hardware.

## What we found

Decompiling the app (jadx) and inspecting the BLE link shows the S1 speaks a protocol
the app calls **"M0"** over the standard **Nordic UART Service** (`6e400001-…`):

- **No cryptography.** The "encryption" is a keyless XOR chain; the checksum is
  `0xFFFF − sum`. Every command is reproducible offline.
- **The BLE password is `0000`.** That is the entire handshake.
- **"Activation" is server bookkeeping.** The app calls `POST_ACTIVATE_PRODUCT` to bind
  the bike to an account, then sends an ordinary `unlock` command. **The firmware never
  checks whether the server approved** — send the unlock yourself and the lock releases.
  Confirmed on a never-activated unit: lock released, telemetry flowing, rides fine.
- **"Won't move" is not a lock** — the S1 is **non-zero-start** (kick-to-start): push off
  with your foot first, *then* the throttle engages. Documented, normal behaviour — not DRM.

### What's actually inside the app

For a product whose single job is "talk to a scooter over Bluetooth," the codebase is
mostly **third-party SDK glue**:

| SDK | Package | Purpose |
|-----|---------|---------|
| Alibaba Cloud OSS | `com.alibaba.sdk.android.oss` | cloud object storage |
| Alibaba Fastjson | `com.alibaba.fastjson` | JSON |
| MobTech ShareSDK | `cn.sharesdk`, `com.mob.*` | social sharing |
| MobTech SMSSDK | `cn.smssdk` | SMS verification (the one that never arrives) |

The genuinely device-specific part — the BLE protocol — is a few hundred lines of
XOR-and-checksum. Everything else is account plumbing, third-party data SDKs, and
"activation" ceremony.

## Editorial

None of this should have been necessary. A company sold a *physical* product that
depends on its servers, then took the servers **and** the apps away and walked off —
leaving paying owners holding bricks, including brand-new units that were never opened.
That is the part worth being angry about.

And the "activation" that supposedly justified all of it is theatre. The hardware never
needed it; the lock is released by a plain BLE write any client can send. The server's
only real job was writing your name next to a serial number — bookkeeping dressed up as
security.

Read the decompiled app and you don't find embedded engineering. You find a thin
Bluetooth shim bolted onto a stack of third-party Chinese SDKs (Alibaba Cloud, MobTech)
plus a heap of account/"activation" bloat. This is not the work of embedded developers —
it's the work of **Klappradfahrer** (German: "folding-bike riders" — weekend dabblers,
not engineers), a crew of **kutyaütő balfaszok** (Hungarian, roughly: bungling
good-for-nothing clowns) who wired SDKs together and called it a product. The actual
scooter protocol is trivial; the effort went everywhere *except* shipping something that
outlives its vendor.

*(Opinions in this section are the author's. The technical claims above come straight
from the app's own bytecode and from testing on real hardware.)*

## Repository layout

| Path | What |
|------|------|
| [`ble_client/`](ble_client/) | Python (`bleak`) reference client — scan, handshake, unlock, gear/light/cruise, live telemetry. Proven on hardware first. |
| [`qt_app/`](qt_app/) | C++/QML (Qt 6) app — battery/speed dashboard, one-tap unlock + controls. Desktop today; Android next. |
| [`BACKLOG.md`](BACKLOG.md) | Ideas & roadmap. |
| `work/` | Local decompilation + tooling. **Not committed** (third-party copyright, large). |

## Quick start

### Python client
```powershell
cd ble_client
python -m venv venv; .\venv\Scripts\pip install bleak
.\venv\Scripts\python.exe ride.py scan                 # find the scooter
.\venv\Scripts\python.exe ride.py ride --address <ADDR># connect, handshake, control
```

### Qt app (Windows desktop)
Needs Qt 6.10 (MSVC) + the Qt Bluetooth module. Then:
```bat
cd qt_app
build.bat        :: configure + build (Release)
deploy.bat       :: bundle the Qt runtime (first time only)
run.bat          :: launch
```

## Disclaimer

Personal **interoperability** project for hardware **I own**. No vendor code is
redistributed here — the decompiled app stays in `work/`, which is git-ignored. Not
affiliated with or endorsed by the manufacturer. Provided **as-is, no warranty**; an
e-bike is a motor vehicle and you assume all risk operating it. Mind your local road laws.
