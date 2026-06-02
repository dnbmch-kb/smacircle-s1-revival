# Smacircle S1 — Offline Revival

Reverse-engineered, **server-free** control for the **Smacircle S1** folding e-bike — a Python
BLE client and a Qt 6 desktop/mobile app that let you actually *use* a device the manufacturer
abandoned.

> **Status:** working. The S1 connects, unlocks, streams live telemetry, and rides — **no
> account, no server, no "activation."** Prebuilt **Android APK** and portable **Windows** build
> on the [Releases](https://github.com/dnbmch-kb/smacircle-s1-revival/releases) page. Roadmap in
> [BACKLOG.md](BACKLOG.md).

---

## Why this exists

The S1 is a "connected" scooter: out of the box it demands **activation through the vendor's app**
before the wheel unlocks. By **2026 that path is dead**:

- The official app is **gone from both the App Store and Google Play.**
- An **old APK** stalls at sign-up — the **SMS verification code never arrives** (it routes through
  MobTech's `SMSSDK`, tied to the vendor's defunct backend). No backend, no code, no unlock.
- So a **brand-new, never-activated** unit is, by the vendor's own design, a **paperweight.**

Except it never had to be — the "activation" was never real protection, and this project proves it
on real hardware.

## What we found

Decompiling the app (jadx) and sniffing the BLE link: the S1 speaks a protocol the app calls
**"M0"** over the standard **Nordic UART Service** (`6e400001-…`):

- **No cryptography.** The "encryption" is a keyless XOR chain; the checksum is `0xFFFF − sum`.
  Every command is reproducible offline.
- **The BLE password is `0000`** — the entire handshake.
- **"Activation" is server bookkeeping.** The app calls `POST_ACTIVATE_PRODUCT` to bind the bike to
  an account, then sends a plain `unlock`. **The firmware never checks the server** — send the
  unlock yourself and the lock releases. Confirmed on a never-activated unit.
- **"Won't move" is not a lock** — the S1 is **non-zero-start**: kick off first, *then* the throttle
  engages. Normal, documented behaviour — not DRM.

### What was inside the original app

For a product whose one job is "talk to a scooter over Bluetooth," the vendor's app is mostly
**third-party SDK glue**:

| SDK | Package | Purpose |
|-----|---------|---------|
| Alibaba Cloud OSS | `com.alibaba.sdk.android.oss` | cloud object storage |
| Alibaba Fastjson | `com.alibaba.fastjson` | JSON |
| MobTech ShareSDK | `cn.sharesdk`, `com.mob.*` | social sharing |
| MobTech SMSSDK | `cn.smssdk` | SMS verification (the one that never arrives) |

The device-specific part — the BLE protocol — is a few hundred lines of XOR-and-checksum. The rest
is account plumbing, third-party data SDKs, and "activation" ceremony.

## Editorial

The "activation" that justified all this was always theatre. Read the decompiled app and you find
no embedded engineering — a thin Bluetooth shim drowning in third-party Chinese SDKs (Alibaba,
MobTech). This is the work of **Klappradfahrer** (German: "folding-bike riders" — weekend dabblers,
not engineers), a crew of **kutyaütő balfaszok** (Hungarian, roughly: bungling good-for-nothing
clowns) who wired SDKs together, called it a product, and walked off — leaving paying owners with
bricks: instant e-waste, including brand-new units never opened.

*(Opinions here are the author's; the facts are above, straight from the app's bytecode.)*

## Repository layout

| Path | What |
|------|------|
| [`ble_client/`](ble_client/) | Python (`bleak`) reference client — scan, handshake, unlock, gear/light/cruise, live telemetry. Proven on hardware first. |
| [`qt_app/`](qt_app/) | Qt 6 C++/QML app — battery/speed dashboard, one-tap unlock + controls. Desktop + Android. |
| [`BACKLOG.md`](BACKLOG.md) | Ideas & roadmap. |
| `work/` | Local decompilation + tooling. **Not committed** (third-party copyright). |

## Download & install

From the [**Releases**](https://github.com/dnbmch-kb/smacircle-s1-revival/releases) page:

- **Android** — `smacircle-s1-revival.apk`. Needs **Android 9.0+**. Allow "install unknown apps", tap to
  install; first launch asks for the Bluetooth permission.
- **Windows** — `smacircle-s1-revival-windows-x64.zip`. Unzip, run `smacircle-s1-revival.exe` (portable).

## Run / build from source

**Python client** — the protocol reference; no build step, just run it (`bleak`):
```powershell
cd ble_client
python -m venv venv
.\venv\Scripts\python.exe -m pip install bleak
.\venv\Scripts\python.exe ride.py scan                  # find the scooter
.\venv\Scripts\python.exe ride.py ride --address <ADDR> # connect + control
```
Minimal unlock-only example: [`ble_client/examples/unlock.py`](ble_client/examples/unlock.py).

**Qt app** — build it (Windows desktop; needs Qt 6.10 MSVC + the Qt Bluetooth module):
```bat
cd qt_app
build.bat   :: configure + build (Release)
deploy.bat  :: bundle the Qt runtime (first time)
run.bat     :: launch
```

No bike handy? `build-demo.bat` builds a separate **simulated-S1 demo** (a "Try demo" button
fakes a connection and streams telemetry) so the whole UX — dashboard, controls, toasts — can be
clicked through with no hardware. The demo flag is off in release CI, so this code never ships.

## Continuous integration

| Workflow | Triggers | Output |
|----------|----------|--------|
| [`android.yml`](.github/workflows/android.yml) | push `main`, `v*` tag, manual | `arm64-v8a` APK — artifact on push, Release asset on tag |
| [`windows.yml`](.github/workflows/windows.yml) | `v*` tag, manual | `windeployqt` portable zip — Release asset on tag |

Push a tag `vX.Y.Z` to cut a Release carrying both builds. With no setup the APK is signed with an
ephemeral key (installs fine; updates need a reinstall); for stable in-place updates add the repo
secrets `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`,
`ANDROID_KEY_PASSWORD`.

## Platforms

Desktop and Android are covered. **iOS isn't** — Apple requires a paid Developer Program
(~US$100/yr) before an app runs on a real iPhone, with no free permanent sideload. And the author
is an **embedded developer, not an iOS app studio**. The Qt/QML is cross-platform and *ready* for
iOS, so the door's open if someone with an Apple account wants to carry that build.

## License

MIT — see [LICENSE](LICENSE). Covers this project's own code; it grants no rights to the
manufacturer's software, which is not included here (see Disclaimer).

## Disclaimer

Personal **interoperability** project for hardware **I own**. No vendor code is redistributed — the
decompiled app stays in `work/` (git-ignored). Not affiliated with or endorsed by the manufacturer.
Provided **as-is, no warranty**; an e-bike is a motor vehicle and you assume all risk operating it.
Mind your local road laws.
