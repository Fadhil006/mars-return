# Mars excursion planner — consolidated design

Status: design agreed in three review stages, 14 November 2026. **Design approved by the user, 14 November 2026.** Approval covers the design only; items marked `⟨A⟩` remain unverified, and implementation has not been authorized.

Scope: all of Group B — mission planner and 2D map, 3D terrain and route rehearsal, grounded assistant, mission report, and demo.

## 1. Sources and limits

| Document | Status |
|---|---|
| Group B brief (`02-group-b-experience-and-demo.md`, planning draft, 12 November 2026) | Read; main source |
| [requirements.md](requirements.md) (baseline, 13 November 2026) | Read |
| [Concept mockups](concepts/index.html) (three static images) | Read; concept 1 chosen as the basis |
| Shared project plan (`00-martian-map-team-plan.md`) | **Not available** |
| `shared/api-contract.md` | **Not available** |
| Group A plan, fixtures, region bundle | **Not available** |

The team repository (`Fadhil006/mars-return`) is private and could not be read from this machine. Every field name, unit, status value and label that depends on the contract is marked `⟨A⟩` and listed in section 11. None of them is a decision.

Nothing here establishes official event or submission rules.

## 2. Decisions made in review

| Decision | Choice | Decided by |
|---|---|---|
| Structure | One workspace, not separate pages or a wizard | User, stage 1 |
| Layout and style basis | Concept 1: dark, three columns, with unverified details removed | User, stage 1 |
| 2D and 3D | A toggle in the viewing area | User, stage 1 |
| Assistant input | Three starter questions plus free text | Recommendation; user had no preference. Drop the text box if it misbehaves in testing |
| Blocked corridor | One preset polygon per mission, switched on with a tick box | Recommendation, accepted by stage 2 approval |
| Export | Browser print dialog (print or save as PDF) | Recommendation, accepted by stage 2 approval |

## 3. Explicit requirements versus assumptions

| Topic | Explicit in the brief | Assumption or suggestion in this design |
|---|---|---|
| Users | A new visitor completes the flow without coaching; no geographic expertise needed | Primary user is a judge or visitor at the demo; secondary is a teammate presenting. Not real mission operators |
| Layout | One main screen: controls left, map/3D centre, comparison and evidence right; tabs on small screens | Placement of the assistant, rehearsal controls and report |
| Flow | Choose destination → inspect evidence → compare routes → rehearse → change scenario → review return options → export | The assistant is available once a current result exists; it is not a numbered step |
| Controls | Destination, route mode, time budget, slope ceiling, speed, dwell, reserve; advanced ones collapsed | Which are "advanced"; all units; route-mode names |
| Metrics | Distance, travel time estimate, slope statistics, dwell, reserve, remaining margin, with units | Which slope statistics; whether reserve is a time or a percentage |
| Statuses | `no_path`, `over_budget`, `invalid_input`, `data_unavailable` are distinct; identical routes are not an error | How an expired plan is signalled |
| Rehearsal | Shared `currentXY`; blocked-corridor polygon with reset; remaining-time control; immediate return versus continue-then-return | Request shape for return options; who authors the polygon coordinates |
| Assistant | Three starter questions; `build_brief(plan_id, selected_route_mode, question)` → `answer, sourceIds, metricRefs, mode`; labelled deterministic fallback | Free-text input in addition to the starters |
| 3D | Real elevation, 1× vertical scale, holes masked, about 256 × 256 display mesh, one camera mode | Toggle rather than side by side |
| Report | Objective, destination, base, routes, assumptions, metrics, sources, dataset/model versions, limitations, scenario | Export through the print dialog |

### Mockup details that are not requirements

- Not in the brief: "Crew", "Energy reserve", the elevation profile strip, "Camp A", "Mission Control", and the destinations "Layered ridge", "Crater rim" and "Rock outcrop".
- Conflicting units: 6 h in concepts 1 and 2, 3 sols in concept 3. The brief gives no unit.
- Invented science: concept 1's "Why visit this stop?" paragraph has no source.
- "Shorter route" and "Lower-slope route" are plausible mode names but unverified.
- All terrain, routes and values in the images are illustrative.

## 4. Users and problem

A visitor with no planetary-mapping background needs to see that a science stop is worth visiting, that a calculated route gets there and back within a time budget, and what happens to the return margin when one assumption changes.

