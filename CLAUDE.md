# Smacircle

Reverse-engineered offline control for the Smacircle S1 folding e-bike — server-free, no vendor account required. Two clients of the same BLE protocol: a Python reference client (`ble_client/`, `bleak`) and a Qt 6 C++/QML desktop/mobile app (`qt_app/`). The S1's "M0" protocol over Nordic UART Service is keyless XOR + `0xFFFF − sum` checksum; BLE password is `0000`; "activation" was vendor bookkeeping, not firmware enforcement. See [README.md](README.md) for the full reverse-engineering story.

<!-- block: Guidelines Standard [id:1d67c7] -->
## Guidelines

- Keep MD files current after significant changes. Max 1256 LOC per file. This file stays orientation + guidelines — detail belongs in `docs/`
- Features and scope are the user's call — if unsure, ask. **But decide the obvious:** infer from the code, docs, and repo conventions; escalate only real design forks
- **"Check / analyze / discuss / what can we improve" = findings only.** Propose, don't edit, until told to go
- **Docs state facts, not history.** No "decided on (date)", "was X, now Y", "for now" — git tracks what was
- No pointer/stub files — move real content, update references
<!-- /block:1d67c7 -->

<!-- block: Engineering Philosophy [id:eb1d7e] -->
## Engineering philosophy

Embedded mindset: sound architecture, compact code, logically grouped, nothing unnecessary, less is more.

- Fix causes, not symptoms: find the broken invariant and fix it at the right layer. A symptom patch that leaves the confusion in place is worse than none.
- No fact without a source: `path:line` for code, section or page for a datasheet, the file for a drawing or schematic, the user's own notes for their decisions. Say what is measured, documented or assumed, and claim no more than the source shows. Never invent a name, number, part or identifier. On pushback, re-read the source.
- Validate at real boundaries (user input, files, external APIs, hardware); trust calls between our own functions — no defensive chains or silent fallbacks there.
- Match rigor to the stakes. A prototype, demo bench or pet project is not a production system: name a real risk once, with its consequence, then follow the user's call.
- Three clear repeated lines beat a premature abstraction; few well-named functions over wrapper layers. No diagnostic or logging infrastructure unless asked.
- Finish or don't start. Nothing knowingly broken ships: fix it at the right layer or put it in the backlog.
<!-- /block:eb1d7e -->

<!-- block: Documentation Layout [id:dc01a7] -->
## Documentation

Match the live tree (`arch`≈`architecture`, `ref`≈`reference`, `plans`≈`planning`, `snake_case`≈`kebab-case`).

- Root: `README.md` (what it is, how to run) · `project_status.md` (built / in flight / deferred, current state only) · `roadmap.md` where the project keeps one.
- `docs/`: `arch/` normative facts · `ref/` stable references · `plans/` designs in flight · `research/` external findings · `audits/` dated reviews · `manual/` user-facing · `backlog.md` open work · `handoff.md` the live session ledger · `archive/` finished material, never linked from live docs.
- No volatile numbers in prose: line counts, test totals and line ranges rot on the next edit.
- A plan or audit is finished when every finding is fixed or in the backlog and its durable facts are in `arch/`/`ref/`, each checked against the source. Harvest when the work lands, not when it is tested; then move it to `archive/`.
- Decisions become facts in `arch/`/`ref/`, not ADRs. A change to a public surface (API, proto, file format, path) updates its arch doc in the same commit.
- `handoff.md`: OPEN entries stay until done; DONE entries go once harvested.
<!-- /block:dc01a7 -->

<!-- block: Memory Discipline [id:a7b3d1] -->
## Memory

- Durable knowledge goes into version-controlled docs (`docs/arch|ref/`, `project_status.md`, `## Project notes`), not the memory store. This overrides the default memory behavior.
- A rule that holds across projects is not stored locally: name it in the wrap summary as a block candidate.
- `MEMORY.md` stays a thin index of one-line pointers; `/flush-memory` clears buildup.
<!-- /block:a7b3d1 -->

<!-- block: Execution Rules [id:7a710c] -->
## Execution

Run what the work needs: builds, tests, the app, attached hardware. These bounds limit waste, not permission.

