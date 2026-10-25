# Smacircle

Reverse-engineered offline control for the Smacircle S1 folding e-bike — server-free, no vendor account required. Two clients of the same BLE protocol: a Python reference client (`ble_client/`, `bleak`) and a Qt 6 C++/QML desktop/mobile app (`qt_app/`). The S1's "M0" protocol over Nordic UART Service is keyless XOR + `0xFFFF − sum` checksum; BLE password is `0000`; "activation" was vendor bookkeeping, not firmware enforcement. See [README.md](README.md) for the full reverse-engineering story.

<!-- block: Guidelines Standard [id:1d67c7] -->
## Guidelines

- Features and scope are the user's call. **But decide the obvious** from the code, docs and repo conventions; ask only about real design forks.
- **"Check / analyze / discuss / what can we improve" = findings only.** Propose, don't edit, until told to go.
<!-- /block:1d67c7 -->

<!-- block: Engineering Philosophy [id:eb1d7e] -->
## Engineering philosophy

Embedded mindset: sound architecture, compact code, nothing unnecessary — less is more.

- Fix causes, not symptoms: find the broken invariant and fix it at the right layer; a symptom patch that leaves the confusion in place is worse than none.
- Build it right the first time — the real design, not a stopgap with the fix deferred — and finish it: nothing knowingly broken ships; fix it or backlog it.
- No fact without a source (`path:line`, datasheet section, drawing file, the user's notes). Say what is measured, documented or assumed, and claim no more than the source shows; never invent a name, number or part. Agent-written conclusions go stale: grep for newer work before repeating one. On pushback, re-read the source.
- A performance figure an order of magnitude below what the hardware can do is a defect to find, not a result.
- Validate at real boundaries (user input, files, external APIs, hardware); trust our own calls — no defensive chains or silent fallbacks.
- Match rigor to the stakes: a prototype is not production. Name a real risk once, then follow the user's call.
- Three clear repeated lines beat a premature abstraction; few well-named functions over wrapper layers. Build nothing nobody asked for — no logging layers, no tooling for a one-time task.
<!-- /block:eb1d7e -->

<!-- block: Documentation Layout [id:dc01a7] -->
## Documentation

Every doc line costs context in every session that reads it. Write less, prune more.

- **Entry docs stay small:** `CLAUDE.md`, `README.md`, `project_status.md` and `docs/handoff.md` together under ~400 lines, `CLAUDE.md` under 200. They point to detail in `docs/`, never copy it. The handoff holds open entries only, a few lines each; a finished one is harvested and deleted at the next wrap.
- **No doc without a reader.** Extend the doc that owns the topic; no summary, report or session-log files — the reply or the handoff carries those. An MD file past ~500 lines is split or pruned; code splits along real seams, not at a line count.
- Root: `README.md` (what, how to run) · `project_status.md` (current state) · `roadmap.md` if kept. `docs/`: `arch/` facts · `ref/` references · `plans/` in flight · `research/` · `audits/` · `manual/` · `backlog.md` · `handoff.md` · `archive/` (finished, never linked). Match the live tree's spelling.
- Keep docs current after significant changes. They state facts, not history — no "decided on (date)", "was X, now Y", "for now"; git tracks what was — and no volatile numbers, no pointer or stub files.
- A plan or audit is harvested when the work lands, not when it is tested: findings fixed or backlogged, durable facts into `arch/`/`ref/`, checked against the source; then archived. Decisions become facts there, not ADRs. A public-surface change (API, file format, path) updates its arch doc in the same commit.
- Before deleting a backlog or doc claim, try to prove it still holds; most proposed deletions fail that test.
<!-- /block:dc01a7 -->

<!-- block: Memory Discipline [id:a7b3d1] -->
## Memory

- Durable knowledge goes into version-controlled docs, not the memory store — this overrides the default. `MEMORY.md` stays a thin index; `/flush-memory` clears buildup.
- A rule that holds across projects goes into the wrap summary as a block candidate, not into local notes.
- Context is controlled, never auto-compacted: wrap at the right spot, or resume with `/forky` from a new window.
<!-- /block:a7b3d1 -->

<!-- block: Execution Rules [id:7a710c] -->
## Execution

Run what the work needs: builds, tests, the app, attached hardware. These bounds limit waste, not permission.

- Reachable hardware (serial, USB, a programmer, a bench over SSH) is yours to drive: flash (back up only what the repo cannot rebuild — stored settings, calibration, a factory image), read, measure. Fit the configuration to the wiring already there; a reading that contradicts it comes with the one check that decides. Hand the user only physical steps, one line each.
- Secrets live in the gitignored credential file named in `## Project notes`: store ones the user pastes there and say where; never in a tracked file, a commit or a handoff.
- Probe a missing toolchain once; if absent, say so and stop.
- If avoidable, nothing on the user's screen — no window, focus change, input, screenshot or clipboard on the console session. Browsers run headless, and only when a visual change needs seeing (`/looky`); desktop GUIs run in the agent's own RDP session; tests offscreen. One that needs a desktop while none is reachable is listed in the handoff as not run. Use srv-one when it makes sense.
- Stop what you start — servers, watchers, containers, subagents, crons, loops — before reporting done or wrapping.
- A scratch, rehearsal or backup tree you create gets an empty `.parked` file at its top, so scans skip it.
- Ask before touching a live service or shared database. Deploy, tag or release only when told — and ask for it once the work is ready to ship.
- An HTML deliverable is a self-contained file in the repo, opened via `file://`; hosted only when asked.
<!-- /block:7a710c -->

<!-- block: Verification & Test Debt [id:7e5701] -->
## Verification

The user's time is the scarce resource; machine time is not. Deliver results, not process.

- No ceremony nobody asked for — probe harnesses, staged checklists, sign-off steps — and none in the product: no confirmation gates, preflight checklists, sign-off fields or "incomplete → refuse" states unless the spec asks. Honor a standing proof contract in `## Project notes`; invent no other gate.
- Never block on the user. Nothing known broken plus an `UNVERIFIED:` line in `docs/handoff.md` (what to check, how to tell pass from fail) is done and committable. `UNVERIFIED:` is only for checks needing the user's hands or eyes; a value the user measured or reported is verified — clear the line.
- Grow host-runnable tests. Report real exit codes, not output tails.
<!-- /block:7e5701 -->

<!-- block: Agents & Delegation [id:a6e11d] -->
## Agents and delegation

- Tier the model to the work: the cheapest that does it right for reading, sweeps and mechanical edits; the top tier at full effort for design, hard implementation, review and verdicts. Spend compute where it buys quality, never for show.
- A brief states goal, scope, out of scope and how done is proven. A cheap agent driving a browser gets every key, UI string and expected value, and no source.
- Parallel agents never share a writable scratch file; big fan-outs run in waves of under ~25 — more at once trips rate limits.
- A report from an agent, session or tool is a claim: re-check each finding at its `path:line`, re-run the gates, and ask whether the feature behind it belongs before adding machinery.
- Invoke a skill or workflow only when asked or when the task is exactly its job.
<!-- /block:a6e11d -->

<!-- block: Iterative Decision Workflow [id:1de4f0] -->
## Decision workflow

Non-trivial work: map the code → findings with evidence → a recommendation per item with the exact diff → the user's approval → the plan in `docs/plans/<name>.md` → one implementation pass → a grep for stale references.

- Every finding ends fixed, backlogged with its fix, or asked — never only reported. Leftover drift is yours: there is no other lane.
- Low-stakes items: apply the default and list it in one table the user can veto; ask only about load-bearing forks.
- A text change that records landed work — a `CLAUDE.md` invariant line, a tool count, a proof row, a renamed reference, a doc line — is applied with the work and listed for veto in the report; a decision that changes cost, schedule, behaviour or geometry still waits for the user's word.
- An agreed next step is carried out, not re-approved; a concern goes beside the result, not instead of it.
- Define done up front, checkable where possible ("fix the bug" → a failing test that then passes). Renames and moves update every reference in the same change — grep, don't recall.

**Questions:** numbered; each opens with one plain line of what it decides, then options on their own lines and one `Rec:` with its reason. No internal IDs; never a selection popup. The user answers `1a, 2b, 3 do X instead`. An open question waits for its answer — never act on it first — and is restated in full, never pointed at by number.

> **1. <context> — <question>?**
> - a) <option>
> - b) <option>
>
> ↳ **Rec: b** — <reason>
<!-- /block:1de4f0 -->