The app makes Group A's results legible and honest. It produces no scientific numbers of its own.

## 5. Trust rules

These hold on every screen and in every state.

1. **One plan, one dataset.** Map, 3D view, assistant and report all refer to the same active plan ID and dataset version, shown in the mission bar.
2. **Group A owns the numbers.** The browser computes only differences between returned values.
3. **Labelled assumptions.** The base, travel speed, slope limits, budget and every scenario event carry a visible label.
4. **Labelled sample data.** "Development sample data" stays in the mission bar and the report header until real data is connected.
5. **No invented terrain.** Missing elevation is visibly absent in both views.
6. **No stale success.** A failed or blocked request never leaves an earlier successful route displayed as current.
7. **Grounded assistant.** It explains supplied results and evidence, cites them, says when evidence is insufficient, and cannot change inputs, routes or the map.
8. **Honest fallback.** A template answer is never presented as model-generated.
9. **No overclaiming.** No copy claims survival, live weather, discoveries or operational validation.

## 6. Visitor journey

1. **Arrive.** A preloaded mission is shown with the data-status label and dataset version.
2. **Choose a destination** from the map or an equivalent list.
3. **Inspect evidence:** why this stop, its sources, dates, resolution and limitations.
4. **Set assumptions and request routes.** Any change marks existing results outdated.
5. **Compare routes** by returned metrics and margin, and select one.
6. **Rehearse.** Switch to 3D, play along the selected route, and pause at a point.
7. **Change the scenario.** Apply the hypothetical blocked corridor or reduce remaining time.
8. **Review return options:** immediate return versus continue then return.
9. **Ask why.** The assistant explains the current plan with citations.
10. **Export** a mission summary, only when the result is current.

The order is suggested through defaults and hints, not enforced as steps. What blocks an action is result freshness.

## 7. Information architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│ Mission bar: product name · data status · datasetVersion · planId ·   │
│              result freshness (current / updating / outdated)         │
├──────────────┬────────────────────────────────────┬──────────────────┤
│ Mission      │ Viewing area                       │ Right panel       │
│ controls     │  [2D map | 3D terrain]             │  tabs:            │
│  destination │  layers: imagery, slope, stops     │  Routes           │
│  route mode  │  scale, north, bounds              │  Evidence         │
│  time budget │                                    │  Assistant        │
│  ▸ advanced  │                                    │                   │
│  [Request]   │                                    │  [Mission report] │
├──────────────┴────────────────────────────────────┴──────────────────┤
│ Rehearsal strip: play/pause · position scrubber · scenario controls   │
│                  (blocked corridor, remaining time, reset) · return   │
└──────────────────────────────────────────────────────────────────────┘
```

- **Mission bar:** always visible.
- **Viewing area:** 2D/3D toggle with the same route, markers, polygon and current position in both.
- **Right panel:** Evidence opens when a destination is selected; Routes opens when a result arrives.
- **Rehearsal strip:** appears once a current route is selected. Return options show in the Routes tab as a second comparison.
- **Report:** a full-view overlay with a print layout, disabled while results are outdated.

## 8. Screens

### 8.1 Plan and compare

```
MARS / EXCURSION PLANNER  [Development sample data]  Dataset ⟨A⟩ · Plan ⟨A⟩ · ● Current
──────────────────────────────────────────────────────────────────────────────────────
EXCURSION PLAN       │ [2D map | 3D terrain]  [Layers ▾]      N↑ │ [Routes] Evidence Assistant
                     │                                           │
Destination          │   (aligned image, local metres)           │        ◉ ⟨Mode 1⟩  ○ ⟨Mode 2⟩  Diff
 [⟨stop⟩        ▾]   │                                           │ Distance        ⟨A⟩    ⟨A⟩     ⟨A⟩
 Source-backed stop  │   ■ Base · Hypothetical                   │ Travel time est ⟨A⟩    ⟨A⟩     ⟨A⟩
Route mode  ⟨A⟩      │   ● ⟨stop⟩                                │ ⟨slope stats A⟩ …
Time budget ⟨unit A⟩ │   ━━ Outbound   ┅┅ Return                 │ Dwell           …
                     │   "Return follows the outbound path"      │ Reserve         …
