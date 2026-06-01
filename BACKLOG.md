# Smacircle — Backlog

Running list of ideas / improvements for the offline BLE client (`ble_client/`,
Python) and the Qt app (`qt_app/`, C++/QML). Discussion notes, not commitments.

Status key: 🔵 idea · 🟡 planned · 🟢 in progress · ✅ done · ❄️ parked

---

## Open

### 1. 🔵 Unified connect / disconnect button  *(qt_app)*
Merge the top "Scan & Connect" button and the bottom "Disconnect" button into a
single button whose label + action follow the connection state.

- **Why:** less clutter, clearer single point of control.
- **Catch — must stay honest (cf. the `hasData` fix):** connection is really 4
  states, but `BleController` only exposes `scanning` + `connected` today. There
  is a gap during *connecting* (both false) where a naive toggle would flash back
  to "Scan & Connect" mid-connect.
- **Proposed states:**
  - Idle → "Scan & Connect" → `startScan()`
  - Scanning → "Scanning…" (ideally tap-to-cancel via `m_agent->stop()`)
  - Connecting → "Connecting…" (disabled)
  - Connected → "Disconnect" → `disconnectScooter()`
- **Work:** add a small state enum/Q_PROPERTY to `BleController` (backend change,
  not just QML). Low effort.

### 2. 🔵 Multiple devices + non-M0 GATT robustness  *(qt_app, + protocol)*
Current scan = match on name contains `SMACIRCLE` **or** advertises service
`6e400001`, then **auto-connect to the first match** and stop scanning.

- **2a. Multiple Smacircles in range:** picks whichever is seen first
  (non-deterministic) → could bind the wrong unit. No picker, no "remember mine."
  - Fix options: (a) device-list picker (like Qt's heart-rate `DeviceFinder`);
    (b) remember chosen address (e.g. `SMACIRCLE09829`) in `QSettings` and
    auto-reconnect only to that one.
- **2b. Different GATT / protocol:** the Qt app is **M0-only**.
  - If a unit uses another protocol (e.g. **C041**, already ported in Python
    `protocol.py` but not in the Qt app) but still advertises "SMACIRCLE", we
    connect then `createServiceObject(6e400001)` → null → graceful
    "Nordic UART service not found!" but no function.
  - If it advertises neither the name nor `6e400001`, we won't find it at all.
  - Fix: at service discovery, detect which known service is present (NUS/M0 vs
    C041) and select the matching protocol → C++ port of the existing C041 path.
- **Note:** our S1 *does* advertise `6e400001`, so it works today; don't assume
  all units advertise their service UUID — the connect-time service check is the
  reliable gate.
- **Verdict:** fine for *our* scooter now; picker + remembered-device + C041
  fallback needed for "works with any Smacircle."

### 3. 🔵 Surface read-only device info (firmware + serial)  *(qt_app + script)*
Three M0 query commands + their reply parsers exist but we never use them:
- `checkControlVersion()` → type-1 reply; controller FW = decoded bytes 6,7
  (e.g. `8077`).
- `checkBleVersion()` → BLE-module FW (e.g. `0487`).
- `getCardSN()` → `parserBike`: payload bytes 6..end-2 are an ASCII serial
  (matches the advertised `SMACIRCLExxxxx` name).
- **Plan:** query once on connect; show in an Info/About panel (Qt) and add
  `ver` / `sn` REPL commands (Python). Needs small parser additions in
  `protocol.h` / `protocol.py`. Safe, read-only.

### 4. 🟡 Real handshake confirmation + password entry  *(qt_app + script)*
`parserInfo` emits `Hand_Success` / `Hand_Fail` from a short status frame
(byte5==00; byte2==03 → fail). Today both clients just wait ~800 ms and assume
success. Detect the real result → show "wrong password" and offer a password
field, so units whose password was changed off `0000` work too.

### 5. ⚠️ Reset-mileage: fix label + add confirm  *(qt_app, + add to script)*
The Qt "Reset trip" button actually sends `clearAllMileage` (`0xF5 'C' 'L'`),
which most likely clears the **total odometer**, not the trip. Verify on
hardware, relabel ("Reset mileage"), add a confirmation dialog (irreversible).
Not present in the Python script at all yet.

### 6. 🔵 Password change (advanced)  *(qt_app settings)*
`buildPasswordChange` exists. Could expose in a settings screen with strong
warnings. Recovery if forgotten = hold throttle+brake while powering on → resets
to `0000`.

### 7. ❄️ Firmware OTA — PARKED (dangerous)
`updateStep1-5` implement a controller (`SD_DK`) + board (`SD_BP`) flash; both
`.binLB` blobs are in the APK assets (`work/src_*/resources/assets/`). Fully
reproducible from our client, but HIGH brick risk and no recovery story.
Power-user tool only — never in the end-user app.

### 8. 🔵 Quality-of-life
- Qt: keep-screen-on while connected, auto-reconnect to last device, low-battery
  toast, larger touch targets for mobile.
- Script: one-shot `ride.py unlock --address X` (connect→unlock→exit), telemetry
  CSV logging.

---

## Known future work (context)

- 🟡 **Android build** — install Android SDK/NDK/JDK (via Qt Creator), generate
  templates, add BLE permissions to `AndroidManifest.xml`, build APK, sideload to
  mother's (Android 9+) phone. Runtime `QBluetoothPermission` request already in
  code. iOS dropped (signing wall; using an Android phone instead).
- 🔵 **C041 protocol in Qt app** — already in Python `protocol.py`; would unlock
  item 2b.
- 🔵 **Re-lock options** — disconnect currently leaves the scooter as-is (by
  request). Could add an optional "lock on disconnect" preference later.
- 🔵 **Firmware / serial display** — `checkControlVersion` / `checkBleVersion` /
  `getCardSN` commands exist; not surfaced in the UI.

---

## Done

- ✅ Reverse-engineered M0 protocol; proven on hardware (handshake → unlock →
  ride). No server/account/activation needed.
- ✅ Python client (`ble_client/`): scan, handshake, unlock, gear/light/cruise,
  live telemetry.
- ✅ Qt desktop app: battery/speed hero tiles, status (lock/mode/light/cruise/
  trip/total/fault), controls (unlock/lock, NORMAL↔SPORT, light, cruise, reset
  trip, connect, disconnect-without-lock).
- ✅ Honest UI — all readouts show "—" until live telemetry arrives (`hasData`).
- ✅ Diagnosed "won't go" as non-zero-start (kick-to-start), not a lock.
