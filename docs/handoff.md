# Handoff log

Newest on top. Open entries only; a finished one is harvested and deleted.

## OPEN · 2026-11-07 — curation pass: parked at v0.2.1, the protocol tests land

`v0.2.1` is the only GitHub Release (tag at `0c564be`; Android and Windows CI green there); `main`
holds docs since. The 2026-06-03 entry is harvested: its landmines are
[arch/qt_app_build_notes.md](arch/qt_app_build_notes.md), its open work and hardware questions
[BACKLOG.md](../BACKLOG.md). New: `python -m unittest discover -s ble_client/tests` (4 tests, no bike).

- Operator's: the Android signing keystore and its four repo secrets, before the next tag.
- Desk, no bike: the unified connect button, the device-info popup's version rows, APK slimming
  (BACKLOG.md § Open, § Release polish).
- UNVERIFIED (the bike): what `clearAllMileage` resets; whether Serial and both firmware fields fill
  on a real connect (BACKLOG.md § Open questions).

NEXT-SESSION KICKOFF: "Smacircle S1 app, parked at v0.2.1. Read CLAUDE.md, BACKLOG.md § Open.
Desk work that needs no bike: the unified connect/disconnect button (a connection-state enum on
BleController, checked in the demo build). No tag before the keystore exists."