▸ Assumptions (4)    │                                           │ Remaining margin…
  slope ceiling      │                                           │
  speed · dwell      │                                           │ ⟨One sentence built from the
  reserve            │   0 ─── ⟨scale A⟩                         │  returned differences only⟩
                     │                                           │
[ Request routes ]   │                                           │ [Rehearse selected route]
                     │                                           │ [Open mission report]
──────────────────────────────────────────────────────────────────────────────────────
REHEARSAL  (available once a current route is selected)
```

### 8.2 Rehearse and change the scenario

```
… mission bar and left column as above; inputs are read-only during rehearsal, with [Edit plan] …
                     │ [2D map | 3D terrain]  Vertical scale 1×  │ [Routes] Evidence Assistant
                     │                                           │
                     │   ◆ Current position                      │ RETURN OPTIONS · Hypothetical scenario
                     │   ▨ Blocked corridor · Hypothetical       │        Return now   Continue, then return
                     │   ━━ travelled   ── remaining             │ Status          ⟨A⟩     ⟨A⟩
                     │                                           │ Travel time est ⟨A⟩     ⟨A⟩
                     │                                           │ Margin against
                     │                                           │ remaining time  ⟨A⟩     ⟨A⟩
──────────────────────────────────────────────────────────────────────────────────────
REHEARSAL  ▶ ❚❚  ├────●──────────┤ ⟨distance⟩ of ⟨total⟩   Playback 1× · presentation speed only
SCENARIO   [ ] Hypothetical corridor blocked    Remaining time [⟨unit A⟩]  (initial budget: ⟨A⟩)
           [ Request return options ]  [ Reset scenario ]
