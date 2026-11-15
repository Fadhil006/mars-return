# Plan 06 — Execution plan to win, against the clock

Written Sunday 15 November 2026, 18:00 IST. Status: **plan only, nothing built.**

[Plan 05](05-standout-plan.md) says *what* makes the entry stand out and why (nine-reviewer debate, sources in `05-panel/`). This plan says *what to do, in what order, in which files*, given the time that is actually left.

## 0. The constraint that overrides everything

`docs/submission-checklist.md` records the deadline as **Sunday 15 November 2026, 11:59 p.m. Local Event time — today.** At the time of writing that leaves about six hours. Plan 05 was scoped in days; most of it does not fit.

- **First action, before any code (B1, 5 min):** open the Project Submission Guide and your Local Event page in a normal browser and confirm the deadline, the timezone, and the demo limit (30 s video or 7 slides). If the deadline is later than tonight, use the extended track in section 6 instead of cutting scope.
- Only the last "Submit for Judging" counts and resubmitting is allowed, so **submit a safe version early and improve it**, never the other way round.

## 1. Strategy for six hours

Win on one sharp idea shown clearly, not on breadth. Rivals have more datasets and globes; none pairs loss of contact with the return decision, and none makes the user commit before the answer is shown.

**The one story:** *"The plan says GO with 76 minutes spare. But for 27 of those minutes, base cannot see you. Would you have turned back in time?"*

Build exactly four things, in this order. Each is usable alone, so stopping after any of them still leaves a better entry.

| # | Item | Why it is in | Time | Owner |
|---|---|---|---|---|
| T1 | Assistant stops refusing radiation / safe / hazard questions | A judge's first question currently gets a refusal | 20 min | B3 |
| T2 | Contact with base: viewshed, out-of-contact minutes, a flight rule, amber verdict | The only constraint that binds on this terrain; creates the story | 2 h | A2 + A3, B1 for the UI |
| T3 | "Decide first": hide the answer at the rehearsal pause, 10 s countdown, then reveal | The only feature aimed at the person; frontend only | 45 min | B1 |
| T4 | Proof strip: every number in an assistant answer shown as traced to the planner | Makes the existing number check visible; "AI used best" in one glance | 45 min | B3 |

Everything else in plan 05 is cut tonight: the ribbon gates, the regain-contact field and third rehearsal option, P90 bands, the AI adversary, HiRISE tiles, the descent, CRISM cards, direction-aware time, hosting. Section 6 keeps them in order for later.

## 2. Timeline (IST; shift it if the deadline differs)

| Time | Work | Gate before moving on |
|---|---|---|
| 18:00–18:10 | Confirm deadline and demo rule. Make the repo public; check it in a private window. Choose a `LICENSE`. | Rule confirmed in writing in the checklist |
| 18:10–18:30 | T1 | `pytest server/tests/test_assistant.py` passes |
| 18:30–20:30 | T2 server, then T2 UI | Full `pytest`, `export_schema --check`, `npm run typecheck && npm test && npm run build` pass; Sid plan shows the amber contact verdict in the browser |
| **20:30** | **Safety submission**: push, fill the form, attach a slide deck draft, click "Submit for Judging" | Confirmation banner seen |
| 20:30–21:15 | T3 | Countdown, reveal and "your call vs planner" line work in the browser |
| 21:15–22:00 | T4 | Chips link to metrics; counter reads n/n; a mismatching answer falls back to the template |
| **22:00** | **Feature freeze.** No new code after this, only fixes | All checks green on `main` |
| 22:00–22:45 | Record the 30 s film or finish the 7 slides (section 4). Update README, `docs/demo-script.md`, `docs/validation.md` | Demo link opens in a private window |
| 22:45–23:15 | Final submission (section 5) | Confirmation banner seen |
| 23:15–23:59 | Buffer. Touch nothing unless the submission is broken | — |

**Cut rules:**
- If T2 server is not green by 20:00, ship T1 only in the safety submission and keep going.
- If T2 UI is not working by 20:45, drop T4.
- If anything is red at 22:00, revert to the last green commit. A working smaller entry beats a broken bigger one.

