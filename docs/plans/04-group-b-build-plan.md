# Group B build plan — 14 November 2026

Builds the browser application and the assistant from Shiv's approved design
([design.md](../design/design.md), [requirements.md](../design/requirements.md))
against the backend on `main`.

## 1. Inputs and what each one is used for

| Input | Used for | Not used for |
|---|---|---|
| `origin/shiv` — design documents only, no code | Layout, trust rules, state table, colour tokens, components, keyboard and print behaviour | Its `⟨A⟩` placeholders; they are resolved in section 2 |
| `main` — Group A backend, real Jezero bundle | Every number, geometry, source record and status shown | — |
| `origin/anjo` — an older parallel backend (no reach, no stress, no real sampling sites, 1.6 KB placeholder imagery) | One idea: its deterministic `POST /api/brief` built from the stored plan | Its routing, models, fixtures and data, which `main` supersedes |

The three concept PNGs on `origin/shiv` (7 MB) are not copied into this branch.

## 2. Shiv's open `⟨A⟩` items, resolved against the contract

| Design question | Answer on `main` |
|---|---|
| Field names, plan/dataset identity (Q1–2) | `planId`, `datasetVersion`, `modelVersion`, `inputHash` in every result |
| Plan expiry (Q3) | 128 plans, one hour, in memory. `/api/brief` answers 404 `plan_expired`; the UI shows "This plan has expired" |
| Request order (Q4) | Client sends `requestId`; server echoes it; client applies only the latest |
| Units (Q5–7) | Minutes, metres, degrees, m/min. Reserve is a duration. Slope 5–30°, speed 0–1000 m/min |
| Route modes (Q8) | `shortest` → "Shortest distance"; `slope_penalized` → "Lower slope" |
| Slope statistics (Q9) | Per leg: `maxSlopeDeg`, distance-weighted `meanSlopeDeg`, `ascentM` |
| Margin (Q10) | `marginMin` is returned; never recomputed |
| Legs (Q11) | `outbound` and `return` are separate; they are drawn once when their vertices coincide |
| `over_budget` (Q12) | Geometry and metrics are returned; the result is current |
| `invalid_input` (Q13) | `error.message` names the field; shown under the controls |
| `data_unavailable` (Q14) | 503 on `/api/region` (region) or on one asset (layer) |
| Identical routes (Q15) | Not flagged; the browser compares the two `pathXY` arrays |
| Grid (Q16–19) | 150 × 150 cells of 20 m, origin west/south, row 0 north; `null` elevation and `mask: false` are missing |
| Landmarks (Q20) | Still outstanding on Group A's side; the manifest warning says so and is shown |
| Slope layer (Q21) | A grid of degrees; breaks chosen for display are 5, 10, 15, 20 and stated in the legend |
| Destinations (Q22–25) | Five real Perseverance sampling sites; `manifest.scenario.defaultTargetId` is preselected; text comes from the stop record |
| Rehearsal (Q26–29) | One `POST /api/rehearse` returns both options; `currentXY` is any valid cell; a blocked position is 422 |
| Preset polygon (Q30) | Not supplied. The browser places a 120 m square on the remaining return path and labels it hypothetical |
| Assistant lookup (Q31–32) | `server.evidence.trusted_context`; metric references are `<assessment>.<field>`; allowed numbers are the values in that record |

Two backend features postdate the design and are added to it: the **return
envelope** (`/api/reach`, a map layer) and the **closure stress test**
(`/api/stress`, a table plus map marks).

## 3. Architecture

```
web/ (React 19, TypeScript, Vite, three)          server/
  mission/types.ts   contract types                 assistant.py  build_brief: template first,
  mission/api.ts     fetch + latest-request guard                 optional model, validated
  mission/state.ts   one reducer: inputs, plan,     api.py        POST /api/brief; serves web/dist
                     freshness, playback, scenario  models.py     BriefRequest / BriefResponse
  mission/*.tsx      controls, comparison, strip
  map/               SVG map in local metres, canvas grid layers
  terrain/           three.js heightfield, same marks
  evidence/ assistant/ report/
```

- One `useReducer` holds everything; every view reads the same plan.
- Freshness is one of `none | requesting | current | outdated | failed`. Any
  input change moves `current` to `outdated`; rehearsal, assistant, stress and
  report are disabled unless `current`.
- The 2D map is one SVG whose user units are local metres with north up. Grid
  layers (slope, missing data, return envelope) are painted to a canvas once.
- The 3D view is a 150 × 150 heightfield at 1× vertical scale. Triangles that
  touch a missing cell are omitted. `x → X`, `north → −Z`, `elevation → Y`.
- The browser calculates only: differences between two returned values, the
  playback position along returned vertices, and the scenario inputs it sends
  (`elapsedMin`, default remaining time), which are labelled as inputs.
- Development sample data is detected from the data (`datasetVersion` or a
  source ID beginning `synthetic`), not from a setting.

## 4. Assistant

`POST /api/brief {requestId, planId, selectedRouteMode, question}` →
`{answer, sourceIds, metricRefs, mode}`.

1. Look the plan up through `trusted_context`. Unknown or expired → 404.
2. Classify the question by keyword: route, return, evidence, or unsupported.
3. Build the template answer from stored values only (`mode: "template"`).
4. If `MODEL_API_KEY` is set, ask the model to rephrase from the same facts.
   Accept its answer only if every cited ID exists and every number in the
   prose is one of the stored values; otherwise keep the template.

The key stays on the server. Nothing typed in the box can change a route.

## 5. Build order and verification

| Step | Result | Check |
|---|---|---|
| 1 | `server/assistant.py`, models, route, schema, contract | `pytest server/tests`, `export_schema --check` |
| 2 | Vite scaffold, types, API, reducer | `npm test` (reducer, stale responses, geometry) |
| 3 | Map, controls, comparison, evidence | Browser against the real API |
| 4 | Rehearsal strip, scenario, return options, envelope, stress | Browser |
| 5 | 3D terrain | Browser; WebGL-off path |
| 6 | Assistant panel, report, print styles | Browser |
| 7 | Narrow layout, keyboard, docs | `npm run build`, browser at 390 px |

## 6. Left out

- User-drawn polygons, multiple regions, voice, avatars (design section 16).
- Browser end-to-end test files; the flow is checked by hand in a browser and
  the logic by unit tests.
- A hosted deployment. `web/dist` is served by the API on one origin locally.
- Higher-resolution imagery. The bundle's image is 150 × 150 px (20 m); the
  5 m source exists, but regenerating the bundle is Group A's decision.