```

### 8.3 Mission report

```
MISSION SUMMARY · ⟨data status⟩ · Dataset ⟨A⟩ · Model ⟨A⟩ · Plan ⟨A⟩
1 Objective            ⟨science narrative agreed with A3⟩
2 Destination and base ⟨stop⟩ · Base (hypothetical)
3 Route(s)             2D map image · selected mode · metrics table
4 Assumptions          every input value, each labelled as an assumption
5 Scenario             only if applied: event, remaining time, both return assessments
6 Sources              title · mission · date · resolution · limitation
7 Limitations          what this does not show
[ Print or save as PDF ]  [ Close ]
```

## 9. Interaction rules

### Destination selection
- Clicking a marker and choosing from the list do the same thing: select the stop, open the Evidence tab, mark any result outdated.
- Evidence text comes only from Group A's evidence records.
- Geological interpretation is labelled separately from measured chemistry. Slope is labelled as derived from elevation.

### Requesting and freshness
- A result is in one of five states: none, requesting, current, outdated, failed.
- Any input change moves "current" to "outdated" at once. The old route is dimmed and labelled "Outdated".
- While not current, Rehearse, Assistant and Report are disabled.
- Each request carries an ID. Only the response matching the latest ID is applied.

### Route comparison
- Two columns plus a difference column computed from returned numbers.
- The summary sentence names only properties that actually improve.
- Outbound and return are drawn as one line where they overlap, with a note.
- Values are rounded for display only.

### Playback
- Play, pause and scrub move one shared position, shown in 2D and 3D.
- Pausing snaps to an actual route point; that coordinate is sent with a scenario request.
- Progress is shown as distance along the route, not a clock. Playback speed is labelled as presentation speed only.

### Scenario and return options
- Ticking the corridor box shows the preset polygon in both views, hatched and tagged "Hypothetical".
- Remaining time is a separate control from the initial budget, and both are shown.
- Changing either scenario control invalidates previous return options and assistant answers.
- "Request return options" asks Group A for both options. Each is shown with its own status and margin.
- "Reset scenario" removes the polygon, clears return options and restores the original plan.
- The marker is never moved to make a result look successful.

### Assistant
- Starter questions: "Why this route?", "Can I still return?", "What evidence supports this destination?"
- Bound to the current plan ID; disabled when results are outdated.
- Answers show source and metric chips that open the Evidence tab or highlight the metric row.
- A badge states whether the answer came from the model or the standard template.
- Authoritative numbers stay in the structured fields. Typing cannot change the map, inputs or routes.

### Export
- Enabled only for a current result.
- Works with no model call.
- Includes the scenario and both return assessments when one is applied.

## 10. States

| State | What the visitor sees | What is blocked |
|---|---|---|
| Initial mission | A preselected destination with its evidence open, the data-status badge, and a prompt to request routes | Rehearse, Assistant, Report |
| Loading | "Requesting routes from the planning service…"; any previous route dimmed and labelled Outdated | Rehearse, Assistant, Report |
| Outdated | "Inputs changed. These results no longer match." with a Request routes button | Rehearse, Assistant, Report |
| Late response | Nothing; a response for an older request is discarded | — |
| `no_path` | "No route was found within the slope ceiling of ⟨value⟩." No route drawn | Rehearse, Report |
| `over_budget` | The route, if returned ⟨A⟩, with "Exceeds the time budget by ⟨value⟩" | Nothing; the result is current |
| `invalid_input` | The offending control highlighted with the service's reason ⟨A⟩ | Rehearse, Assistant, Report |
| `data_unavailable` | "The planning data for this region could not be loaded." with Retry. A missing layer disables only its own toggle | Depends on what is missing |
| Identical routes | "Both modes return the same route for these inputs." One line drawn | Nothing |
| Expired plan ⟨A⟩ | "This plan has expired. Request routes again." No automatic re-request | Rehearse, Assistant, Report |
| Missing terrain | 2D: hatched area labelled "No elevation data". 3D: a visible gap | Nothing |
| Blocked current position | "The current position is inside the blocked corridor. No return route can be calculated from here." | Return options |
| Return option unavailable | That option's card shows its own status; the other is unaffected | — |
| Scenario reset | Polygon removed, return options cleared, original plan restored | — |
| Model timeout or invalid answer | The standard explanation, badged "Standard explanation · AI model unavailable" | Nothing |
| Unsupported question | "The supplied evidence does not cover this." with what it does cover | — |
| WebGL unavailable | 3D toggle disabled: "3D terrain is not available in this browser. The 2D map has the same route and controls." | 3D only |

## 11. Group A dependencies and open items

| Must come from Group A | Can use labelled sample data | Undecided |
|---|---|---|
| Schema, field names, units, status values | Synthetic elevation grid for the 3D viewer | Product name |
| Coordinate and row conventions, landmarks | Fixture plan results for layout and states | Route-mode names |
| Aligned imagery, elevation, missing-data mask | Placeholder evidence records, marked as such | Time-budget and reserve units |
| Destinations and evidence records | A sample blocked polygon | Which slope statistics are returned |
| Route and return-option results, all metrics | | How plan expiry is signalled |
| Dataset and model version strings | | Whether `over_budget` returns geometry |
| Trusted plan lookup for the assistant | | Blocked-polygon coordinates |
| | | Model provider and deployment target |
| | | Actual submission and presentation rules |

**Before implementation planning:** read the shared project plan and `shared/api-contract.md`, then replace or confirm every `⟨A⟩` in this document.

Section 17 restates these dependencies as questions and requests addressed to Group A.

## 12. Layout, keyboard and accessibility

### Desktop
- Three columns from about 1,200 px wide.
- Between roughly 900 and 1,200 px, the left column collapses to a drawer.

### Small screens
- Three tabs: Mission, Map, Results.
- The mission bar condenses to data status and freshness, expanding on tap to show versions.
- The rehearsal strip docks under the Map tab. The report becomes a single column.

### Keyboard
- Tab order: mission bar, controls, viewing area, right panel, rehearsal strip.
- The destination list is the keyboard route to markers (arrow keys and Enter).
- The scrubber is a slider: arrow keys step by route point; Home and End jump to the ends.
- Space toggles play and pause when the strip has focus.
- 3D view: arrow keys orbit, plus and minus zoom, and a Reset view button is always present.
- The report overlay traps focus, closes on Escape and returns focus to its button.

### Accessibility
- Status changes are announced politely; errors are announced immediately.
- The metrics table is the text equivalent of the map and appears in the report.
- Text contrast meets 4.5:1. Route lines and markers have a dark casing to hold 3:1 over imagery.
- Nothing is conveyed by colour alone: line style, hatch and text tags carry the meaning.
- Camera moves are skipped under reduced-motion settings. Playback starts only on a user action.
- Touch targets are at least 44 px.

## 13. Visual direction

Based on concept 1. All values below are proposals for review, not inherited requirements; the brief specifies none of them.

### 13.1 Principles

- **Imagery carries the colour.** Interface surfaces are dark and neutral so the Mars image and terrain are the only warm areas on screen.
- **One colour, one job.** Orange means "primary action" and nothing else. Cyan means "route". Violet means "hypothetical". Status colours never appear on controls.
- **Never colour alone.** Every colour-coded meaning also has a shape, line style, hatch or text tag.
- **Nothing decorative that could be read as data.** No sky, fog, atmosphere, glow, invented shading or textures in the 3D view.

### 13.2 Colour tokens

Contrast ratios are computed (WCAG 2 formula) against the panel surface unless noted.

| Token | Value | Use | Contrast |
|---|---|---|---|
| `surface.app` | `#14171A` | Page background, 3D scene background | — |
| `surface.panel` | `#1B1F23` | Columns, mission bar, rehearsal strip | — |
| `surface.raised` | `#242A30` | Inputs, cards, selected tab, table header | — |
| `border.subtle` | `#333B43` | Dividers only (decorative, 1.5:1) | — |
| `border.control` | `#6B7783` | Input and button outlines | 3.6:1; 3.2:1 on raised |
| `text.primary` | `#EEF1F3` | Body text, values | 14.6:1 |
| `text.secondary` | `#B3BCC4` | Labels, captions | 8.6:1 |
| `text.muted` | `#8D98A3` | Units, helper text, placeholders | 5.7:1; 4.9:1 on raised |
| `action.default` | `#D9622B` | Primary button fill, active tab underline | 4.5:1 as a shape |
| `action.hover` | `#E57A47` | Primary button hover | — |
| `action.text` | `#14171A` | Text on primary buttons | 4.9:1 on `action.default` |
| `focus.ring` | `#FFD166` | Keyboard focus | 11.5:1 |
| `route.line` | `#3DD6E8` | Route lines, position marker ring | 10.3:1 on app |
| `route.casing` | `#0B1114` | Dark outline under every route line and marker | 10.9:1 against the line |
| `status.current` | `#5CC98A` | "Current" | 8.0:1 |
| `status.updating` | `#7FB4FF` | "Updating" | 7.8:1 |
| `status.outdated` | `#E3B341` | "Outdated", "Expired" | 8.5:1 |
| `status.error` | `#FF7B72` | No path, unavailable, invalid | 6.6:1 |
| `hypothetical` | `#C9A0FF` | Hypothetical tag, blocked-corridor hatch, scenario results | 7.9:1 |
| `missing.hatch` | `#7A858F` | "No elevation data" hatch | 4.8:1 on app |
| `badge.sample` | `#EEF1F3` fill, `#14171A` text | "Development sample data" | 15.9:1 |

