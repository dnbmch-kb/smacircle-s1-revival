# Qt app — build & QML/CI notes

Normative constraints for building and laying out the Qt 6.10 app (`qt_app/`) and cutting
its releases. These are load-bearing — the alternatives listed broke real builds.

## QML layout (this Qt's `QtQuick.Layouts` is fussy)

- The Mode / Light / Cruise / Reset control buttons use **anchored halves** inside a plain
  `Item` (left→horizontalCenter, horizontalCenter→right). Do **not** convert them to
  `Layout.fillWidth` + `Layout.preferredWidth`: each `fillWidth` item grabs the whole surplus
  and overflows the window.
- Never bind a child's `Layout` size hint to its **containing layout's** width — it causes
  full-layout thrash on relayout (e.g. connect/demo flipping many `visible` properties at once).
- `GridLayout.uniformCellSizes` is **not exposed** by the deployed `QtQuick.Layouts` module —
  using it makes the QML fail to load.

## Build toolchain

Build recipe is encoded in [build.bat](../../qt_app/build.bat): MSVC `vcvars64` (BuildTools
2022) + Qt 6.10.1 `msvc2022_64` + Qt's bundled CMake and Ninja, configured with
`-DCMAKE_PREFIX_PATH` pointing at the Qt kit. The Qt **Bluetooth** module is added to the kit
via `aqt --noarchives`. `build-demo.bat` configures `-DSMACIRCLE_DEMO=ON` into `build-demo/`
for the no-hardware demo; that sim code is `#ifdef SMACIRCLE_DEMO` and compiled out of releases.

## Release CI (`.github/workflows/{android,windows}.yml`, tag `v*` → GitHub Release)

- `androiddeployqt` downloads gradle and sometimes hits a transient **HTTP 502**, failing the
  build. Not a code bug — re-run the failed job (`gh run rerun <id> --failed`); watch with
  `gh run watch <id> --exit-status`.
- `Qt6::Svg` (needed for QML `Image` SVG icons) is in the aqt **base** — it builds in CI with
  no extra `-m` module.
- Never `[skip ci]` the commit a release **tag** points to — GitHub skips the whole release
  build (this has cost a re-tag).
- The APK is **ephemeral-signed** until the `ANDROID_KEYSTORE_*` repo secrets exist, so in-place
  updates require an uninstall first. Add the keystore before the next tag.
