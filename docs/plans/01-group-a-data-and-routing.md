# Group A — Data, Routing, and Mission Calculations

> Implementation checkpoint: the backend and real CTX region are now implemented. See [validation evidence](../validation.md) and the current [API contract](../../shared/api-contract.md) for verified behavior and remaining gates. The original planning checklists below are not a claim that all team acceptance checks are complete.

Three-person implementation plan • Planning draft, 12 November 2026

> For agentic workers: Use superpowers:executing-plans if later authorized to implement. This document currently assigns work to the six human teammates; it does not authorize automatic implementation or delegation. Checkboxes track work still to be done.

**Goal:** Produce a reproducible region package and route service that explains whether a hypothetical Mars excursion and return fit the team's chosen constraints.

**Architecture:** Prepare a bounded region in advance of serving requests during the build. Compute routes on a shared local metric grid, expose the results through a small API, and keep provenance alongside every result. Group B consumes those results without recalculating the science independently.

**Proposed stack:** Python, NumPy, Rasterio/GDAL, FastAPI, pytest. Versions are pinned to a compatible environment at kickoff.

**Spec:** [Shared project plan](00-martian-map-team-plan.md). Read it before this document, especially the coordinate and API contract.

## Repository status — structure created, 12 November 2026

Repository: `/home/fadhil/Projects/mars-return` · Remote: `https://github.com/Fadhil006/mars-return.git`

The folders, ownership READMEs, shared API design, collaboration guide and documentation templates now exist. This is a structural scaffold: application modules, dependency manifests/lockfiles, machine-readable schemas, fixtures, data products and tests are still to be implemented. No working app, scientific result or passing application test suite is claimed.

The authoritative plans live in `docs/plans/` in the repository. The chat output copies are synchronized snapshots. All repository paths below are relative to the repository root. Existing README/template files are starting points; unchecked implementation tasks remain open.

## Global constraints

- Real imagery and numeric elevation; no fabricated scientific terrain.
- One bounded region and one science destination per route request.
- Positions in local meters, with documented Mars projection and origin.
- No-data and blocked cells are excluded from routing.
- Time and slope settings are explicit illustrative scenario assumptions, not certified astronaut operating limits.
- Group A owns route numbers; Group B displays and explains them.
- API and dataset changes are versioned and agreed with B1.
- No claims of physiological safety, live weather prediction, or current obstacle detection.

## Review focus

1. Coordinate transformations: degrees, meters, latitude type, north/south row direction and 3D axes must not be confused. A1 owns landmark and round-trip conversion tests.
2. Coverage gaps: missing elevation must not become zero-height, traversable ground. A1 tests masks; A2 tests route exclusion.
3. Disconnected paths: barriers and diagonal corners must not permit impossible shortcuts. A2 tests both.
4. Time accounting: return legs, dwell, reserve and elapsed time must be counted exactly once. A2/A3 test plan and rehearsal separately.
5. Stale state: an old dataset or plan must not silently produce a current explanation. A3 tests version and plan lookup errors; B1/B3 handle presentation.

## People and outputs

| Person | Owns | Must hand over | Reviewer |
|---|---|---|---|
| A1 | Source discovery, preprocessing, coordinates | Region bundle and source manifest | A3 for science, B2 for alignment |
| A2 | Algorithms and mission arithmetic | Tested route and rehearsal functions | A3 |
| A3 | Scientific destinations, API, validation | Service, fixtures and evidence package | A2 for service outputs, B3 for evidence |

A3 is Group A's coordinator. Help A1 if data access threatens the H3 decision gate. Avoid giving all integration work to A2 after routing is finished.

## Implementation files and ownership

The parent directories now exist. The code, data and test files listed below are planned deliverables, not completed modules. The listed documentation files exist as starter templates and still need evidence from the build.