Notes:

- White text on the orange button reaches only 3.7:1, so button text is dark.
- The sample-data badge is a neutral inverse badge so it cannot be confused with an action, a status or a hypothetical tag.
- Route and hypothetical colours fall to about 1.2–3.2:1 directly on Mars-toned imagery. The dark casing is therefore mandatory, not a style choice. The imagery tones used for this check were estimates; **recheck on A1's actual image** before sign-off.

### 13.3 Slope layer

- A five-step sequential ramp at 60% opacity over the imagery: `#440154`, `#3B528B`, `#21918C`, `#5EC962`, `#FDE725` (low to high). It stays ordered for common colour-vision deficiencies.
- Class breaks and units come from Group A ⟨A⟩. The legend states "Slope, derived from elevation" and shows the breaks.
- Whether cells above the slope ceiling get a distinct treatment depends on what Group A returns ⟨A⟩.
- Cells with no elevation use the missing-data hatch, never a ramp colour.

### 13.4 Typography

| Role | Size / line height | Weight | Use |
|---|---|---|---|
| Product name | 16 / 24, letter-spacing 0.08em, uppercase | 600 | Mission bar |
| Panel heading | 18 / 24 | 600 | "Excursion plan", "Return options" |
| Section label | 12 / 16, letter-spacing 0.06em, uppercase | 600 | Group labels, table headers |
| Body | 14 / 20 | 400 | Controls, evidence text, assistant answers |
| Metric value | 16 / 24, tabular numerals | 500 | Comparison table values |
| Unit and caption | 12 / 16 | 400 | Units, helper text, map legend |
| Identifier | 12 / 16, monospace | 400 | Plan ID, dataset and model versions |