## 3. Work items in detail

### T1 · Assistant answers what judges ask (B3)

**Problem:** `server/assistant.py` `TOPICS` puts `radiation|safe|safety|hazard|dust|…` in the `unsupported` group, checked first, so those questions are refused even when the plan holds a radiation estimate.

**Change:**
- Split the `unsupported` pattern. Keep refusing what the data cannot support: `weather|storm|wind|temperature|medical|health|oxygen|suit|surviv*|die|injur*|life|water|alien*`.
- Move `safe|safety|hazard*|obstacle*` to a new `limits` topic. Its template answers with what the model does and does not cover: slope ceiling, missing-data mask, 20 m resolution, hypothetical inputs, plus the route status and margin from `trusted_context`. It makes no safety claim.
- Move `radiation|dose` to a `radiation` topic that reads the stored per-excursion estimate through `trusted_context` and states its limit (MSL RAD at Gale, an estimate, not a forecast). Check how commit ea4a3e9 stored the radiation figure first; if it is not in the plan record, the answer cites the source record and gives no number.
- `dust` stays unsupported.

**Tests (`server/tests/test_assistant.py`):** one question per topic; assert `supported`, the `metricRefs`, and that no answer contains "safe to" or a number missing from the plan.

### T2 · Contact with base (A2 arithmetic, A3 contract, B1 map)

**Server — new `server/contact.py`:**
- `viewshed(region, base_xy, mast_m, eye_m)` returns a height × width grid of booleans.
  - For each cell, walk the straight line from the base cell to it in steps of half a cell, sampling elevation by bilinear interpolation.
  - The cell is visible if no sample rises above the sight line from `base elevation + mast_m` to `cell elevation + eye_m`.
  - Subtract the curvature drop `d² / (2 · 3 389 500 m)` from the terrain along the line.
  - Missing-data cells are never visible and are never sampled as terrain; a ray that crosses one is treated as blocked.
  - 150 × 150 cells is about 22 000 rays; cache the grid in process memory by `(base cell, mast_m, eye_m)`.
- `contact_metrics(path_xy, visible, manifest, speed)` returns:
  - `outOfContactMin`: total time on out-of-sight cells
  - `longestOutOfContactMin`, with `longestStartM` and `longestEndM` along the leg
  - `inContact`: one boolean per path vertex

**Server — `server/mission.py`:**
- In `_leg`, attach the contact metrics to every `ok` leg.
- In `_assessment`, sum `outOfContactMin`, take the largest `longestOutOfContactMin` across legs, and set `contactStatus` to `"within_rule"` or `"exceeds_rule"` against `maxOutOfContactMin`.
- Do **not** add a new value to `status`. `over_budget`/`ok` keep their meaning, so existing frontend switches and tests keep working. The contact rule is a second, separate verdict.
- `evaluate_plan`, `evaluate_rehearsal` and `evaluate_stress` pick this up through `_leg`/`_assessment` with no further change.

**Contract — `server/models.py` (additive only, `schemaVersion` stays 1):**
- `Scenario`: `mastHeightM` (default 2, range 0–10), `eyeHeightM` (default 1.7), `maxOutOfContactMin` (default 15, range 0–600). All three are hypothetical scenario inputs.
- `Leg`: optional `outOfContactMin`, `longestOutOfContactMin`, `longestStartM`, `longestEndM`, `inContact`.
- `Assessment`: optional `outOfContactMin`, `longestOutOfContactMin`, `contactStatus`.
- `PlanResponse`: `contact` object with `visible` (grid of 0/1), `visibleFraction`, `mastHeightM`, `eyeHeightM`.
- Bump `modelVersion` to `grid-constant-speed-v2`.
- Then: `python -m server.export_schema`, update `shared/api-contract.md`, regenerate fixtures with `python -m scripts.generate_fixtures`. **A3 and B1 both approve** before the frontend consumes it.
- `server/evidence.py`: no change needed if the new fields sit inside the stored assessment; confirm `trusted_context` returns them, and add them to `FIELDS` in `assistant.py` so answers may cite them.
- `server/api.py`: add a limitation line next to the existing ones: line of sight is geometric on a 20 m DEM, with no antenna pattern, relay or diffraction.

