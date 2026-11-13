# Validation

Measured evidence that the Group A backend satisfies the contract in
`shared/schema.json`. All numbers below were produced on this machine with the
committed synthetic dataset and are reproducible from a clean checkout.

## 1. Environment

| Item | Value |
| --- | --- |
| Python | CPython 3.14.8 (`.venv`) |
| Platform | Linux |
| Virtualenv | `/home/anjo/Projects/mars-return/.venv` |
| Pinned deps | `requirements.txt` (fastapi 0.162.5, uvicorn 0.54.0, numpy 2.5.4, rasterio 1.5.2, pillow 13.0.0, pydantic 2.14.3, pytest 9.2.0, httpx 0.28.1) |
| Dataset | `data/region/` committed synthetic fallback |
| `datasetVersion` | `jezero-synthetic-2026.11-v1` |
| `modelVersion` | `group-a-1.0.0` |

## 2. Commands

```bash
cd /home/anjo/Projects/mars-return

# 1. Environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Deterministic dataset (already committed; safe to regenerate)
.venv/bin/python server/preprocess.py --synthetic-fallback

# 3. Full test suite
.venv/bin/pytest server/tests -q

# 4. Service smoke test
.venv/bin/uvicorn server.api:app --host 127.0.0.1 --port 8000
```

## 3. Numerical checks and observed results

Full suite: **44 passed, 1 warning**. The single warning is Starlette's
`httpx` deprecation notice from `fastapi.testclient`, not a failure.

```text
$ .venv/bin/pytest server/tests -q
............................................                             [100%]
44 passed, 1 warning in 1.10s
```

Per-file breakdown:

| File | Tests | Covers |
| --- | --- | --- |
| `test_coordinates.py` | 6 | Orientation, pixel centres, round trip, open edges, malformed manifests |
| `test_routing.py` | 13 | Flat ground, wall with gap, disconnection, corner traps, no-data holes, slope ceiling, slope penalty, closures, determinism |
| `test_mission.py` | 11 | 900 m round trip = 90 min, ascent, plane slope, no-path nulls, invalid inputs, rehearsal arithmetic, closure without teleport |
| `test_api.py` | 14 | Region manifest, plan/no-path/invalid, brief from stored plan, missing/stale/expired plans, closures, bounded store, fixture invariants, `data_unavailable` |

### Requirement-to-test matrix

| Requirement | Test(s) |
| --- | --- |
| `row = 0` North, `col = 0` West, East/North positive | `test_pixel_centres_and_orientation` |
| Pixel <-> metric round trip | `test_round_trip_all_cells` |
| Out-of-bounds handled, not clamped | `test_out_of_bounds_returns_none`, `test_pixel_out_of_range_raises` |
| Bounds are outer cell edges | `test_bounds_are_outer_edges` |
| Malformed manifest rejected | `test_malformed_manifest_rejected` |
| 8-neighbour A*, unsmoothed unit steps | `test_flat_ground_shortest`, `test_same_cell_is_zero_distance` |
| Wall with a single gap | `test_wall_with_one_gap` |
| Fully disconnected region -> `no_path` | `test_fully_disconnected_region` |
| No diagonal corner cutting | `test_diagonal_corner_cutting_forbidden` |
| No-data holes avoided | `test_no_data_hole_is_avoided` |
| Slope ceiling enforced (5–30 deg) | `test_max_slope_ceiling` |
| `slope_penalized` prefers gentler path | `test_slope_penalized_prefers_gentler_path` |
| Blocked polygons conservative, detours work | `test_blocked_polygon_wall_and_gap`, `test_blocked_polygon_rasterization_is_conservative` |
| Start/goal on blocked cell -> `no_path` | `test_start_or_goal_on_blocked_cell_is_no_path` |
| Deterministic routing | `test_route_is_deterministic` |
| 900 m + 900 m @ 30 m/min + 10 + 20 = 90 min | `test_round_trip_time_arithmetic_900m` |
| Negative margin -> `over_budget` | `test_over_budget_sets_margin_and_status` |
| Ascent and slope correctness on known plane | `test_known_plane_ascent_and_slope` |
| Profiles bounded and monotonic | `test_profile_is_bounded_and_distance_monotonic` |
| No path -> `null`, never `0` | `test_no_path_nulls_never_zero` |
| Invalid inputs explicit | `test_invalid_inputs_are_explicit` |
| Rehearsal return-only vs continue | `test_rehearsal_return_only_vs_continue` |
| `elapsedMin` not subtracted twice | `test_rehearsal_does_not_subtract_elapsed_twice` |
| Closure invalidates current, no teleport | `test_rehearsal_closure_invalidates_current_without_teleport` |
| Closure can make return impossible | `test_rehearsal_closure_can_make_return_impossible` |
| `/api/region` manifest shape | `test_get_region_manifest` |
| `/api/plan` success metrics | `test_plan_success_and_round_trip_metrics` |
| `/api/plan` no-path nulls | `test_plan_no_path_fixture` |
| Semantic invalid -> HTTP 200 `invalid_input` | `test_plan_invalid_input_is_explicit` |
| Malformed body -> HTTP 400 | `test_malformed_body_returns_invalid_input` |
| Brief ignores prompt metrics | `test_brief_uses_stored_plan_not_question_text` |
| Missing plan -> 404 + recalculate | `test_brief_missing_plan_requires_recalculation` |
| Stale/expired plan -> 409/410 | `test_brief_stale_and_expired_plans` |
| Rehearsal fixture arithmetic | `test_rehearse_return_only_fixture` |
| Rehearsal closure no teleport (API) | `test_rehearse_closure_does_not_teleport` |
| Bounded plan store | `test_plan_store_is_bounded` |
| Six fixtures self-consistent | `test_contract_fixtures_are_self_consistent` |
| Missing dataset -> 503 `data_unavailable` | `test_missing_dataset_returns_data_unavailable` |