- **Typeface:** Inter for the interface, with its tabular-numeral feature for all numbers; the system monospace for identifiers. Inter is open-licence (SIL OFL) and is bundled with the app so the local backup works offline.
- **Small screens:** body becomes 16 / 24; nothing is set below 12.
- **Evidence and assistant text:** maximum line length of about 70 characters.
- **Units:** always shown, in `text.muted`, separated from the value by a thin space.

### 13.5 Spacing and layout

- **Spacing scale:** 4, 8, 12, 16, 24, 32 px. Panel padding is 16; gaps between control groups are 24; table rows are 32 high.
- **Columns:** left 300 px, right 360 px, centre fluid with a minimum of 480 px.
- **Bars:** mission bar 48 px; rehearsal strip 96 px (playback row and scenario row).
- **Corners:** 4 px on controls and tags, 6 px on panels and cards. Map and 3D canvas are square-cornered.
- **Borders and depth:** 1 px borders; no drop shadows. The report overlay uses a `#0B1114` scrim at 80%.

### 13.6 Components

| Component | Convention |
|---|---|
| Primary button | Orange fill, dark text, 36 px high (44 on touch). One per panel: "Request routes", "Request return options" |
| Secondary button | `border.control` outline, `text.primary` label: "Rehearse selected route", "Reset scenario" |
| Disabled control | 40% opacity plus a visible reason beneath it, such as "Request routes to enable". Never disabled without a reason |
| Input and select | `surface.raised` fill, `border.control` outline, label above, unit inside the right edge |
| Tabs | Text tabs; active tab has `text.primary` and a 2 px orange underline |
| 2D/3D toggle | Two-segment control; the active segment uses `surface.raised` and `text.primary`, not orange |
| Status indicator | 8 px dot plus the word ("Current", "Updating", "Outdated"); the word is always present |
| Tag | 12 px text in a 20 px outlined pill: "Hypothetical" in violet, "Assumption" and "Outdated" in their own colours |
| Comparison table | Label column left-aligned; value columns right-aligned in tabular numerals; difference column in `text.secondary` with an explicit + or − |
| Return-option card | `surface.raised`, violet left edge 3 px, "Hypothetical scenario" tag, status line first, then metrics |
| Banner | Full-width strip inside the affected panel: status colour left edge 3 px, icon, one sentence, one action |
| Citation chip | Outlined pill with a source or metric icon and short title; opens the Evidence tab or highlights the metric row |
| Answer-mode badge | "AI model" or "Standard explanation" in `text.secondary`, above every assistant answer |
| Scrubber | 4 px track; travelled part in `route.line`; 16 px thumb with casing; 44 px hit area |
| Focus | 2 px `focus.ring` outline with a 2 px offset on every interactive element, including map markers and the 3D canvas |

### 13.7 Map and terrain marks

| Mark | 2D | 3D |
|---|---|---|
| Base | 14 px white square with casing, "Base · Hypothetical" label | Same symbol as an upright marker |
| Science stop | 12 px white circle with casing; selected stop gets a cyan ring | Same |
| Current position | 14 px cyan diamond with white centre and casing | Same, always drawn above the surface |
| Outbound | 3 px solid `route.line` over a 6 px casing | Same, with a small display-only offset above the surface |
| Return | Same weight, dashed 8 on / 6 off | Same |
| Travelled part | Full opacity; the remaining part at 55% | Same |
| Outdated route | 35% opacity, dashed casing, "Outdated" label at its midpoint | Same |
| Blocked corridor | Violet 45° hatch, 6 px spacing, 2 px violet outline over a casing, "Hypothetical" label | Draped on the surface with the same hatch |
| No elevation data | Grey 45° hatch in the opposite direction, labelled | A visible gap showing `surface.app` |
| Scale, north, bounds | Scale bar bottom-left, north arrow top-right, 1 px bounds outline | "Vertical scale 1×" label top-right; north indicator |

- **Labels:** 12 px `text.primary` on a `route.casing` plate at 85% opacity so they stay readable on any imagery.
- **3D terrain:** textured with A1's aligned image, one neutral directional light, no exaggeration unless labelled.

### 13.8 Motion

- Panel and tab transitions: 150 ms ease-out. Toggle between 2D and 3D: 200 ms cross-fade.
- No looping or attention-seeking animation. The "Updating" state uses a static label plus a thin indeterminate bar.
- Under reduced-motion settings, all transitions become instant and camera moves are skipped.

### 13.9 Printed report