**Tests — new `server/tests/test_contact.py`:**
- flat synthetic terrain: every cell visible, zero minutes out of contact
- a synthetic ridge between base and target: cells behind it are not visible; the leg's out-of-contact minutes equal blind length ÷ speed
- raising the mast never reduces the visible set
- the rule flips at the threshold exactly (`==` passes, just above fails)
- a missing-data cell on the ray blocks it
- API round trip: `/api/plan` returns the `contact` grid with the manifest's dimensions

**Validation:** add a "Contact" section to `scripts/validate_demo.py` output and `docs/validation.md`: visible fraction, and for each of the five stops the out-of-contact and longest-stretch minutes. These server numbers replace the reviewer's rough ones (26 %, 73 %, 805 m, 27 min) everywhere.

**UI (B1; B2 if time):**
- `web/src/mission/types.ts`: the new fields.
- `web/src/map/layers.ts` + `MissionMap.tsx`: a new `contact` layer, on by default once a plan exists. It draws a cool grey wash over cells where `visible` is 0, using the server grid. Add a legend entry "Base cannot see here (hypothetical 2 m mast)".
- Route line: dashed on segments where `inContact` is false.
- `web/src/mission/RouteComparison.tsx`: a row "Out of contact" (total, and longest stretch), and an amber badge "Exceeds contact rule" when `contactStatus` says so.
- `web/src/App.tsx`: a one-sentence verdict banner above the map, built only from server fields. Example shape: "Within time budget · out of contact for N min (rule: 15)". Rounded to whole minutes.
- `MissionControls.tsx`: `maxOutOfContactMin` as an assumption row, labelled hypothetical.
- `MissionReport.tsx`: the same two rows.
- 3D (`TerrainView.tsx`): only if time remains, tint blind cells in the terrain material from the same grid. Skip otherwise; the 2D map carries the film.

### T3 · Decide first (B1, frontend only)

- `web/src/mission/state.ts`: add `call: "return" | "continue" | null` and `revealed: boolean`.
  - On "Request return options", fire the request as now but show a choice panel instead of the results: **Return now / Continue to the stop**, with a 10 s countdown.
  - A click, or the countdown ending (recorded as "no call made"), sets `revealed`.
- `RehearsalStrip.tsx` / `RouteComparison.tsx`: after the reveal, show the server's two options as today, plus one line comparing the user's call with the planner's result. Use only server statuses: for example "You chose to continue. The planner shows that option over budget by N min."
- No verdict about the user beyond that line; no score. A "Skip, show results" link keeps it accessible and keeps the demo script flexible.
- Un-hide the rehearsal strip (hidden in 3fe8fb9) so the feature is reachable.
- Tests (`web/tests`): reducer tests for the three paths (click, timeout, skip) and that results never render before `revealed`.

### T4 · Proof strip (B3)

- `server/assistant.py`: alongside `metricRefs`, return `tracedNumbers`: for each numeric token in the final answer, the token and the `metricRef` or input name it matched. `_consistent()` already finds the match; return it instead of discarding it. An answer with any unmatched number is still rejected and replaced by the template, as now.
- `server/models.py` `BriefResponse`: optional `tracedNumbers`; regenerate the schema and contract.
- `web/src/assistant/MissionAssistant.tsx`: render each traced number as a chip; clicking sets `highlight` to its ref (the mechanism already exists). Under the answer: "n of n numbers traced to planner output".
- Template answers get the same strip, so the feature shows with no API key.
- Cut for tonight: the staged "rejected answer" button. Describe the rejection behaviour on a slide instead, citing the test that proves it.
- Tests: every number in a template answer is traced; a fabricated number makes the model answer fall back.

## 4. The demo

Pick one format at 22:00 based on what works on screen.

**Option A — 30 s film** (screen capture at 1600×1000, burned-in subtitles, no voice needed):