## 4. Dataset measurements

Generated by `server/preprocess.py --synthetic-fallback` (fixed NumPy seed
`2026`) and re-measured from the committed files.

| Property | Measured |
| --- | --- |
| Grid | 150 x 150 cells |
| Cell size | 20 m |
| Extent | 3000 m x 3000 m (~3 km x 3 km) |
| Valid cells | 21,775 / 22,500 (96.8%) |
| Elevation range | -2603.29 m to -2459.54 m (143.75 m relief) |
| Slope p50 / p90 / p99 / max | 2.84 / 8.87 / 33.36 / 35.57 deg |
| Cells at or below 15 deg | 89.6% |
| `imagery.webp` | 150 x 150 RGB hillshade aligned to grid |
| Science stops | 3 (Hazeltop, Montdenier, Mageik) |
| Committed dataset size | 768 KB |

No-data cells are `null` in `elevation.json` / `slope.json` and `false` in
`mask.json`; counts and percentages above are computed from the mask.

## 5. Live API measurements

Smoke test against `uvicorn server.api:app` on `127.0.0.1:8123`, using
`shared/fixtures/plan_success.request.json`.

### `GET /api/region`

- HTTP 200, `schemaVersion = 1`, `datasetVersion = jezero-synthetic-2026.11-v1`.
- Grid 150 x 150 @ 20 m, `cellSizeM` in the allowed `{10, 20}` set.
- Three science stops returned with provenance and source IDs.
- Layer paths resolve to `elevation.json`, `slope.json`, `mask.json`,
  `imagery.webp`, `science-stops.json`.
- `parameterBounds.maxSlopeDeg = {min: 5, max: 30, default: 15}`.

### `POST /api/plan` (base `[400, 400]` -> Hazeltop, 180 min budget)

| Metric | `shortest` | `slope_penalized` |
| --- | --- | --- |
| `status` | `ok` | `ok` |
| `pathXY` cells (combined) | 91 | 91 |
| `distanceM` | 1800.0 | 1833.14 |
| `ascentM` | 25.99 | 28.59 |
| `maxSlopeDeg` | 4.58 | 4.71 |
| `meanSlopeDeg` | 2.41 | 2.14 |
| `travelMin` | 60.0 | 61.1 |
| `dwellMin` | 10.0 | 10.0 |
| `reserveMin` | 20.0 | 20.0 |
| `totalRequiredMin` | 90.0 | 91.1 |
| `marginMin` | 90.0 | 88.9 |

The outbound and return distances are both 900 m, so the shortest mode
reproduces the required `900 + 900 = 1800 m / 30 m/min = 60 min`, plus 10 min
dwell and 20 min reserve, giving 90 min required. `marginMin` is +90 against
the 180 min budget.

### `POST /api/plan` with the `plan_no_path` closure

A north-south closure at `x = 800..820` severs the corridor. Response status is
`no_path`; every `pathXY`, `distanceM`, `ascentM`, `travelMin`,
`totalRequiredMin` and `marginMin` field is `null` and `profile` is `[]`.

### `POST /api/rehearse` (`rehearse_return_only` request)

`currentXY = [1000, 400]`, `baseXY = [400, 400]`, `elapsedMin = 35`,
`remainingBudgetMin = 60`.