| File/directory | Owner | Purpose |
|---|---|---|
| shared/schema.json | A3 + B1 | Versioned request/response definitions |
| shared/fixtures/*.json | A3 | Explicit synthetic development cases |
| data/region/manifest.json | A1 | Bounds, transform, projection, sources, versions |
| data/region/imagery.webp | A1 | Aligned preview texture |
| data/region/elevation.json | A1 | Row-major elevation grid; null for unknown |
| data/region/slope.json | A1 | Analysis slope grid in degrees |
| data/region/mask.json | A1 | Valid cells and permanent exclusions |
| data/region/science-stops.json | A3 | Documented destinations and source IDs |
| server/preprocess.py | A1 | Source-to-region conversion |
| server/coordinates.py | A1 | Raster/world conversion |
| server/routing.py | A2 | Graph search and path metrics |
| server/mission.py | A2 | Round-trip and rehearsal evaluation |
| server/api.py | A3 | Validation, endpoints and plan records |
| server/evidence.py | A3 | Structured evidence lookup for B3 |
| server/tests/test_coordinates.py | A1 | Coordinate and alignment checks |
| server/tests/test_routing.py | A2 | Geometry, barriers, search correctness |
| server/tests/test_mission.py | A2 | Budget and return behavior |
| server/tests/test_api.py | A3 | Contract, invalid data and version checks |
| docs/data-method.md | A1 | Processing and limitations |
| docs/validation.md | A3 | Measured test results and independent checks |

## A1: Data engineer and coordinate owner

### Task A1.1 — Prove data access and choose the study area (H1–3)

**Inputs:** Shared scope, USGS Jezero catalogue leads and official resource list when published.

**Outputs:** Verified candidate crop, input file inventory, suitability decision.

- [ ] Inspect the official challenge resources and record any useful additions.
- [ ] Open a numeric terrain raster locally. Confirm its bands, units, no-data value, source coordinate system, pixel spacing, bounds and file size.
- [ ] Open imagery covering the same region. A rendered hillshade is display material, not a substitute for numeric elevation.
- [ ] Work with A3 to identify a roughly 3 km area containing scientifically useful destinations. Keep all route endpoints inside valid coverage.
- [ ] Choose HiRISE if access and coverage work promptly; otherwise choose verified CTX coverage and disclose its coarser resolution.
- [ ] Record source product IDs, mission/instrument, URLs, acquisition dates where available, publication date separately, attribution and use terms.
- [ ] Show the crop and one measured elevation to the whole team at H3.

**Acceptance:** A second person can open the source file, identify the same geographic feature and confirm that the numeric values are elevation in the stated units. A source page alone does not pass.

### Task A1.2 — Produce the shared grid (H3–6)

**Interface:** prepare_region(source_paths, crop_bounds, output_dir) → manifest and region files. pixel_to_xy(row, col, manifest) → [x_m, y_m]. xy_to_pixel(x_m, y_m, manifest) → [row, col] or out-of-bounds.

- [ ] Define an explicit local metric analysis frame with a documented Mars datum and projection. Preserve the complete transforms from each source.
- [ ] Start with 10 m analysis cells if source data supports them, or 20 m cells with CTX. Do not upsample 20 m data and describe it as 10 m evidence.
- [ ] Keep the analysis grid at most 512 × 512 cells by narrowing the crop or choosing a coarser documented grid. This is a performance limit, not a science guarantee.
- [ ] Derive slope from metric elevation gradients. Do not compute gradients in raw longitude/latitude degrees. Mask slope neighborhoods that lack valid elevation.
- [ ] Where fine terrain is aggregated, retain a conservative within-cell slope statistic for traversability instead of concealing steep patches through averaging; document the baseline and reduction method.
- [ ] Export aligned imagery, elevation, slope and mask. Preserve unknowns as null/masked cells.
- [ ] Add a per-layer coverage and resolution description. Distinguish pixel spacing from measurement accuracy.
- [ ] Supply three checked landmarks, their local coordinates, image pixel locations and source positions to B1/B2.

**Acceptance:** Round-trip pixel/world conversion differs by less than half an analysis cell; a known-plane synthetic raster returns its expected slope; three real landmarks align within the chosen analysis-cell tolerance. Record the actual discrepancy rather than imply subpixel geodetic accuracy.

**Reference:** USGS describes known terrain artifacts, so inspect shaded relief and source imagery around the demo route: https://stac.astrogeology.usgs.gov/docs/data/mars/hirise_dtms/

### Task A1.3 — Support 3D and freeze the data (H6–9, final review H24–27)

- [ ] Confirm B2's mesh orientation and vertical scale against the supplied landmarks.
- [ ] Provide a lower-density display mesh/grid if required, with the same bounds and transform as the analysis grid.
- [ ] Identify processing seams or artifacts near the route; exclude unreliable areas or move the demo crop.
- [ ] Freeze datasetVersion and checksums. Any subsequent data change creates a new version and invalidates old plans.
- [ ] Finish the short processing record so another teammate can reproduce the bundle.

## A2: Routing and mission-model owner

### Task A2.1 — Search paths correctly (H1–6)

**Inputs:** Start with synthetic test grids; replace them with A1's real grid after H3.

**Interface:** route(grid, start_xy, goal_xy, mode, max_slope_deg, blocked_polygons) → RouteResult. mode is shortest or slope_penalized.

- [ ] Create tests for flat ground, a wall with one gap, disconnected regions, diagonal corner cutting and no-data holes.
- [ ] Implement eight-neighbor A* or Dijkstra. Both modes use the same hard exclusions and slope ceiling.
- [ ] For shortest mode, use horizontal step distance as cost.
- [ ] For slope_penalized mode, use cost = stepDistance × (1 + 4 × (edgeSlope / slopeLimit)^2). Set edgeSlope to the larger conservative cell slope at the edge. These are transparent prototype preferences, not validated physiological costs.
- [ ] Use a Euclidean-distance heuristic for A*; it is bounded by these nonnegative edge costs. Verify against Dijkstra on small grids.
- [ ] Forbid a diagonal move if either adjacent orthogonal cell is blocked. Rasterize any scenario polygon conservatively; reject route edges that cross it.
- [ ] Keep the grid path for analysis. Do not smooth it into visually attractive shortcuts through forbidden terrain.
- [ ] Return identical paths honestly when the two objectives agree.

**Defaults:** Illustrative maximum slope 15 degrees; UI-supported range 5–30 degrees. This setting is a user-selected planning constraint, not an astronaut capability claim. A slope-weighted optimum is not guaranteed to minimize every reported slope metric; describe what actually improves in each result.

**Acceptance:** Flat-grid distances and barriers are correct, paths remain in valid cells, both modes match their reference optimum on small grids, and no-path returns a structured error instead of a straight line.

### Task A2.2 — Evaluate round trips (H6–9)

**Interface:** evaluate_plan(region, request) → PlanResult with two route options, each containing outbound and return legs.

- [ ] Compute each leg explicitly, even if a static symmetric model returns the reverse of the outbound path.
- [ ] Calculate distance, cumulative ascent, maximum sampled slope, distance-weighted mean slope and elevation profile.
- [ ] Use horizontal path distance consistently for distance and simple travel time. Label this choice; do not mix surface and horizontal distances across views.
- [ ] Compute totalRequiredMin = outboundDistance/speed + returnDistance/speed + dwellMin + reserveMin.
- [ ] Compute marginMin = totalBudgetMin − totalRequiredMin. A negative margin means over_budget, not no_path.
- [ ] Reject nonpositive speed, invalid endpoints, unsupported versions, negative budgets, and reserve larger than budget. Return explicit validation messages.
- [ ] Use example defaults of 30 m/min travel speed, 180 minutes total budget, 10 minutes at the science stop and 20 minutes reserve. Mark every value as an illustrative assumption. Constant speed does not model terrain-dependent fatigue or suit performance.

**Acceptance example:** With 900 m outbound, 900 m return, 30 m/min speed, 10 min dwell and 20 min reserve, total required time is 90 minutes. With a 180 minute budget the margin is 90 minutes. This is a synthetic arithmetic check, not a prediction for an astronaut.

### Task A2.3 — Implement “Can we still get back?” (H9–12)

**Interface:** evaluate_rehearsal(region, request) → immediateReturn and continueThenReturn results.

- [ ] Accept the current position along the previously selected route, the remaining budget, and an optional blocked corridor.
- [ ] Recompute current → base for immediate return and current → destination → base for continuation. Use the updated exclusions for every leg.
- [ ] Compute immediate-return requirement as returnDistance/speed + reserveMin. Add remaining dwell only to continuation.
- [ ] Treat remainingBudgetMin as time available now; elapsedMin is contextual history, not another subtraction.
- [ ] Distinguish: both feasible; only return fits; neither fits the budget; no return path exists; current position invalidated by the closure.
- [ ] If an event blocks the current cell, report that the scenario needs adjustment. Do not teleport the astronaut to a nearby cell.
- [ ] Show the event as hypothetical. A missing or blocked route is not proof that an actual astronaut cannot return; it is a limitation/result of this model.

**Acceptance:** A test corridor closure forces a detour or no-path result, reducing time changes margins correctly, and resetting the event restores the original output for the same versioned inputs.

## A3: Science lead, service integrator and reviewer

### Task A3.1 — Give Group B a stable interface immediately (H0–1)

- [ ] Review `shared/api-contract.md` with B1; confirm schemaVersion 1, units, coordinate order and null/error behavior, then implement `shared/schema.json`.
- [ ] Publish fixture responses for success, identical routes, budget failure, invalid input, no-path and missing data.
- [ ] Publish the source record format: sourceId, title, URL, mission/instrument, productId if present, temporal information, resolution if relevant, attribution and limitations.
- [ ] Initialize the Python project under `server/`, record compatible pinned dependencies and launch/test commands in `server/README.md`, then create service validation and a simple region endpoint so Group B can integrate while A1/A2 continue.

**Acceptance:** B1 can render fixture data without inventing fields, and both groups can identify the meaning and units of every numeric field.

### Task A3.2 — Curate science destinations (H1–6)

- [ ] Review NASA's sample descriptions and rover-location context with A1. Select three distinct locations inside the verified crop.
- [ ] For each, write its scientific question, observed rock/geologic description, relevance to the proposed excursion, source links and location provenance.
- [ ] Distinguish the original observation/sample site from a sample depot or the sample's present storage location.
- [ ] Use source coordinates or defensibly registered positions. If a location is approximate, record that uncertainty and display an area/approximate marker. Do not extract precise coordinates by guessing from a screenshot.
- [ ] If exact published sites do not fit the crop, reduce the site count or select a different crop. Hypothetical waypoints can be used, but cannot inherit a real sample's identity without evidence.
- [ ] Give B3 compact evidence records with IDs. Label geological interpretation as such; do not call a text rock classification a quantitative chemical measurement.

**Acceptance:** A teammate can trace each science statement and location to a source. The bundle combines orbital and surface-mission evidence, rather than relabeling several derivatives of one raster as independent missions.

### Task A3.3 — Assemble and validate the service (H6–12)

- [ ] Connect A2's functions to /api/plan and /api/rehearse using the shared contract.
- [ ] Record planId, input hash, modelVersion and datasetVersion for every successful evaluation. Keep a bounded in-memory store; missing/expired plans request recalculation.
- [ ] Provide a validated evidence/metrics context to B3's assistant endpoint. B3 owns model calls and answer construction; A3 owns trusted plan lookup.
- [ ] Distinguish HTTP validation errors from valid no_path or over_budget results.
- [ ] Log computation timings and failures without credentials or unnecessary user data.
- [ ] Confirm hosted and local launch instructions with B2. Serve the frontend and prepared assets from the same origin if feasible.

### Task A3.4 — Independent review and scientific handoff (H24–30)

- [ ] Run the meaningful test suite: pytest server/tests.
- [ ] Manually check a landmark, an elevation sample and a route distance using a second tool or independent calculation.
- [ ] Record three real-data scenarios and one synthetic regression case with inputs, outputs, versions and limitations.
- [ ] Verify that the UI does not describe slope-penalized routing as universally safest or globally optimal beyond the chosen grid/model.
- [ ] Review B3's explanation for one successful route, one return-only scenario and one unsupported question.
- [ ] Give B3 the final list of measured claims that can appear in the pitch.

## Group A definition of done

- [ ] One reproducible real-data region, with documented source and analysis resolution.
- [ ] Two route modes and explicit return calculations.
- [ ] Scenario event and time-budget behavior verified.
- [ ] Valid responses for no-path, missing data and invalid input.
- [ ] Source-backed science stops and evidence records.
- [ ] Correct 2D/3D alignment confirmed with Group B.
- [ ] Measured test/performance results and a short limitation statement.
- [ ] Service runs on another teammate's machine.

## If blocked

If high-resolution terrain is unavailable, use actual coarser elevation and narrow claims. If data size is too large, crop and reduce display density before reducing scientific integrity. If the algorithm is too slow, narrow the grid and measure again. If the destination coordinates cannot be justified, use a broader documented geological region with explicit location uncertainty. Never substitute a fabricated route while describing it as calculated from NASA data.

## Starting sources

- https://astrogeology.usgs.gov/search/map/mars-2020-jezero-crater-landing-site-products
- https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic
- https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars
- https://science.nasa.gov/mission/mars-2020-perseverance/location-map/
- https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/
