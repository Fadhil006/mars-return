# API contract — v1

Owners: A3 and B1. Runtime request/response models live in `server/models.py`; generate `shared/schema.json` with `python -m server.export_schema`. Named types are in `$defs`. Synthetic handoff cases live in `shared/fixtures/` and are never scientific observations.

## Coordinates and region

All positions are `[x_m, y_m]`, east/north positive, in the region's documented Mars metric frame. Raster row 0 is north and column 0 west. `manifest` contains `width`, `height`, `cellSizeM`, `originXY` (west/south), `datasetVersion`, source/analysis projection and provenance. Nested grid arrays are row-major. Elevation unknowns are `null`; `mask: false` excludes missing/unreliable terrain. Slope is degrees, derived in meters; invalid slope neighborhoods are excluded.

Cell centers are `x = west + (col + 0.5)*cellSizeM`, `y = south + (height-row-0.5)*cellSizeM`. West/south boundaries are included; east/north excluded. An endpoint is represented by its containing cell's center, with requested/effective coordinates returned. Invalid endpoint cells are rejected, not relocated. This discretization is not measurement accuracy. Never use Earth's Web Mercator/distance helpers for these Mars coordinates.

`GET /api/region` returns `schemaVersion`, `datasetVersion`, `manifest`, `scienceStops`, `sources`, `layers`, `parameterBounds`, and `warnings`. Assets are served by fixed names under `/api/assets/`. When the bundle has one, `layers` also lists `rover-traverse.json`: real Perseverance `waypoints` (`sol`, `rmc`, `xy`, `elevationM`, `odometerM`) and a `pathXY` polyline in the same local frame. Science stops of `kind: "rover_sample_site"` carry `samples`, `roverSol`, `roverRMC` and `locationProvenance`. Missing/corrupt bundles return HTTP 503; replacing a region requires a restart.

## Requests

`POST /api/plan` takes:

- Required: `requestId`, `schemaVersion: 1`, `datasetVersion`, `baseXY`, `targetId`.
- Defaults: `maxSlopeDeg: 15`, `speedMPerMin: 30`, `totalBudgetMin: 180`, `reserveMin: 20`, `dwellMin: 10`, `blockedPolygonsXY: []`, `mastHeightM: 2`, `eyeHeightM: 1.7`, `maxOutOfContactMin: 15` (all three hypothetical contact inputs, on every scenario request).
- Slope range: 5–30 degrees. Speed: greater than zero, at most 1000 m/min. Times are nonnegative, capped at 1,000,000 minutes to bound numerical inputs. Reserve must not exceed initial total budget.

`POST /api/rehearse` takes the common identity, dataset, base, target, slope, speed, reserve and polygon fields, plus required `selectedRouteMode`, `currentXY`, `elapsedMin`, `remainingBudgetMin`, and optional `remainingDwellMin: 10`. It does **not** take `totalBudgetMin` or original `dwellMin`.

`remainingBudgetMin` is time available now; elapsed time is never subtracted again. Reserve may exceed remaining budget: that is a valid over-budget scenario. Current position is validated against current exclusions, not automatically constrained to an older route; B1 supplies the playback position. All scenario events are hypothetical.

All numbers must be finite; unknown fields are rejected. Maximum body size is 256 KiB; at most 16 polygons, each 3–128 vertices. Polygon interiors, boundaries, and touched grid cells are blocked conservatively. Self-crossing/degenerate polygons are invalid.

`POST /api/reach` takes the common identity, dataset, base, slope, speed, reserve and polygon fields (no target), plus required `selectedRouteMode` and `remainingBudgetMin`. It answers "from where can we still walk home?"

`POST /api/stress` takes every plan field plus required `selectedRouteMode`, and optional `closureRadiusM: 60` (20–300) and `closureCount: 8` (1–12). It answers "does the way home survive any single closure?"

## Results

Successful HTTP calculations include `requestId`, `schemaVersion`, `datasetVersion`, `modelVersion`, `planId`, `inputHash`, `sourceIds`, and `warnings`.

- Plan: `options.shortest` and `options.slope_penalized`.
- Rehearsal: `selectedRouteMode`, `immediateReturn`, `continueThenReturn`.
- Each assessment has `status`, named legs, `totalDistanceM`, `travelMin`, `dwellMin`, `reserveMin`, `totalRequiredMin`, and `marginMin`.
- Contact (when the base has terrain data): each `ok` leg adds `outOfContactM`, `outOfContactMin`, `longestOutOfContactMin`, `longestOutOfContactStartM`, `longestOutOfContactEndM` (metres along the leg) and `inContact` (one boolean per `pathXY` vertex). Each assessment adds `outOfContactMin` (walking plus dwell at a stop the base cannot see), `longestOutOfContactMin` (one continuous stretch, across the stop), `maxOutOfContactMin` and `contactStatus` (`within_rule` when the longest stretch is at most the rule, else `exceeds_rule`). `contactStatus` is a second verdict and never changes `status`. A step between two path cells is in contact only if both cells can see the base mast.
- Plan responses add `contact`: `visible` (row-major 0/1 grid, row 0 north, same shape as the region), `visibleFraction`, `mastHeightM`, `eyeHeightM`, `maxOutOfContactMin`. Line of sight is geometric on the DEM with curvature, bilinear terrain samples every half cell, and any sight line passing within one cell of missing data counts as blocked. It ignores antennas, relays and radio diffraction.
- Plan legs: `outbound`, `return`.
- Immediate return leg: `return`.
- Continuation legs: `currentToTarget`, `targetToBase`.
- Each leg contains `pathXY`, horizontal `distanceM`, `ascentM`, `maxSlopeDeg`, distance-weighted `meanSlopeDeg`, `travelMin`, `profile`, and objective `cost`. Profiles contain `distanceM`, `elevationM`, `slopeDeg`.