| Time | Shot |
|---|---|
| 0–5 s | Title card: "On Mars, plan the way back first." Then the map with Sid selected, route drawn, banner "Within time budget" |
| 5–12 s | Contact layer fades in; the valley goes grey; banner adds "out of contact for N min"; badge turns amber |
| 12–19 s | Rehearsal paused mid-route. "Return now / Continue?" with the countdown running |
| 19–25 s | Reveal: both options with their margins; then the assistant answer with "n of n numbers traced to planner output" |
| 25–30 s | End card: positioning line, missions used, "Base and scenario are hypothetical" |

**Option B — 7 slides** (safer if recording goes badly; make the draft for the 20:30 safety submission):
1. Title, team, members, challenge
2. The question: "Can we still get back?" and why rivals' answer (a walk-home ring) is not enough
3. Contact with base: screenshot with the grey wash and the amber verdict
4. Decide first: screenshot of the countdown, one line on why (commit before the answer)
5. AI that cannot invent a number: screenshot of the proof strip; note the JPL December 2025 precedent as a comparison, not a claim of equivalence
6. Validity: real CTX terrain, real Perseverance sampling sites, 27-drive check, test counts; what is hypothetical
7. NASA data used, AI-use disclosure, repo link

**Rules for both:** read every number from the screen on the night; keep hypothetical labels in frame; no AI-generated imagery without a watermark; English.

## 5. Submission (B1 drives, one other person watches)

1. `main` is green: `pytest server/tests`, `export_schema --check`, `npm run typecheck && npm test && npm run build`. Record the commands and results in the checklist.
2. Push; open the repo in a private window.
3. README: add the four new features, the contact limitation, and update "Use of AI tools".
4. Rewrite `docs/demo-script.md` to the story in section 1.
5. Form: name, summary (≤ 1500 characters, lead with the positioning line from plan 05), details, NASA data links (MRO CTX via USGS, Mars 2020 localizations and sample inventory, MSL RAD), other data and tools, AI disclosure.
6. Demo link tested in a private window.
7. Tick the two checkboxes, click "Submit for Judging", wait for the banner, screenshot it.

## 6. If there is more time than tonight

Only if the deadline check in section 0 says so, or for a later judging round that allows updates (check the rules; do not assume). Order, from plan 05:

1. Regain-contact field and the third rehearsal option "move to contact, then decide" (multi-source search in `routing.py`).
2. Return ribbon coloured by turn-back margin, with gates and a cuff card.
3. P90 margin band from the 27 real Perseverance drives (`scripts/calibrate_drives.py`).
4. "Orbit said / Rover found" cards (CRISM, after an alignment check); fix Roubion and the generic science question.
5. First impression: HiRISE tiles cached locally, one-row header, larger map, label fixes.
6. AI adversary that picks the event; the rejected-answer demo; free-text flight rules.
7. Public hosting with the model key server-side and rate-limited.
8. Direction-aware walking time.

## 7. Risks

| Risk | Mitigation |
|---|---|
| The server's viewshed gives a much smaller blind stretch than the reviewer's rough script, so the default plan stays green | Check the number first thing in T2. If the Sid route passes a 15 min rule, pick the stop or rule value that the data supports and say what was chosen; do not tune the mast to manufacture a failure |
| Schema change breaks the frontend mid-evening | Additive optional fields only; fixtures regenerated in the same commit; A3 and B1 approve together |
| Viewshed is slow per request | Cache by base and mast; measure once; 22 500 rays of ≤ 300 samples is small |
| Recording fails late | Slides drafted at 20:30 are the fallback |
| Something breaks after freeze | Revert to the last green commit; the 20:30 safety submission already stands |
| Deadline is in a different timezone than assumed | Section 0, first action |

## 8. Not verified

- The deadline, timezone and demo limit: taken from `docs/submission-checklist.md`, not re-read from the official guide today.
- All contact numbers: from a reviewer's scratch script until T2 computes them.
- How the radiation estimate is stored in the plan record (affects T1's radiation answer).
- Time estimates assume the code is written with AI assistance and reviewed by the owner; none has been tested against this team's pace.