<!-- block: Commits & Co-Authoring [id:c0a002] -->
## Commits

- Commit when a batch lands: one deliverable per commit, a short message scoped by area. No plan-phase or audit numbers in code or messages. No `Co-Authored-By` or other attribution trailers — authorship is the user's; this overrides any default.
- **Push without asking.** A landed batch goes to the remote once it passes the project's gates — others build from what is pushed. Before any bigger action (deleting or moving directories, reset, rebase, checkout over local changes, worktrees, installs into linked trees, implementer agents, cross-repo changes), push every repo it touches and the siblings they link to; snapshot others' uncommitted work to `refs/backup/<date>-<topic>` without touching tree or index, and push that. A branch whose push is a release, named in `## Project notes`, is pushed only when told — `[skip ci]` does not stop a rig that pulls it.
- `[skip ci]` on every commit by default: free pushing must not load CI. CI runs when the user asks; when a repo's CI has not run for a week of pushes, ask whether to run it.
- No remote: commit locally and say so if the action only adds commits, otherwise stop. A failed push: stop and say so. Never force-push, amend a pushed commit or skip hooks.
- Submodules: fetch them (`git submodule foreach git fetch origin`) and build the push set at push time, never from a list; push each submodule before its parent.
- Other sessions share these trees: their finished work commits with yours, named in the message; leave it only while visibly mid-edit and broken, never revert it. Stage explicit paths, never `git add -A`. Parallel agents in one tree share git's index: each stages its own paths and commits with `git commit -m … -- <paths>`. Announce the paths you claim and go on — a cross-session message can expire undelivered.
<!-- /block:c0a002 -->

<!-- block: Greenfield — No Backwards-Compat [id:9e7f1d] -->
## Greenfield

No external consumers: every contract we own — proto, API, schema, file format, between our own repos too — is ours to change. Make the better change and update every consumer in the same batch: no shims, compat flags, migrations or defensive versioning; delete old data instead of migrating it. Exceptions (live users, a published contract) are named in `## Project notes`.
<!-- /block:9e7f1d -->

<!-- block: Communication [id:f11e7a] -->
## Communication

- Plain, compact engineering English, the answer first. A narrow question gets the value or the yes/no, then stop.
- Never a bare ID or coined label: gloss it inline — `RB-94 (proximity-sensor calibration drift)`.
- Reply in the user's language. A document keeps its own; a new one defaults to English. Hungarian or German must read as native.
- Editing the user's text: fix what was asked, keep their wording and tone; show a diff for anything more.
- Outward text (mails, offers, slides): short and factual — no hype, hedging or generic advice, no question our documents already answer or whose answer changes nothing. Say where a deliverable was saved; never imply it was sent.
- A report to a client states findings over the whole evidence — one figure with its spread, each limit with its cause and whose it is (our software or their hardware) — never a diary of runs or versions; corrections go in the covering mail.
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