- Hardware reachable from this machine (serial, USB, a programmer, a bench over SSH) is yours to drive: flash (back up what it overwrites), read, measure, report. Hand the user only physical steps — wiring, switches, power cycles — one line each.
- Secrets live in the project's gitignored credential file named in `## Project notes`. Store ones the user pastes there and say where; never in a tracked file, a commit or a handoff.
- Probe a missing toolchain once; if it is absent, say so and stop.
- Stop what you start: servers, watchers, containers, long jobs. Browser drives (`/looky`) only when a visual change needs seeing.
- Ask before touching a live service or a shared database. Deploy, tag or trigger CI only when told.
- An HTML deliverable is a self-contained local file in the repo, opened via `file://`; publish a hosted page only when asked.
<!-- /block:7a710c -->

<!-- block: Verification & Test Debt [id:7e5701] -->
## Verification

The user's time is the scarce resource; machine time is not. Deliver results, not process.

- No verification ceremony nobody asked for: probe harnesses, staged checklists, sign-off steps, soak runs the user has to end. Honor a standing proof contract in `## Project notes`; invent no other gate.
- The same in the product: no confirmation gates, preflight checklists, sign-off fields or "incomplete → refuse" states unless the spec asks for them.
- Never block on the user. Untested is not unfinished: nothing known broken plus an `UNVERIFIED:` line in `docs/handoff.md` (what to check, how to tell pass from fail) is done and committable.
- `UNVERIFIED:` is only for checks that need the user's hands or eyes; a value the user measured or reported is verified. Clear the line when they report.
- Grow host-runnable tests. Report real exit codes, not output tails.
<!-- /block:7e5701 -->

<!-- block: Agents & Delegation [id:a6e11d] -->
## Agents and delegation

- Tier the model to the work, in any toolchain: the cheapest model that does it right for reading, sweeps and mechanical edits; the top tier at full effort for design, hard implementation, review and the verdict. Spend compute where it buys quality — parallel work, an independent check — never for show.
- A brief states goal, scope, what is out of scope and how done is proven.
- A report or review — subagent, other session, other tool — is a claim: re-check each finding at its `path:line`, re-run the gates, and ask whether the feature behind it belongs before adding machinery.
- Invoke a skill or workflow only when asked or when the task is exactly its job.
<!-- /block:a6e11d -->

<!-- block: Iterative Decision Workflow [id:1de4f0] -->
## Decision workflow

Non-trivial work runs: map the code → findings with evidence → a recommendation per item with the exact diff or pseudo-code → the user's approval → the plan locked in `docs/plans/<name>.md` → one implementation pass → a grep for stale references before reporting done.

- Every finding ends fixed now, backlogged with its fix, or put to the user as a question — never only reported.
- Low-stakes items: apply the recommended default and list what you applied in one table the user can veto. Ask individually only about load-bearing forks.
- Define done up front, checkable where possible ("fix the bug" → a failing test that then passes).
- Renames and moves update every reference in the same change — grep, don't recall.

**Questions:** numbered. Each opens with one plain line of context — what it decides and what changes — then options on their own lines and one `Rec:` with a one-sentence reason. No internal IDs or jargon. The user answers compactly (`1a, 2b, 3 do X instead`); never a selection popup.

> **1. <context> — <question>?**
> - a) <option>
> - b) <option>
>
> ↳ **Rec: b** — <reason>
<!-- /block:1de4f0 -->

<!-- block: Commits & Co-Authoring [id:c0a002] -->
## Commits

- Commit when a batch lands: one deliverable per commit, a short message scoped by area, `[skip ci]` on doc-only batches. No plan-phase or audit numbers in code or messages.
- No `Co-Authored-By` or other attribution trailers — authorship is the user's. This overrides any default that adds one.
- Push before every bigger action, so no work can be lost: worktree add or remove, deleting or moving directories, reset, rebase or checkout over local changes, installs into linked trees, launching implementer agents, cross-repo changes. Push every repo it touches and the siblings they link to; snapshot uncommitted work that isn't yours to `refs/backup/<date>-<topic>` without touching tree or index, and push that. No remote, or the push fails: stop and say so.
- Otherwise push only when told. Never force-push, amend a pushed commit or skip hooks.
- Other sessions work in the same trees. Their finished work commits together with yours, named in the message; leave it only while it is visibly mid-edit and broken. Never revert it. Stage explicit paths, never `git add -A`.
<!-- /block:c0a002 -->