The report prints in a light theme regardless of the screen theme.

| Element | Value | Contrast on white |
|---|---|---|
| Text | `#1A1D20`, 11 pt body, 9 pt captions | 16.9:1 |
| Secondary text | `#5A636B` | 6.1:1 |
| Route lines | `#006D7A`, solid and dashed | 6.1:1 |
| Hypothetical | `#6B3FB5` hatch and tag | 7.0:1 |

- A4 and Letter, 18 mm margins, tables kept together across page breaks.
- The header on every page carries data status, dataset version, model version and plan ID.

### 13.10 Not yet verified

- Contrast of route, hypothetical and slope colours over the real imagery.
- Legibility of the slope ramp over the real imagery at 60% opacity.
- Frame rate with the hatch and casing treatments on the demo laptop.

## 14. Demo narrative

The brief's two-minute length is an internal target only. No numbers appear here because none are verified.

1. **Problem.** "An explorer has a science goal and a fixed amount of time to get back. Which route, and how much margin?"
2. **Destination.** Select the stop, open its evidence, and point to the source, date and limitation.
3. **Routes.** Request routes, compare the two modes, and read the margin row from the screen.
4. **Terrain.** Switch to 3D at 1× scale, play the rehearsal and pause partway.
5. **Change.** Tick "Hypothetical corridor blocked" and request return options. Show both cards.
6. **Why.** Ask "Can I still return?", then open the cited source from the answer.
7. **Close.** Open the report. State what works, what was measured, and what would need validating.

If the service or model fails live: say so, show the labelled fallback and continue. Do not substitute a recording without announcing it. A2 verifies quantitative claims and A1 verifies data attribution before the pitch.

## 15. Acceptance criteria for the design

- [ ] Every surface shows or inherits the same plan ID and dataset version.
- [ ] No number on any screen is computed in the browser except differences between returned values.
- [ ] Every assumption, the base and every scenario element carries a visible label.
- [ ] Sample data is labelled in the mission bar and the report.
- [ ] Each state in section 10 has defined copy and defined disabled actions.
- [ ] A failed request never leaves an old route shown as current.
- [ ] Missing terrain is visibly absent in both views.
- [ ] The full flow works with a keyboard and without WebGL.
- [ ] The assistant cannot change inputs, routes or the map, and its fallback is labelled.
- [ ] The report exports without a model call and never from an outdated result.
- [ ] Every `⟨A⟩` placeholder is listed as an open dependency, not presented as a decision.
- [ ] No copy claims survival, live weather, discoveries or operational validation.
- [ ] Orange appears only on primary actions; status and hypothetical colours never appear on controls.
- [ ] Every colour-coded meaning also has a shape, line style, hatch or text tag.
- [ ] Text meets 4.5:1 and control outlines and map marks meet 3:1, rechecked on the real imagery.
- [ ] The 3D view contains no decorative element that could be read as terrain data.

## 16. Out of scope

Detailed avatars, first-person controls, voice, whole-planet navigation, multiple regions, user-drawn polygons, accounts, a new database, unrelated chat and decorative transitions.

## 17. Notes for Group A

This section is written to be read on its own. It was drafted without access to the shared project plan or `shared/api-contract.md`, so some questions may already be answered there; if so, a pointer to the relevant section is all we need.

### 17.1 What Group B will and will not do with your data

- **We display, we do not calculate.** Every distance, time, slope figure, margin and status on screen is yours. The only arithmetic in the browser is the difference between two values you returned.
- **We round for display only.** Please return full precision; tell us if any field should be shown at a specific precision.
- **We show your geometry as returned.** Routes are not smoothed, snapped or simplified for analysis. The 3D view lifts lines slightly above the surface for display only.
- **We never fill gaps.** Cells you mark as missing are drawn as hatched (2D) or as a hole (3D).
- **We label what is hypothetical.** The base, travel speed, slope ceiling, budget and scenario events are tagged as assumptions or hypothetical everywhere, including the report.
- **The assistant only explains.** It receives the current plan summary and your evidence records, and it cannot request or alter a route.

### 17.2 Questions we need answered

**Contract and identity**

1. What are the exact field names and types in the plan request and plan result?
2. What are `planId` and `datasetVersion` called and formatted as, and is there a separate model or algorithm version string for the report?
3. Do plans expire? If so, how is that signalled: a status value, an HTTP error, or a timestamp we compare?
4. Should we send a request ID that you echo back, or do we track request order entirely on our side?

