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
