# Plan 05 — Make MARS RETURN stand out

Date: 15 November 2026. Status: **plan only, nothing built.** Supersedes nothing; it sequences new work on top of plans 03 and 04.

## How this plan was made

Nine adversarial expert reviewers (Claude Opus subagents, each with a persona) used the live app at `http://127.0.0.1:8000/`, read the code and docs, researched online, wrote a critique, then read each other's critiques, attacked the three weakest proposals, defended or dropped their own, and voted. Their full write-ups, including every source URL, are in [`05-panel/`](05-panel/).

| ID | Persona |
|---|---|
| jpl-traverse | JPL surface operations / rover drive planner |
| isro-scientist | ISRO, Chandrayaan-3 / Mangalyaan / sample return |
| eva-human-factors | NASA JSC EVA flight director / human factors |
| planetary-geologist | USGS Astrogeology / Mars 2020 science team |
| viz-ux | Space visualisation designer (Eyes, Trek, Explore with Perseverance) |
| ai-strategist | Applied-AI lead, former Space Apps judge |
| red-team-competitor | Captain of a rival team |
| lunar-artemis | Artemis south-pole EVA planner (Moon) |
| earth-crossdomain | Aviation / mountaineering / wildfire / SAR decision support (Earth) |

Reviewer measurements are scratch scripts, not server output. **Every number quoted below must be recomputed by the server before it appears on screen, in the film or in the pitch.**

## 1. The verdict

The app is honest, well-tested and dull. Four findings drove the whole debate:

1. **The scenario has no tension.** Median slope in the crop is 2.3°; 0.12 % of cells exceed 15°. "Lower slope" differs from "shortest" by about 1.5 % on the Sid route, every stop passes 8/8 stress closures, and the default plan shows a big green "GO +76 min". A tool that always says yes tests nothing. (jpl-traverse, measured.)
2. **The core idea is no longer unique.** 25+ public entries exist for this challenge. ReturnLine ("where the crew can still get home"), LIFELINE (shrinking safe zone, one-tap "Rover fails"), Protikriti (Tobler pace, line of sight, a Perseverance drive benchmark, daylight, walking rings, ~25 datasets) and others already cover walk-home rings, sunset clocks, O2 consumables, light-time, rover photos and cuff cards. Magurin's planner already has an OpenAI agent that edits the plan. (red-team-competitor, from 18 rival READMEs in `05-panel/`.)
3. **The AI is a bolt-on, and it refuses what judges ask first.** The Assistant is a third tab with canned answers. `server/assistant.py` `TOPICS` classifies `radiation|safe|hazard|dust|surviv*` as unsupported, so it refuses radiation even though radiation is now a data layer. (ai-strategist.)
4. **The first screen is a form, not Mars.** It shows a 3×3 km brown square, a two-row header, the map at about 35 % of the width, and "can we still get back?" five clicks deep. The legend hides sites and the scale bar reads "250500". (viz-ux, screenshots in `05-panel/`.) The phone "Loading the region" stall was a headless-browser artefact; a real-time load takes under 4 s.

And one finding turned the debate. **The only constraint that binds on this terrain is contact with base.** A rough viewshed from the hypothetical base (2 m mast) sees about 26 % of the crop. Three of five stops are out of sight. The default Sid route is out of sight for about 73 % of the outbound leg, including one ~805 m (~27 min) blind stretch, yet the app says GO +76 min. (lunar-artemis, nearest-cell viewshed, ignores curvature.) Artemis EVA planning uses "maximum time without line of sight to lander" as a real constraint. All nine reviewers put this first or second.

## 2. Positioning

> **Every team draws the way home. MARS RETURN shows where you lose contact with home, tests whether *you* turn back in time, and its AI may only say numbers that a planner calibrated against Perseverance's real drives has computed.**

Three claims no rival can make together:
- **Contact-aware return**: out-of-contact minutes as a flight rule, plus "move to contact, then decide".
- **Human-in-the-loop AI**: the AI picks the event, the human commits a decision first, the planner reveals the numbers, and the AI debriefs with every number traced (and one wrong number visibly rejected). This is the propose-and-verify pattern JPL used with Claude to plan Perseverance drives in Jezero in December 2025 (anthropic.com/news/claude-on-mars), plus a cognitive-forcing step (Buçinca et al. 2021: committing first reduces over-reliance on AI; explanations alone do not).
- **Validity from real Mars data**: margins carry a band calibrated on 27 consecutive real Perseverance drives, and each science stop shows where an orbital prediction was later checked on the ground.