**Inputs and units**

5. What unit is the time budget in (minutes, hours, sols)? The earlier mockups disagreed.
6. Is reserve a duration or a percentage, and of what?
7. What are the units and valid ranges for slope ceiling, speed and dwell? We will use your ranges as input limits.
8. What are the route modes, what are their exact identifiers, and what should a visitor see them called?

**Results**

9. Which slope statistics do you return (maximum, mean, share above a threshold)?
10. Is remaining margin returned directly, or are we expected to show budget minus total? We would rather display your value.
11. Are outbound and return legs returned as separate geometries? How do we tell that they are identical?
12. For `over_budget`, do you still return the route geometry and metrics?
13. For `invalid_input`, do you return which field failed and a readable reason?
14. For `data_unavailable`, can we tell a missing layer from a missing region?
15. When both modes give the same route, is that flagged, or do we compare geometries?

**Region and coordinates**

16. What are the origin, extent and cell size of the region in local metres, and which corner is row 0, column 0?
17. What elevation is the stored origin that 3D heights should be measured from?
18. How are missing cells encoded: a mask file, a nodata value, or both?
19. What are the pixel dimensions of the aligned image and the analysis grid? We plan a display mesh of about 256 × 256.
20. Which three landmarks and which elevation difference should we use for the 2D/3D alignment check?
21. Is the slope layer delivered as an image, a grid or class polygons, and what are the class breaks?

**Destinations and evidence**

22. How many destinations are there, and which should be preselected for the initial mission?
23. Does each evidence record carry: title, mission, date, resolution, limitation, and a flag separating geological interpretation from measured chemistry?
24. What are the evidence record IDs? The assistant must cite them exactly.
25. Who writes the short "why this stop matters" text, and is it part of the evidence record?

**Rehearsal and scenario**

26. What does the rehearsal request look like: current position, blocked polygon, remaining time?
27. Does one request return both options (return now; continue, then return), or is it two requests?
28. Should the current position be an exact route vertex, or do you accept any point on the route?
29. What is returned when the current position is inside the blocked polygon?
30. Can you supply one preset blocked polygon per mission, in local metres, that actually intersects the route? We would rather not author one that turns out to be irrelevant.

**Assistant**

31. What does the server-side lookup return for a plan ID, and what are the valid `metricRefs` identifiers?
32. Which values count as "allowed plan values" when we check numbers in generated text?

### 17.3 What we need, by the brief's handoff points

| When | We need from you | We return |
|---|---|---|
| H1 | Schema and synthetic fixtures, including one fixture per status value | Screen needs and a field-mismatch report |
| H3 | Real-data feasibility decision and the crop extent | Confirmation that the crop fits the flow |
| H6 | Region files, missing-data mask, landmarks | 2D/3D alignment check with screenshots |
| H9 | Real plan results and evidence records | Integrated round trip |
| H12 | Rehearsal responses and the preset polygon | End-to-end scenario demo |
| H27 | Final versions and validated numbers | Assistant and report consistency review |
| H30 | Frozen service and data | Frozen submission candidate |

### 17.4 Fixtures that would help most

- One successful two-mode result, and one where both modes are identical.
- One each of `no_path`, `over_budget`, `invalid_input` and `data_unavailable`.
- One expired plan, if plans expire.
- A region bundle with at least one block of missing cells, so the masked state can be designed against real structure.
- One rehearsal response where one return option is feasible and the other is not.

Every fixture should carry a field or filename that marks it as development sample data, so we can drive the on-screen label from the data and not from a setting we might forget to change.

### 17.5 Reviews we will ask you for

- **A1:** landmark and elevation checks in 3D; data attribution in the pitch; contrast of our route and slope colours over the real image.
- **A2:** every quantitative claim in the pitch and report.
- **A3:** the request and result types; independent inspection of assistant answers and citations; the science narrative.

### 17.6 Things that would change our design

Please tell us early if any of these is true, because each one changes a screen:

- More than two route modes, or only one.
- More than one region, or a region much larger than the display mesh assumes.
- Routes that are not simple out-and-back legs (for example, multiple stops).
- A time budget that is not a single number.
- No per-cell missing-data information.
- Return options that cannot both be computed in one interaction.
