# Smacircle — Backlog

Ideas and open work for the offline BLE client (`ble_client/`, Python) and the Qt app
(`qt_app/`, C++/QML). Discussion notes, not commitments.

Status key: 🔵 idea · 🟡 planned · ⚠️ needs care · ❄️ parked

## Open

### Unified connect / disconnect button  *(qt_app)*
Merge the top "Scan & Connect" and bottom "Disconnect" into one button whose label +
action follow the connection state.

- **Why:** less clutter, one control.
- **Catch — stay honest (cf. the `hasData` rule):** connection is really 4 states, but
  `BleController` only exposes `scanning` + `connected`. There's a gap during *connecting*
  (both false) where a naive toggle would flash back to "Scan & Connect".
- **States:** Idle → "Scan & Connect"; Scanning → "Scanning…" (tap-to-cancel);
  Connecting → "Connecting…"; Connected → "Disconnect".
- **Work:** add a small state enum/property to `BleController` (backend change, not just QML).

### Multiple devices + non-M0 GATT robustness  *(qt_app + protocol)*
Scan currently matches name `SMACIRCLE` **or** service `6e400001`, then auto-connects to the
first match and stops.

- **Multiple S1s in range:** picks whichever is seen first → could bind the wrong one. Fix:
  device-list picker (like Qt's heart-rate `DeviceFinder`) and/or remember the chosen address
  in `QSettings` and reconnect only to that one.
- **Different GATT / protocol:** the Qt app is **M0-only**. A C041 unit (ported in Python
  `protocol.py`, not in Qt) would connect but fail gracefully ("Nordic UART service not
  found!"). Fix: detect the present service at discovery and pick the matching protocol — a
  C++ port of the C041 path.
- Our S1 *does* advertise `6e400001`, so it works today; the connect-time service check is the
  reliable gate.

### iOS CI pipeline (simulator build)  *(ci)*
Add `.github/workflows/ios.yml`: build for the **iOS simulator** on a macOS runner (free on a
public repo; proves the iOS build compiles). Device / TestFlight signing steps gated behind
Apple Developer secrets — dormant until an account exists. (See README → Platforms for the
$99 signing wall; this is build-only validation, not distribution.)

### Quality-of-life
- Qt: keep-screen-on while connected, auto-reconnect to last device, low-battery toast,
  larger touch targets for mobile.
- Script: one-shot `ride.py unlock --address X` (connect→unlock→exit), telemetry CSV logging.

### Release polish
- **APK slimming** — the release APK is ~47 MB. Strip unused QML modules + Qt translations and
  tighten the deployment to roughly halve it.
- **README screenshot/GIF** — a shot of the dashboard (author to capture).
- **Stable signing keystore** — generate a release `.jks` and store it + its credentials as the
  repo secrets (`ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`,
  `ANDROID_KEY_PASSWORD`) so APK updates install in place instead of needing a reinstall. Do it
  before the next release so it's the last build signed with an ephemeral key. (Walk-through on
  request.)

## Open questions (verify on hardware)

- Does `clearAllMileage` reset the **total** odometer or the **trip**? (button is labeled
  "Reset mileage" + confirm dialog until confirmed.)
- Do **Serial / Controller FW / Bluetooth FW** populate on a real connect? The reply-frame
  routing (type 1, `ex==0x10` for serial, addr for control vs BLE) is inferred; the Python
  `ver` / `sn` commands dump raw bytes if it needs adjusting. (Serial decoded as `09829` in a
  synthetic test — matches the `SMACIRCLE09829` advertised name, a good sign.)

## Parked

### Firmware OTA — dangerous
`updateStep1-5` flash the controller (`SD_DK`) + board (`SD_BP`); both `.binLB` blobs are in
the APK assets. Fully reproducible but HIGH brick risk, no recovery story. Power-user tool
only — never in the end-user app.

### Password change  *(qt_app)*
`buildPasswordChange` exists. Recovery if forgotten = hold throttle+brake at power-on → resets
to `0000`. Parked by decision; low value, easy to lock yourself out.

## Known future work

- C041 protocol support in the Qt app (already in Python `protocol.py`) — unlocks the non-M0
  device path above.
- Optional "lock on disconnect" preference (disconnect currently leaves the scooter as-is, by
  request).

## Done

- Reverse-engineered the M0 protocol; proven on hardware (handshake → unlock → ride). No
  server, account, or activation needed.
- Python client: scan, `0000` handshake, unlock, gear/light/cruise, live telemetry, plus
  `ver` / `sn` / `reset` commands and handshake-result printing.
- Qt app: battery/speed dashboard; status (lock / NORMAL↔SPORT / light / cruise / trip /
  total / fault); controls (unlock/lock, mode, light, cruise, reset, connect, disconnect
  without locking); device-info card (serial + controller/BLE firmware); real handshake
  detection with a wrong-password prompt; indeterminate activity bar while busy.
- Honest UI — every readout shows "—" until live telemetry arrives (`hasData`).
- Diagnosed "won't go" as non-zero-start (kick-to-start), not a lock.
- App icon (open padlock) — Android mipmaps + Windows exe icon + window icon. MIT LICENSE.
  Minimal `ble_client/examples/unlock.py`.
- Version stamped from `git describe` (Android versionName/Code + header label).
- Android + Windows release CI (`android.yml`, `windows.yml`), Qt cached between runs.
  `v0.1.1` published — icon'd, version-stamped APK + portable Windows zip; installs and
  launches on a real Android phone.
- Distinct release naming — artifacts and the desktop exe are `smacircle-s1-revival.*`
  (was `SmacircleS1*`); on-device app name is "Smacircle S1 freed", set apart from the
  vendor app. Package id `eu.danube.smacircle` unchanged (updates still install in place).
- Error toasts — transient snackbar over the status line (red for errors, neutral for
  confirmations), driven by a `notify` signal on `BleController`: scan/BLE errors, lost
  link (vs. a calm "Disconnected" on user disconnect), wrong password, and unlock / lock /
  mileage-reset confirmations.