## 3. What we build (ranked by panel vote, merged)

Effort: S ≤ ½ day, M ≈ 1–2 days, L > 2 days, for one or two people. Owners follow `CONTRIBUTING.md`.

### P0-1 · Contact-aware return (votes: 9/9 in top 2) — A1, A2, A3, B1 · M

**What:** Line of sight from the base becomes a scenario input and a flight rule.

- **Server (A1/A2):**
  - New `server/contact.py`: viewshed from the base cell over the 20 m DEM. Mast height and eye height are labelled hypothetical inputs, with defaults of 2 m and 1.7 m. Include Mars curvature (about 1.3 m at 3 km), and sample along each ray with interpolation rather than the nearest cell.
  - Compute it per request; it is cheap at 150×150. Cache it by base and mast in process memory.
  - Per route, return:
    - `outOfContactMin`: the total time out of sight
    - `longestOutOfContactMin`, with its start and end distance along the route
    - `maxMinFromContact`: the worst point on the route, measured in minutes back to contact (the ETOPS framing)
  - Add a flight rule `maxOutOfContactMin` as a scenario input, hypothetical, default 15 min. Breaking it gives a new status, `contact_rule` (amber), distinct from `over_budget`.
- **Contact field (A2):**
  - Generalise `routing._search`/`return_field` to accept a set of start cells (multi-source Dijkstra).
  - Seed it from every visible cell to get "minutes to regain contact" for every cell.
  - Expose it on `/api/reach` as `regainContactMin`, next to `returnMin`.