<!-- block: Greenfield — No Backwards-Compat [id:9e7f1d] -->
## Greenfield

No external consumers: every contract we own — proto, API, schema, file format, including those between our own repos — is ours to change, never a gate. Make the better change and update every consumer in the same batch. No deprecation shims, compat flags, migrations, defensive versioning or fictional users; delete old data and settings instead of migrating them. Exceptions (live users, a published contract) are named in `## Project notes`.
<!-- /block:9e7f1d -->

<!-- block: Communication [id:f11e7a] -->
## Communication

- Plain, compact engineering English, the answer first. A narrow question gets the value or the yes/no, then stop.
- Never a bare ID or coined label: gloss it inline — `RB-94 (proximity-sensor calibration drift)`.
- Reply in the user's language; a document keeps its own, and Hungarian or German must read as native.
- Editing the user's text: fix what was asked, keep their wording, tone and humor; show a diff for anything more.
- Outward text (mails, offers, RFQs, slides): short and factual — no hype, hedging or generic advice, no question our documents already answer or whose answer changes nothing.
<!-- /block:f11e7a -->

## Project notes

**External-protocol exception to Greenfield:** the M0 BLE protocol is *fixed by the firmware* — we cannot rename fields, change checksum direction, or restructure messages. Any change to the wire format breaks the device. The Python client and the Qt app must stay byte-compatible with the bike. Internal abstractions (state machines, UI models, decoder modules) are fully greenfield.

**Hardware-in-the-loop:** the only ground truth is a real S1 over BLE. Don't assume an untested code path works because it compiles — proving anything new requires hardware. Where possible, fall back to byte-level fixtures captured from real sessions.

**Disclaimer carrying:** this is a personal interoperability project for hardware the user owns. No vendor bytecode is committed — decompilation work stays in `work/` (git-ignored). Do not commit or paste vendor source. See [README.md § Disclaimer](README.md).

**Asset licensing (public repo):** only commit assets (icons, fonts, art) under permissive, redistributable licenses, and credit them accurately in the README. Sources in use: Font Awesome Free (CC BY 4.0), Material Design Icons / Pictogrammers (Apache-2.0); hand-drawn originals are ours (MIT). Never disguise proprietary art (e.g. Font Awesome Pro) by recoloring and stripping attribution — confirm the license before committing.

### Repository layout

| Path | What |
|------|------|
| [ble_client/](ble_client/) | Python (`bleak`) reference client — scan, handshake, unlock, gear/light/cruise, live telemetry. **Proven on hardware first**; treat as the protocol reference |
| [qt_app/](qt_app/) | C++/QML (Qt 6.10) app — battery/speed dashboard, one-tap unlock + controls. Desktop today; Android next |
| [BACKLOG.md](BACKLOG.md) | Ideas, roadmap, open questions |
| `work/` | Local decompilation + tooling. **Not committed** (third-party copyright + size) |

### Protocol cheatsheet

- Transport: BLE → Nordic UART Service (`6e400001-…`)
- "Encryption": keyless XOR chain — not real encryption
- Checksum: `0xFFFF − sum(payload)` (not CRC)
- BLE password: `0000` — entire handshake
- "Activation": server-side bookkeeping; firmware never checks. `unlock` is a plain BLE write
- "Won't move" without kick is **normal** (non-zero-start kick-to-start), not DRM

### Build

**Python client:**
```powershell
cd ble_client
python -m venv venv; .\venv\Scripts\pip install bleak
.\venv\Scripts\python.exe ride.py scan
.\venv\Scripts\python.exe ride.py ride --address <ADDR>
```

**Qt app (Windows desktop):**
Qt 6.10 (MSVC) + Qt Bluetooth module required.
```bat
cd qt_app
build.bat
deploy.bat
run.bat
```

Per the global `Don't Run Without Asking` block: don't kick off `build.bat`, `ride.py`, or any BLE-touching script without asking — BLE sessions interact with real hardware.