- Reach: `status`, `returnMin` (row-major grid of walking minutes back to base along the chosen objective's path, `null` where unreachable), `allowanceMin` (remaining budget minus reserve), `reachableAreaM2`, `returnableAreaM2`, `farthestReturnableMin`. A cell is returnable when `returnMin <= allowanceMin`. Status is `over_budget` when no cell is.
- Stress: `baseline` (the plan assessment for the selected objective), `closures`, `closureRadiusM`, `survivableCount`, `worstMarginMin`, `verdict`. Each closure is an octagon of the given radius centred on a point of the baseline return path, never within one radius plus one cell of either endpoint. It reports `centerXY`, `alongReturnM`, `status`, `returnDistanceM`, `detourM`, `totalRequiredMin`, `marginMin` and the rerouted `pathXY`. Outbound travel and dwell are unchanged; only the return is recalculated. `verdict` is `robust` when every closure stays within budget, `fragile` when any is over budget or has no path, `unavailable` when there is no baseline round trip. `worstMarginMin` is `null` if any closure has no path.

Both objectives share hard exclusions. Slope-penalized cost is distance × `(1 + 4*(edgeSlope/slopeLimit)^2)`, using the larger endpoint slope. This is a prototype preference, not physiological energy or a universally safer route. Identical results are valid. Paths remain unsmoothed grid geometry.

Total required time is all leg distances / speed + dwell + reserve. Immediate return omits dwell; continuation uses remaining dwell. Margin is budget minus required time; zero is feasible. No-path geometry and unsupported totals are `null`, not invented zeroes. Valid legs may remain present when another leg is unavailable.

## Errors and stale state

| HTTP | Status | Meaning |
|---|---|---|
| 200 | `ok` | Valid, within modeled budget |
| 200 | `over_budget` | Paths exist, negative time margin |
| 200 | `no_path` | Valid endpoint cells disconnected under constraints |
| 422 | `invalid_input` | Invalid fields, endpoint cells, destination or scenario |
| 404 | `invalid_input` | `/api/brief` only, code `plan_expired`: plan missing, expired or evicted; recalculate |
| 409 | `invalid_input` | Dataset version conflict; reload/recalculate |
| 413 | `invalid_input` | Body limit exceeded |
| 503 | `data_unavailable` | Prepared region/assets missing or invalid |

Errors use `{requestId, schemaVersion, status, error: {code, message}}`; malformed requests may have a null request ID.

B1 discards responses whose request ID is not current. Any input change invalidates old reports/explanations. Dataset changes create a new dataset version. The server keeps at most 128 evaluations for one hour in memory, including rehearsal results; restart/expiry/eviction requires recalculation. Run one worker process because the store is process-local.

## B3 assistant boundary

`POST /api/brief` (`server/assistant.py`, owner B3) takes `requestId`, `planId`, `selectedRouteMode` and `question` (1–500 characters); unknown fields are rejected. It returns `requestId`, `schemaVersion`, `planId`, `datasetVersion`, `modelVersion`, `answer`, `sourceIds`, `metricRefs`, `mode` and `supported`.

- The plan is read through `server.evidence.trusted_context(store, planId, datasetVersion, selectedRouteMode)` using the running region's dataset version. Only saved calculations are trusted; nothing in the question can change a metric. Both plan and rehearsal IDs are accepted; a rehearsal must be asked about with the route mode it was saved with.
- `metricRefs` are `<assessment>.<field>`: the route mode for a plan (`shortest.marginMin`), or `immediateReturn` / `continueThenReturn` for a rehearsal. Every `sourceId` exists in the region's source records or the stop's `sourceIds`.
- The question is sorted by keyword into route, return, evidence or unsupported. Unsupported questions (weather, medical, safety, anything unmatched) return `supported: false`, an answer beginning "The supplied evidence does not cover this." and no references; they never reach a model.
- `mode: "template"` is a deterministic answer built from the stored values. `mode: "model"` appears only when `MODEL_API_KEY` is set and the optional `anthropic` package is installed, and only if the generated answer parses, cites only allowed IDs and repeats only numbers present in the stored facts. A timeout (8 s), refusal, outage or failed check returns the template.

No model provider or credential is required to run the service or its tests.