| Assessment | `status` | `distanceM` | `travelMin` | `totalRequiredMin` | `marginMin` |
| --- | --- | --- | --- | --- | --- |
| `immediateReturn` | `ok` | 600.0 | 20.0 | 40.0 | 20.0 |
| `continueThenReturn` | `over_budget` | 1200.0 | 40.0 | 70.0 | -10.0 |

Immediate return costs `600 / 30 + 20 reserve = 40 min`. Continuing to
Hazeltop then returning costs `1200 / 30 + 10 dwell + 20 reserve = 70 min`,
which exceeds the 60 min available now. `elapsedMin` is echoed but not
subtracted again, so the live arithmetic differs from the older
`rehearse_return_only` fixture (which uses a 1050 m continuation and 65 min);
both are internally consistent.

### `POST /api/brief`

Posting a question containing falsified numbers (`99999 m`, `5 min`) returns a
`mode: "template"` answer built from the stored plan. Measured `metricRefs`
for `shortest`:

- `distanceM` = 1800.0 m (combined)
- `totalRequiredMin` = 90.0 min
- `marginMin` = 90.0 min
- Outbound and return `distanceM` = 900.0 m each, `travelMin` = 30.0 each

The falsified `99,999` never appears in `answerText`. `sourceIds` cite the
science-stop and DEM records. Missing / expired / stale plan IDs return
HTTP 404 / 410 / 409 with `recalculate: true`.

### Schema validation of live responses

Live API responses were additionally validated against `shared/schema.json`
with `jsonschema` (installed ad hoc; not a runtime dependency). All of the
following validated with zero errors:

- `GET /api/region` -> `regionResponse`
- `POST /api/plan` -> `planResponse` (success and `invalid_input`)
- `POST /api/rehearse` -> `rehearseResponse`
- `POST /api/brief` -> `briefResponse`
- Malformed body and missing plan -> `errorResponse`

All six committed fixtures also validate against their respective request and
response definitions.

## 6. Fixture validation

The six required fixtures exist in `shared/fixtures/` (plus `.request.json`
sidecars for direct posting):

| Fixture | Top-level status | Key invariant |
| --- | --- | --- |
| `plan_success` | `ok` | 90 min required, margin +90, slope mode 92.66 min / +87.34 |
| `plan_identical_routes` | `ok` | Shortest and slope-penalized paths and metrics byte-identical |
| `plan_over_budget` | `over_budget` | 90 min required against 50 min budget; both margins negative |
| `plan_no_path` | `no_path` | All paths/metrics `null`, profiles empty |
| `rehearse_return_only` | `over_budget` | Immediate return 40 min (+20); continue 65 min (-5) |
| `invalid_input` | `invalid_input` | Explicit per-field errors, no fabricated metrics |

## 7. Independent source/coordinate checks

- `test_coordinates.py` (6 tests) checks pixel-centre orientation, metric round
  trips, open outer edges, out-of-bounds handling, and malformed manifest
  rejection.
- Science-stop longitude/latitude values are approximate contextual values, not
  surveyed rover fixes; local `xy` positions are synthetic grid positions.
- No independent survey or external coordinate validation has been performed.

## 8. 2D/3D alignment evidence

- `imagery.webp` is a 150 x 150 RGB hillshade aligned to the same grid as
  `elevation.json`, `slope.json`, and `mask.json`.
- No 3D terrain or playback exists yet because the frontend is not implemented;
  no 3D alignment evidence is recorded.

## 9. Performance measurements

- The only recorded performance measurement is the full-suite wall time:
  `44 passed, 1 warning in 1.10s`.
- No API latency or throughput benchmark has been run.

## 10. Known failures and limitations

No test failures were observed in the recorded run. Known limitations:

- The committed terrain is a deterministic synthetic analog, so all measured
  distances/slopes describe the analog, not actual Jezero topography. The
  real-raster path in `server/preprocess.py` is implemented but not exercised
  against downloaded USGS data in this environment.
- Traversal is purely geometric. No rover speed-vs-slope, energy, thermal,
  solar, communication-window, or slip model is applied; `speedMPerMin` is a
  constant.
- Slope is a cell-scale gradient. Features smaller than a 20 m cell can be
  under-represented, and no-data produces a conservative one-cell halo.
- Paths are unsmoothed grid paths, so ascent and distance include grid-scale
  zig-zag and are planning estimates.
- Briefs are deterministic templates. The contract's `mode: "model"` is
  reserved but not implemented.
- Plan storage is process-local, in-memory, and bounded (256 entries,
  30-minute TTL by default); it is lost on restart and has no auth or rate
  limiting.
- No frontend application code is implemented; `web/` contains only placeholder
  READMEs inherited from `origin/main`.
