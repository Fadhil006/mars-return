# API contract — v1

Owners: A3 and B1. Runtime request/response models live in `server/models.py`; generate `shared/schema.json` with `python -m server.export_schema`. Named types are in `$defs`. Synthetic handoff cases live in `shared/fixtures/` and are never scientific observations.

## Coordinates and region

All positions are `[x_m, y_m]`, east/north positive, in the region's documented Mars metric frame. Raster row 0 is north and column 0 west. `manifest` contains `width`, `height`, `cellSizeM`, `originXY` (west/south), `datasetVersion`, source/analysis projection and provenance. Nested grid arrays are row-major. Elevation unknowns are `null`; `mask: false` excludes missing/unreliable terrain. Slope is degrees, derived in meters; invalid slope neighborhoods are excluded.

Cell centers are `x = west + (col + 0.5)*cellSizeM`, `y = south + (height-row-0.5)*cellSizeM`. West/south boundaries are included; east/north excluded. An endpoint is represented by its containing cell's center, with requested/effective coordinates returned. Invalid endpoint cells are rejected, not relocated. This discretization is not measurement accuracy. Never use Earth's Web Mercator/distance helpers for these Mars coordinates.

`GET /api/region` returns `schemaVersion`, `datasetVersion`, `manifest`, `scienceStops`, `sources`, `layers`, `parameterBounds`, and `warnings`. Assets are served by fixed names under `/api/assets/`. Missing/corrupt bundles return HTTP 503; replacing a region requires a restart.

## Requests

`POST /api/plan` takes:

- Required: `requestId`, `schemaVersion: 1`, `datasetVersion`, `baseXY`, `targetId`.
- Defaults: `maxSlopeDeg: 15`, `speedMPerMin: 30`, `totalBudgetMin: 180`, `reserveMin: 20`, `dwellMin: 10`, `blockedPolygonsXY: []`.
- Slope range: 5–30 degrees. Speed: greater than zero, at most 1000 m/min. Times are nonnegative, capped at 1,000,000 minutes to bound numerical inputs. Reserve must not exceed initial total budget.

`POST /api/rehearse` takes the common identity, dataset, base, target, slope, speed, reserve and polygon fields, plus required `selectedRouteMode`, `currentXY`, `elapsedMin`, `remainingBudgetMin`, and optional `remainingDwellMin: 10`. It does **not** take `totalBudgetMin` or original `dwellMin`.

`remainingBudgetMin` is time available now; elapsed time is never subtracted again. Reserve may exceed remaining budget: that is a valid over-budget scenario. Current position is validated against current exclusions, not automatically constrained to an older route; B1 supplies the playback position. All scenario events are hypothetical.

All numbers must be finite; unknown fields are rejected. Maximum body size is 256 KiB; at most 16 polygons, each 3–128 vertices. Polygon interiors, boundaries, and touched grid cells are blocked conservatively. Self-crossing/degenerate polygons are invalid.

## Results

Successful HTTP calculations include `requestId`, `schemaVersion`, `datasetVersion`, `modelVersion`, `planId`, `inputHash`, `sourceIds`, and `warnings`.

- Plan: `options.shortest` and `options.slope_penalized`.
- Rehearsal: `selectedRouteMode`, `immediateReturn`, `continueThenReturn`.
- Each assessment has `status`, named legs, `totalDistanceM`, `travelMin`, `dwellMin`, `reserveMin`, `totalRequiredMin`, and `marginMin`.
- Plan legs: `outbound`, `return`.
- Immediate return leg: `return`.
- Continuation legs: `currentToTarget`, `targetToBase`.
- Each leg contains `pathXY`, horizontal `distanceM`, `ascentM`, `maxSlopeDeg`, distance-weighted `meanSlopeDeg`, `travelMin`, `profile`, and objective `cost`. Profiles contain `distanceM`, `elevationM`, `slopeDeg`.

Both objectives share hard exclusions. Slope-penalized cost is distance × `(1 + 4*(edgeSlope/slopeLimit)^2)`, using the larger endpoint slope. This is a prototype preference, not physiological energy or a universally safer route. Identical results are valid. Paths remain unsmoothed grid geometry.

Total required time is all leg distances / speed + dwell + reserve. Immediate return omits dwell; continuation uses remaining dwell. Margin is budget minus required time; zero is feasible. No-path geometry and unsupported totals are `null`, not invented zeroes. Valid legs may remain present when another leg is unavailable.

## Errors and stale state

| HTTP | Status | Meaning |
|---|---|---|
| 200 | `ok` | Valid, within modeled budget |
| 200 | `over_budget` | Paths exist, negative time margin |
| 200 | `no_path` | Valid endpoint cells disconnected under constraints |
| 422 | `invalid_input` | Invalid fields, endpoint cells, destination or scenario |
| 409 | `invalid_input` | Dataset version conflict; reload/recalculate |
| 413 | `invalid_input` | Body limit exceeded |
| 503 | `data_unavailable` | Prepared region/assets missing or invalid |

Errors use `{requestId, schemaVersion, status, error: {code, message}}`; malformed requests may have a null request ID.

B1 discards responses whose request ID is not current. Any input change invalidates old reports/explanations. Dataset changes create a new dataset version. The server keeps at most 128 evaluations for one hour in memory, including rehearsal results; restart/expiry/eviction requires recalculation. Run one worker process because the store is process-local.

## B3 assistant boundary

`POST /api/brief` remains B3's implementation: `requestId`, `planId`, `selectedRouteMode`, `question` → answer, source IDs, metric references, and model/template mode. A3 provides `server.evidence.trusted_context(store, planId, datasetVersion, selectedRouteMode)`. Only saved calculations are trusted; client-supplied metrics never override them. No model provider or credential is required to run Group A.
