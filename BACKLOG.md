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

### Probe hidden M0 telemetry: error / warning codes  *(protocol + hardware)*
`M0Protocol` defines two query builders we never ported — and **the vendor app never calls
them either** (no callers anywhere; `parserInfo` has no branch for their replies). They're
dead code in the official app, so the reply format is unknown:

- `getErrorCode()` → frame `A5 5A 04 20 01 1B 02 …` ([M0Protocol.java:164](work/src_1.2.4/sources/com/smacircle/android/ble/M0Protocol.java#L164))
- `getWarningCode()` → frame `A5 5A 04 20 01 1C 02 …` ([M0Protocol.java:171](work/src_1.2.4/sources/com/smacircle/android/ble/M0Protocol.java#L171))

**Why it matters (the C041/S1 "same model" angle):** the M0 status frame is *fully* mapped —
speed, battery%, flags+gear, trip, total ([M0Protocol.java:255-263](work/src_1.2.4/sources/com/smacircle/android/ble/M0Protocol.java#L255-L263), ported in
[protocol.py:126-136](ble_client/protocol.py#L126-L136)). It carries **no voltage, current, ride-time, or fault detail**.
Those fields exist in the shared `BLEInfoBean` ([BLEInfoBean.java:9-31](work/src_1.2.4/sources/com/smacircle/android/ble/BLEInfoBean.java#L9-L31): `voltage`, `current`,
`allTimeH/MIN`, `lockTimeS`, `autoOffTime`, `startPower`, `errCode`, `maxSpeed`) but are set
**only by the C041 parser** ([C041Protocol.java:222-238](work/src_1.2.4/sources/com/smacircle/android/ble/C041Protocol.java#L222-L238)). If C041 and the S1 share the same
controller board, that sensor data physically exists on the device — M0 just doesn't surface
it in the status frame. These two opcodes (and possibly an undiscovered voltage/current query)
are the likely path to it. No "busbar current" by that name exists in either protocol; C041's
closest field is a generic pack `current` float.

- **Work:** add `get_error_code()` / `get_warning_code()` to `protocol.py`, fire at the real
  S1, capture raw replies, and reverse the layout from the bytes. Hardware-in-the-loop —
  unprovable offline. Bonus: sweep nearby `0x20/0x01/ex` query opcodes for hidden telemetry.
- ⚠️ Read-only queries, low risk, but only the bike can confirm the reply format.

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
- No-hardware demo mode — `build-demo.bat` (`-DSMACIRCLE_DEMO=ON`) builds a simulated S1: a
  "Try demo" button fakes a connection and streams synthetic telemetry; controls mutate local
  state and fire the toasts. Compiled out of release builds (flag off in CI).
- UI polish — white Font Awesome icons on every control (lock/unlock, rabbit/turtle mode,
  light, cruise, reset, scan, demo, disconnect); device-info moved to an ⓘ popup; equal-width
  control buttons; status rows restyled as labelled value chips. Dashboard screenshot in README.

---

## Sweep 2026-09-07 (agent portfolio sweep)

Machine-gathered by an agent sweep and re-verified against the working tree on 2026-09-07.
**Needs an owner pass** — nothing below has been triaged by the operator. Items already open
above (signing keystore, APK slimming, iOS CI, unified button, multi-device/C041, the
error/warning opcode probe, the two hardware questions) were deliberately **not** restated.

### Drift — docs vs tree

- [docs/handoff.md](docs/handoff.md) § 2026-06-03 heads its change list "**all on `main`, pushed**"
  and its kickoff says "`main` clean, nothing pending". `git log --oneline @{u}..HEAD` → one
  unpushed commit `09d8957`; `git status --short` → ` M CLAUDE.md`, ` M README.md`, `?? docs/arch/`.
  The ledger has described a state the tree does not have since 2026-06-04.
- The Documentation Layout block in [CLAUDE.md](CLAUDE.md) names root `roadmap.md` and
  `project_status.md`. `git ls-files` lists neither — the tracked docs are `BACKLOG.md` and
  `docs/handoff.md`, and `docs/arch/` exists but is untracked. The block's own preamble says the
  live tree wins, so this is a question about the block, not a licence to rename anything.

### Test honesty

- **The repo has no tests and CI has no test step, against a stated byte-compatibility invariant.**
  `git ls-files` contains no test file (every `test_*.py` on disk is inside the gitignored
  `ble_client/venv/`); `grep -n -i test .github/workflows/*.yml` returns only `runs-on: *-latest`
  and an unrelated `SDKM=` line. [CLAUDE.md](CLAUDE.md) § External-protocol exception states the
  hard invariant — "The Python client and the Qt app must stay byte-compatible with the bike" —
  and `ble_client/protocol.py` and `qt_app/protocol.h` are two independent implementations of that
  one wire format with nothing comparing them. The same file's Verification & test debt block says
  "Accumulate host-runnable tests". Toolchain confirmed present today: `python --version` → 3.12.13;
  `C:/Qt/6.10.1/msvc2022_64`, `C:/Qt/Tools/CMake_64/bin/cmake.exe`, `C:/Qt/Tools/Ninja/ninja.exe`
  and `…/BuildTools/VC/Auxiliary/Build/vcvars64.bat` all exist.

### Residency

- `docs/arch/qt_app_build_notes.md` (written 2026-06-04) is **untracked** — `git status --short` →
  `?? docs/arch/`. It is the harvest of the handoff's "Landmines (do NOT undo)" into a normative
  arch doc, and the Documentation Layout block says handoff entries get pruned once harvested.
  One copy, no history, never pushed.
- One commit ahead of `origin`; `gh repo view dnbmch-kb/smacircle-s1-revival --json pushedAt` →
  `2026-06-02T21:52:57Z`, so the remote has never seen `09d8957`.
- This file cites the decompiled vendor sources five times by path
  (`work/src_1.2.4/sources/com/smacircle/android/ble/M0Protocol.java#L164` and four more).
  `work/` is gitignored (.gitignore § "Decompiled original app, tooling, APK") and holds **728 MB**
  on this disk only — every one of those citations is unresolvable from a clone.

### Operator decisions

- **The uncommitted README "Tips" paragraph publishes the unit's BLE address to a public repo.**
  `git diff README.md` adds: "The author's unit advertises as `SMACIRCLE09829` at address
  `C1:1F:F6:43:E3:F3`". `gh repo view dnbmch-kb/smacircle-s1-revival --json visibility` → `PUBLIC`.
  Settle this before the commit, not after.
- **Signing keystore — today's status of the item already open above, not a new item.**
  `gh secret list --repo dnbmch-kb/smacircle-s1-revival` → empty; none of the four
  `ANDROID_KEYSTORE_*` secrets exists. `.github/workflows/android.yml:76` reads them and `:92`
  falls back to an ephemeral key ("Updates will require uninstalling the old app first").
  Creating and storing that credential is the operator's alone; `keytool` is on this box at
  `work/jdk/jdk-21.0.11+10/bin/keytool.exe`.
- The hardware questions and the error/warning opcode probe (both open above) need the physical
  S1 in hand. No offline path exists to either.

### Correction to an earlier sweep claim

- An earlier pass recorded the release-assets claim as UNVERIFIED. Checked on 2026-09-07:
  `gh release view v0.2.1 --repo dnbmch-kb/smacircle-s1-revival --json assets` returns both
  `smacircle-s1-revival.apk` (48,142,871 B) and `smacircle-s1-revival-windows-x64.zip`
  (28,629,637 B), state `uploaded`, not a draft. README and handoff are correct. The APK size also
  corroborates the "~47 MB" in Release polish above.
