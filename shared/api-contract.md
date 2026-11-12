# API Contract — Draft v1

Owners: A3 and B1. Design only: JSON Schema, fixtures and endpoints are not implemented. The shared plan is in `docs/plans/00-martian-map-team-plan.md`.


All calculations and browser overlays use one local metric coordinate system. Positions are [x_m, y_m] with east and north positive. The manifest stores the full source projection, the analysis projection, origin, pixel transform, Mars datum/radius, units, and coverage. Do not use Earth's Web Mercator or Earth distance helpers for Mars calculations.

The region bundle contains manifest.json, an imagery preview, elevation and slope grids, a valid-data mask, and science-stops.json. Raster row 0 is the north edge; column 0 is the west edge. A1 supplies conversion functions and three landmark checks. B2 converts these coordinates into its 3D axes explicitly.

**Service contract, schema version 1 (design only):**

- GET /api/region: manifest, layer paths, supported parameter bounds, science stops and source records.
- POST /api/plan: requestId, schemaVersion, datasetVersion, baseXY, targetId, maxSlopeDeg, speedMPerMin, totalBudgetMin, reserveMin, dwellMin, blockedPolygonsXY. Returns results for both route modes.
- POST /api/rehearse: the same dataset and constraint fields plus currentXY, elapsedMin, remainingBudgetMin, targetId, baseXY, and blockedPolygonsXY. Returns immediateReturn and continueThenReturn assessments. remainingBudgetMin excludes elapsed time; the server must not subtract elapsedMin a second time.
- POST /api/brief: requestId, planId, selectedRouteMode, question. Returns answer text, sourceIds, metricRefs, and mode: model or template. The server retrieves the saved plan; it does not trust route metrics supplied by a chat prompt.

A route result contains status, pathXY, distanceM, ascentM, maxSlopeDeg, meanSlopeDeg, travelMin, dwellMin, reserveMin, totalRequiredMin, marginMin, profile, sourceIds, datasetVersion, modelVersion, and warnings. A round trip contains distinct outbound and return legs plus combined metrics. A rehearsal continuation contains current-to-target and target-to-base legs. Each profile sample contains distanceM, elevationM, and slopeDeg.

Statuses: ok, over_budget, no_path, invalid_input, data_unavailable. If there is no path, path and unsupported metrics are null, not invented zeroes. The service records a planId and input hash. B1 discards results whose requestId does not match the latest input. Reports and assistant responses always include the active planId; stale answers are invalidated after any mission change.

**Hour 1 handoff:** A3 and B1 publish the schema and sample responses for success, identical routes, over-budget, no-path, invalid input, and missing data. Fixtures are explicitly synthetic development inputs. Group B uses them immediately while Group A processes real data.


## Items to resolve before schema freeze

- Specify the exact envelope/type for each endpoint, including planId and error objects.
- Separate per-leg geometry metrics from aggregate mission/time metrics.
- Define rehearsal route mode explicitly: evaluate both modes or require selectedRouteMode consistently.
- Define input bounds, polygon validity, response status codes and plan expiry behavior.
- Define region manifest serialization, grid asset formats and source record schema.

Record these decisions in the machine-readable schema and fixtures; do not let each group invent different shapes.
