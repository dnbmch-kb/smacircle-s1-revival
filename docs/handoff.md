# Handoff log

Newest on top. Operational notes to seed the next session.

## 2026-06-03 — UI overhaul, demo mode, v0.2.1 release

**Shipped:** `v0.2.1` (only release; `v0.2.0` deleted — its binaries embedded Pro icons).
Both assets clean: `smacircle-s1-revival.apk`, `smacircle-s1-revival-windows-x64.zip`.

**What changed (all on `main`, pushed):**
- Distinct release naming — artifacts + desktop exe `smacircle-s1-revival.*`; on-device app name `Smacircle S1 freed`. Package id `eu.danube.smacircle` unchanged.
- Error/confirmation **toasts** — `notify(message, error)` on `BleController`, routed through `setStatus(s, Toast)`; QML snackbar in `Main.qml`. Calm "Disconnected" vs red "Connection lost" via `m_userDisconnect`.
- **No-hardware demo** — `qt_app/build-demo.bat` configures `-DSMACIRCLE_DEMO=ON` into `build-demo/`, builds, deploys, launches. All sim code `#ifdef SMACIRCLE_DEMO` (compiled out of releases). "Try demo" button gated on `ble.demoBuild`.
- **Dashboard polish** — device-info moved to an ⓘ header popup; top status line removed (toasts cover it; the "Ready, kick-start" hint is now an info toast); header title `fillWidth`+`elide`; version moved into the ⓘ popup.
- **White button icons** — `iconSource` (url) property on the `Btn` component renders a white `Image` (needs **`Qt6::Svg`**, added to CMake). Icons in `qt_app/icons/`. State swaps: lock-open/lock (primary), rabbit/turtle (Mode).
- **Popups restyled** — dropped `standardButtons` (system footer was square-cornered + OS-language); custom `Btn`s inside content → fully rounded, matching, English. Status rows → dim uppercase label + tinted **value chip**.
- README dashboard screenshot (`qt_app_0_1.png`, pre-chip capture).
- **Licensing fix** — Mode rabbit/turtle were Font Awesome **Pro** (nulled, no license). Replaced with **Material Design Icons** rabbit/tortoise (Apache-2.0), white, same filenames. Other 10 icons are FA **Free** (CC BY 4.0). README credit corrected.

**Landmines (do NOT undo):**
- Control buttons (Mode/Light/Cruise/Reset) use **anchored halves** inside a plain `Item`. Do **not** "simplify" them to `Layout.fillWidth` + `Layout.preferredWidth` — that overflowed the window in this Qt (each fillWidth item grabbed the full surplus).
- Never bind a child's `Layout` size hint to its **containing layout's** width — caused full-layout thrash on connect.
- `GridLayout.uniformCellSizes` is **not exposed** by the deployed `QtQuick.Layouts` — don't use it.
- Never `[skip ci]` the commit a release **tag** points to — it skips the release build.
- `androiddeployqt` can hit a transient **gradle 502** on CI (it downloads gradle). Not a code bug — just re-run the failed job (`gh run rerun <id> --failed`). `Qt6::Svg` builds fine in CI (it's in the aqt base; no extra `-m` module needed).
- Icons: keep assets permissive (FA Free CC BY, MDI Apache). No FA Pro. Pre-v0.2.1 git **history** still holds the old Pro SVGs — user said leave it (no filter-repo).

**UNVERIFIED:**
- I never ran a local build (per repo rule — user builds). Verified by: user's demo builds + CI `v0.2.1` Android + Windows both green.
- Hardware questions still open: does `clearAllMileage` reset total or trip? Do Serial / Controller FW / Bluetooth FW populate on a real connect? (demo fakes them.)

**Open (top of BACKLOG):**
- **Stable signing keystore** — APK still ephemeral-signed → in-place updates need uninstall first. Add `ANDROID_KEYSTORE_*` secrets **before the next tag**.
- Unified connect/disconnect button; multi-device picker + C041; iOS sim CI; APK slimming (~47 MB); probe hidden M0 error/warning codes (hardware).
- Minor: device-info popup mixes "App version" with device firmware rows.

### NEXT-SESSION KICKOFF
> Smacircle S1 app — `v0.2.1` shipped (icons, toasts, demo mode, UI polish). `main` clean, nothing pending. Top task: **stable Android signing keystore** (add `ANDROID_KEYSTORE_*` secrets) before the next release so updates stop needing a reinstall — walk me through it. Don't build/tag/push without asking. Don't revert the anchored control buttons or the value-chip status rows.