- **Rehearsal (A2):** add a third option next to `immediateReturn` and `continueThenReturn`: `moveToContactThenDecide`. It means walking to the nearest visible cell (the "safe haven", after NASA VIPER's parking spots), then returning. Each option reports its own contact metrics.
- **Contract (A3, B1 agree):** update `server/models.py`, regenerate `shared/schema.json` with `python -m server.export_schema`, and update `shared/api-contract.md`. Add a contact section to `docs/validation.md`.
- **Tests:**
  - flat synthetic terrain gives full visibility
  - a synthetic ridge gives a known blind band
  - the multi-source field equals the minimum of the single-source fields
  - the status flips to `contact_rule` exactly at the threshold
  - the Jezero numbers are recorded in `docs/validation-results.json`
- **UI (B1/B2):** a "base can't see here" wash on 2D and 3D, drawn from the server raster and never recomputed in the client. The longest blind stretch gets a bracket labelled with its length and minutes.

**Why it wins:** it creates the missing tension on real terrain, it is a real NASA EVA planning constraint, and Sightline (a rival) shows only a blind fraction, with no clock and no return option. Impact, Validity, Creativity.

### P0-2 · Return ribbon with turn-back gates (votes: 9/9 in top 4) — A2, B1, B2, B3 · M

**What:** one image that answers "can we still get back?".

- **Server (A2):** for each route vertex, return `turnBackMarginMin`, the spare time if the crew turns back here (budget − elapsed − return time from this cell − reserve), plus `inContact`.
  - Mark the **point of no return**: the first vertex where that margin goes negative.
  - Mark three **gates**, each with a latest pass time (the wildfire trigger-point method: Kalogeropoulos 2023, k-PERIL).
  - Under rehearsal, recompute after the event.
- **UI:**
  - Colour the route by `turnBackMarginMin` (green, amber, red) and dash the out-of-contact segments.
  - A pulsing marker shows the point of no return; gate ticks show their clock times.
  - After an event the ribbon recolours.
  - The same ribbon is drawn in 3D.
- **Report (B3):** a printable **cuff card**, one card per gate (time, margin, contact), plus a one-sentence verdict at the top ("Turn back by T+47 or lose contact for 27 min").

### P0-3 · AI loop: adversary → human call → planner → verified debrief (votes: 9/9 in top 3) — B3, A3 · M

All four steps keep the project rule: **the model never computes a route number.**

1. **Fix the refusal bug first (S).** Questions about radiation, safety, hazards and dust should be answered from the data, with stated limits ("the radiation figure is a Gale RAD estimate, not a forecast"), not refused. The truly unsupported topics stay refused (medical, survival odds, live weather). Add tests for each topic.
2. **AI adversary picks the event (M).**
   - Claude, with tool use, calls the real `/api/rehearse`, `/api/reach` and `/api/stress` to look for the cheapest plausible event that breaks the plan: a delay of N minutes inside the blind stretch, a closure, or a lost contact.
   - The server scores every candidate.
   - The output is "3 ways this walk fails", each replayable on the map. The model chooses *inputs* only.
3. **Decide first (S, frontend only, B1).** At the rehearsal pause, hide the server's options and ask **Return / Continue / Move to contact?** with a 10 s countdown. Then reveal the server numbers and say plainly whether the call matched them. Log it, so a user can see their own continuation bias over several runs.
4. **Verified debrief with proof strip (S–M).**
   - Every number in an answer is a chip linked to its `trusted_context` metric ref, with a counter such as "7/7 numbers traced to planner".
   - Extend `_consistent()` to require a ref for every number.
   - A labelled **"Show a rejected answer"** demo button feeds the model a prompt that produces a wrong number, and the UI shows it discarded: "42 min — not in planner output, discarded".
5. **Live-link only: Flight Director (M, after 1–4).** Free-text what-ifs ("what if we lose 30 min at Brac?") and plain-language flight rules ("turn back if margin < 20 min") become typed scenario inputs and constraint JSON, which the server checks PASS/FAIL. The model shows what it understood; the server judges.

**Operations:**
- The model key stays server-side only, through the existing `MODEL_API_KEY` env var, never committed.
- Add a per-IP rate limit and a response cache keyed by plan ID and question.
- When the model is unavailable, the deterministic templates answer, labelled "Standard explanation". Without a key, the adversary falls back to a fixed, documented search over closures and delays.
- Use the current Claude models: Opus 5.5 for the adversary, Sonnet 5.5 or Haiku 5.5 for debriefs if cost matters. Measure latency before the film; nobody has timed a live `/api/plan` round trip yet.

### P0-4 · Margins with a band from real Perseverance drives (votes: 8/9) — A2, A1 · S–M

- **Calibration (A1):** new `scripts/calibrate_drives.py`, built from jpl-traverse's `05-panel` method. It routes the planner between 27 pairs of consecutive Perseverance positions (odometry already in the repo) and writes the ratios of real distance to planned distance to a small tracked file, `data/region/drive-calibration.json`.
  - Measured so far: unbiased overall (4,716 m driven vs 4,659 m planned); p10–p90 0.88–1.29; maximum 1.74.
  - Rover paths are not walking paths; say so.
- **Server (A2):** margins become whole minutes with a P90 value ("+62 min, P90"). This is an empirical quantile; no Monte Carlo and no invented physiology. The return envelope and the out-of-contact minutes use the same band.
- **UI:** "+76.34 min" disappears. An optional 3D "Perseverance as test pilot" replay draws one real drive with the planner's route over it (S, B2).

### P1-5 · "Orbit said / Rover found" science cards (votes: 9/9 in top 5) — A1, B3 · S–M

**Data (A1):**
- **CRISM mineral map** (Parente et al., Zenodo 5575824, CC-BY, 1.4 MB, 36 m). Sample it per stop in `scripts/build_science.py` and store the class plus a confidence in `science-stops.json`.
  - Preliminary sampling: Brac is olivine, high confidence in 6 of 9 pixels; Issole is olivine / olivine+smectite; Rochette, Sid and Roubion show no detection.
  - **Before using it, check the CRISM-to-CTX alignment on one landmark.**
- **What the rover found:** from the PDS Sample Dossier Initial Reports (released 2026-02-13), and for Brac Liu et al. 2022, *Science* (olivine cumulate). A **verdict** per site: confirmed / orbit silent / partial.
- **Claude reads NASA documents offline** and drafts each "Rover found" line with a page citation. A team member approves it and it is stored as data. A test asserts every line has a `sourceId`. This is an honest, visible AI use.
- **Fix Roubion.** Its sample is atmospheric (the first coring attempt failed), so label it honestly or drop it as a science stop. Replace the identical generic `scientificQuestion` on all five sites with one specific question per site.

**Optional (A1, S):** THEMIS thermal inertia (Edwards & Buz 2021, Zenodo 4931348) as a labelled "loose ground" context layer. It adds Mars Odyssey as a mission. Keep it context only; do not use it as a speed penalty.

**Mission count after this:** MRO (CTX terrain, HiRISE image, CRISM minerals), Mars 2020 (sites, traverse, sample reports, drive calibration) and MSL (RAD, labelled as Gale), plus Odyssey if THEMIS lands. Each layer changes a decision or a verdict.

### P1-6 · First impression (votes: 7/9) — B1, B2, A1 · M

- **HiRISE 25 cm Jezero ortho** as the image basemap. The Trek tiles are verified reachable (`JEZ_hirise_soc_006_orthoMosaic_25cm`). Cache the crop's tiles in `scripts/prepare_demo.py` so the demo never depends on Trek; the tiles are ignored by Git.
  - Imagery only: do **not** swap the 3D geometry to the HiRISE DTM, or the display shows scarps the router never saw.
- **3-second context descent** from a labelled Jezero context view (crater rim, delta) into the study box. Keep a permanent locator inset. It falls back to the current view if the context tile fails.
- **Layout:**
  - a one-row header and the map at 65 % of the width or more
  - a one-sentence verdict banner above the map
  - the Rehearse strip visible again, without having to compare routes first (it was hidden in 3fe8fb9)
- **Fixes:**
  - the legend hides Brac and Issole on desktop and four sites on phone
  - the scale bar text "250500"
  - the Sid label clipped off screen
  - the hatched spike artefact at the far 3D edge (likely the missing-data mask being extruded)
  - contours off by default
- **3D polish (B2, ½ day, only after the P0 items):** Mars sky, haze in the sky colour, soft terrain edge, tone mapping, all display-only.

### P2-7 · Direction-aware walking time (defensive; votes 7/9, but every reviewer called it parity, not novelty) — A2 · M

- Tobler's slope-to-speed function times a labelled "suited, Mars-gravity" factor, applied per profile segment, so the return leg can take longer than the outbound.
- This breaks the documented symmetric-edge assumption in `return_field`. Compute the return field over reversed edges, and update the docstring, tests and `docs/validation.md`.
- Do it only after P0. Judges from NASA will ask about it, but Protikriti already has it.

### P2-8 · Report as an EVA "map book" — B3 · M

Traverse map, contact coverage, ribbon and gates, one page per stop with its orbit/rover card, and a flight-rules PASS/FAIL table. Server numbers only; any AI-drafted prose passes the same number check.

## 4. What we will not build (the traps, and why)

| Idea | Why it is cut |
|---|---|
| Sunset / solar-time clock | ISRO's own Mars24 run: Jezero sunset is 18:03–18:31 local solar time, and the sun stays above 15° for ~10 h. A 3 h mid-sol EVA never meets it. Keep it as one label line ("sun at return: not limiting"). Rivals already ship it. |
| O2 / consumables %, metabolic Monte Carlo | No Mars suit exists, so every rate would be invented. On 2.3° terrain O2 is just minutes in another unit. 10 of 18 rival READMEs already have it. |
| Earth light-time countdown | Earth is not in a 3 h walkback loop at 4–24 min delay; the crew-to-base link matters, and P0-1 models it. Rivals have it. At most one caption line. |
| First-person / street-view walk | MarsWay and Protikriti have it; 20 m terrain smears at eye level and it changes no decision. Keep the camera above ~150 m. |
| ML terrain classifier, or AI vision "finds hazards/minerals" | No orbital labels, no way to measure accuracy; CTX cannot resolve rocks or minerals. It would put an unvalidated layer next to real ones. |
| Learned risk score (Skitourenguru-style) | No Mars accident data. Copy the pattern (segment colours, one class), not the ML. |
| HiRISE DTM as 3D geometry | M–L effort, contradicts the 20 m router. Imagery only. |
| "Add 20 more datasets" | Add only layers that change a decision (P1-5), then stop. |
| Live weather from MEDA/REMS | Past point measurements, not forecasts; the MEDA wind sensor stopped around sol 315. Breaks the hypothetical-labelling rule. |
| Solar-storm replay as the headline | RAD is at Gale, not Jezero; Sightline already tells that story. It may appear as an event option in the adversary. |
| Horizon-match localisation | Needs a real helmet camera; a fake input would break the rules. |
| Reinforcement-learning planner | Unverifiable in days; destroys reproducible numbers. |

## 5. The 30-second film

The team's `docs/submission-checklist.md` says: video ≤ 30 s **or** ≤ 7 slides, English or subtitled; going over makes the entry ineligible for Global Awards. **Confirm this against the 2026 Project Submission Guide in a normal browser before recording** (automated retrieval failed TLS verification).

| # | Time | Shot | Needs |
|---|---|---|---|
| 1 | 0–4 s | LRO image of Apollo 14's tracks stopping short of Cone Crater's rim. Caption: *"1971: turned back near the rim. By the clock."* | Public LROC image, cited |
| 2 | 4–8 s | Descent into Jezero over HiRISE. Sid is selected, the route draws, the banner reads **GO** | P1-6 |
| 3 | 8–14 s | The base viewshed washes the valley grey. The banner flips to **AMBER: 27 min out of contact**, and a "move to contact" arrow appears | P0-1, P0-2 |
| 4 | 14–19 s | The walker pauses. The AI adversary injects "contact lost" inside the blind stretch. A 3 s countdown: *Return / Continue / Move to contact?* | P0-3 |
| 5 | 19–25 s | The ribbon recolours and the point of no return drops. The debrief shows a chip strip: **"7/7 numbers traced to planner"**, one discarded wrong number, and the P90 band | P0-2, P0-3, P0-4 |
| 6 | 25–30 s | Brac card: **Orbit: olivine (CRISM, MRO) · Rover: olivine cumulate (Perseverance)**. End title with the positioning line | P1-5 |

**Rules:**
- Hypothetical labels (base, event, rule) stay in frame.
- Scripted camera poses, no cursor hunting, burned-in subtitles.
- Re-read every figure from the server on the day of recording.

**If slides instead (≤ 7):**
1. Title, team and challenge
2. Apollo 14 → the question
3. Contact-aware return, with a screenshot
4. The AI loop diagram
5. Real-data validity: drive calibration, orbit vs rover
6. What is hypothetical and what is not
7. Live link, QR code and data credits

## 6. Sequence

Each phase ends at a gate. Do not start the next phase while a P0 test is failing.

| Phase | Work | Gate |
|---|---|---|
| **1 — Tension** | Assistant refusal fix (P0-3.1); viewshed, contact metrics and multi-source field (P0-1 server); drive calibration script (P0-4); cache the HiRISE tiles | `pytest` passes; `export_schema --check` passes; Jezero contact numbers recorded in `validation-results.json`; the default Sid plan now reads amber |
| **2 — Show it** | Contact wash and ribbon with gates (P0-1 UI, P0-2); P90 display; layout and label fixes (P1-6); rehearsal third option | Every reviewer complaint in §1.4 is visibly closed in a fresh screenshot at 1600×1000 and 390×844 |
| **3 — AI loop** | Decide-first, proof strip and rejected-answer demo, adversary (P0-3.2–4); orbit/rover cards with Claude-drafted, human-approved lines (P1-5) | Each AI number traced in tests; deterministic fallback works with no key; latency measured |
| **4 — Ship** | Public hosting with the key server-side and rate-limited; film and slides; demo-script rewrite; Flight Director free text (P0-3.5) only if phases 1–3 are done | A public link loads on a phone in < 4 s in a private window; the film is ≤ 30 s and checked against the official guide |
| **5 — If time** | Direction-aware time (P2-7), map-book report (P2-8), THEMIS, 3D polish | — |

## 7. Shared-interface changes (need A3 + B1 sign-off)

- `PlanResponse` / `RehearsalResponse`: per-route contact metrics, `turnBackMarginMin` and `inContact` per vertex, point-of-no-return index, gates, P90 fields, new status `contact_rule`, and option `moveToContactThenDecide`.
- `ReachResponse`: `regainContactMin` grid.
- Scenario inputs: `mastHeightM`, `maxOutOfContactMin`, both labelled hypothetical.
- `science-stops.json`: `orbitalPrediction` (class, confidence, sourceId), `roverFinding` (text, sourceId, page), and `verdict`.
- `trusted_context`: exposes the new metrics so the assistant can cite them. The assistant still never computes them.
- New tracked small file: `data/region/drive-calibration.json`.

## 8. Still unverified (check before relying on it)

- The 30 s / 7-slide rule and the 2026 judging criteria wording: read the official guides in a browser.
- The viewshed numbers (26 %, 73 %, 805 m, 27 min) come from a rough nearest-cell scratch script; the server implementation must replace them.
- CRISM-to-CTX alignment: the stop classes are provisional until a landmark check.
- The download path for the Sample Dossier Initial Report PDFs was not found yet.
- Rival features were read from READMEs, not their live sites (`05-panel/round2/red-team-competitor.md`).
- Model latency and cost for the adversary loop are unmeasured.
- The Apollo walkback speed (3.3 km/h) came from a poorly scanned page; re-check it before quoting.
