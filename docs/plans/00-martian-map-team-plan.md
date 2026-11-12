# Martian Map — Six-Person Team Plan

Planning draft • 12 November 2026 • Two groups of three

This is a proposed hackathon build plan, not a claim that the application or datasets have been tested. The user requested real route planning, 3D exploration, AI assistance, and a distinctive idea. Names, stack, and exact local deadlines were left to the planner. Person A1–A3 and B1–B3 are assignment placeholders.

Read this shared plan first, then give each group its own detailed document:

- [Group A: Data, routing, and mission calculations](01-group-a-data-and-routing.md)
- [Group B: Map, 3D, assistant, and presentation](02-group-b-experience-and-demo.md)

**Proposed product: MARS RETURN.** A mission rehearsal tool for exploring a small part of Jezero Crater, choosing a science stop, comparing routes, and answering: “If conditions change here, can we still return to base within our chosen time budget?”

## Repository status — structure created, 12 November 2026

Repository: `/home/fadhil/Projects/mars-return` · Remote: `https://github.com/Fadhil006/mars-return.git`

The folders, ownership READMEs, shared API design, collaboration guide and documentation templates now exist. This is a structural scaffold: application modules, dependency manifests/lockfiles, machine-readable schemas, fixtures, data products and tests are still to be implemented. No working app, scientific result or passing application test suite is claimed.

The authoritative plans live in `docs/plans/` in the repository. The chat output copies are synchronized snapshots. All repository paths below are relative to the repository root. Existing README/template files are starting points; unchecked implementation tasks remain open.

## 1. The experience and its distinctive feature

The visitor selects a hypothetical base and a documented science destination. They inspect actual imagery and terrain, compare shortest-distance and slope-penalized routes, and rehearse the chosen route in 3D. At a selected point, they block a corridor or reduce the remaining time. The system recalculates an immediate return and, where feasible, continuation to the destination followed by return. A grounded assistant explains the difference and links to evidence.

The proposed distinction is the combination of return planning, visible data limitations, and an explained before/after rehearsal. Do not claim this is the first Mars mapping, routing, or AI planning tool. NASA already publishes rover maps and terrain-based planning tools. Novelty should be demonstrated as a useful experience, not claimed as an unverified scientific invention.

The mission is hypothetical. The base, time budget, travel speed, slope limit, and injected obstruction are scenario assumptions. The underlying terrain and published science observations are real. Use explicit labels for observations, derived quantities, and scenario inputs.

## 2. Scope that six people can finish

**Required for the intended complete demo:**

- One approximately 3 × 3 km region, adjusted to verified overlapping data coverage.
- One hypothetical base, three source-backed science destinations, and one selected destination per calculation.
- Optical imagery, elevation/derived slope, and an interpreted geology/science-stop layer based on published rover observations. Elevation and slope count as the same underlying data family.
- Two route modes: shortest distance and a route that penalizes steeper terrain. They may legitimately coincide.
- A round-trip comparison, route elevation profile, and visible data resolution.
- A real-terrain 3D view with orbit, zoom, and simple route playback.
- One corridor-blocking event and a remaining-time control.
- An immediate-return comparison from the rehearsal position.
- An AI assistant limited to the selected mission and curated evidence, with a non-AI explanation fallback.
- A shareable mission summary containing route metrics, assumptions, source links, and limitations.
- A working hosted demo and a local backup that does not depend on live NASA services.

**Extensions only after all of the above works:** additional regions, multiple stops, natural-language scenario commands, detailed astronaut animations, voice, richer lighting, or an overview globe. Do not train a new model or implement physiological oxygen/radiation forecasts for this build.

## 3. Team structure and decision ownership

| Person | Primary responsibility | Concrete deliverable | Direct partner |
|---|---|---|---|
| A1 | Data and coordinate systems | Verified region package, aligned imagery/elevation, source manifest | B1 and B2 |
| A2 | Routing and return calculations | Tested route engine and scenario evaluation | B1 |
| A3 | Science content, service integration, numerical QA; Group A lead | API, science stops, validation report | B3 |
| B1 | Product flow, 2D map, state management; Group B lead | Complete interactive mission flow | A3 |
| B2 | 3D terrain, visual integration, performance | Data-derived terrain and route playback | A1 |
| B3 | Grounded assistant, mission report, demo story | Evidence-backed explanations and presentation | A3 |

B1 coordinates scope and the task board. A3 coordinates data/interface changes. A1 approves scientific source attribution; A2 approves calculation claims; B2 owns deployment packaging with A3. B3 prepares the submission narrative, while B1 owns the final submission checklist and confirmation of receipt. All six rehearse and review the final project.

Each task has one owner and one reviewer. Each member can use AI, but owns verification of the output.

## 4. Suggested technical approach

Use React + TypeScript + Vite for the browser interface, a bounded image/map canvas for the 2D view, Three.js for the terrain view, and Python + FastAPI for preprocessing and route calculations. Use NumPy and a raster library such as Rasterio/GDAL for actual elevation values. Pin the working dependency versions at the start of the event. This is a recommended stack, not a user-specified requirement.

Serve the built frontend and prepared data from the same application origin as the API. Keep the deployment simple: one service, small prepared files, no database, and no login. An optional model endpoint runs server-side; credentials stay outside browser code. Package the core scenario so the local application works without external APIs.

The 3D view is a mesh built from the same elevation grid used in analysis, or a documented decimation of it. The image texture comes from the aligned imagery. No generated terrain is used as a scientific surface. AI-generated artwork may be decorative only and labeled when relevant.

## 5. Data plan and the early decision gate

| Need | Starting source | What the team must verify |
|---|---|---|
| Local elevation | USGS Mars 2020 Jezero products; HiRISE DTM preferred | Actual numeric raster access, coverage, projection, units, artifacts, resolution |
| Fallback elevation | USGS Jezero CTX DEM, published at 20 m/pixel | Download and extraction; reduce precision claims accordingly |
| Orbital imagery | Matching USGS orthoimage or Mars Trek layer | Alignment, attribution, usable crop, local display |
| Science destinations | NASA Perseverance sample descriptions and location information | Traceable location, geological relevance, image/source association |
| Context | NASA/USGS mission material | Historical dates, mission attribution, clear distinction from predictions |

USGS lists Jezero HiRISE and CTX terrain products; the CTX science mosaic page lists a 20 m/pixel DEM and a matched 5 m/pixel image mosaic. These are verified catalogue leads, not successfully downloaded and validated inputs for this project. The higher-resolution product must be checked before making meter-scale claims.

The official challenge resource tab still displayed “Resources will be available on Friday, November 13” on 12 November. A1 checks the updated list at kickoff. Availability of a web page is not proof that a file can be downloaded, processed, or used at a particular location.

**By build hour 3:** A1 must show a numeric elevation crop, aligned imagery, and a location that A3 can connect to documented science. Prefer a roughly 3 km crop near the western delta, but let data coverage determine the exact extent. If high-resolution access fails, use verified CTX coverage. If no numeric elevation can be loaded, switch to an explicitly limited layered mission-map submission and disclose that automated routing/terrain rehearsal is incomplete. Never manufacture elevations to preserve the pitch.

## 6. Shared interface: confirm this before splitting

All calculations and browser overlays use one local metric coordinate system. Positions are [x_m, y_m] with east and north positive. The manifest stores the full source projection, the analysis projection, origin, pixel transform, Mars datum/radius, units, and coverage. Do not use Earth's Web Mercator or Earth distance helpers for Mars calculations.

The region bundle contains manifest.json, an imagery preview, elevation and slope grids, a valid-data mask, and science-stops.json. Raster row 0 is the north edge; column 0 is the west edge. A1 supplies conversion functions and three landmark checks. B2 converts these coordinates into its 3D axes explicitly.

The draft design is also available in `shared/api-contract.md`. A3 and B1 maintain that contract together, then implement `shared/schema.json` and fixtures. Keep this overview synchronized when the contract changes.

**Service contract, schema version 1 (design only):**

- GET /api/region: manifest, layer paths, supported parameter bounds, science stops and source records.
- POST /api/plan: requestId, schemaVersion, datasetVersion, baseXY, targetId, maxSlopeDeg, speedMPerMin, totalBudgetMin, reserveMin, dwellMin, blockedPolygonsXY. Returns results for both route modes.
- POST /api/rehearse: the same dataset and constraint fields plus currentXY, elapsedMin, remainingBudgetMin, targetId, baseXY, and blockedPolygonsXY. Returns immediateReturn and continueThenReturn assessments. remainingBudgetMin excludes elapsed time; the server must not subtract elapsedMin a second time.
- POST /api/brief: requestId, planId, selectedRouteMode, question. Returns answer text, sourceIds, metricRefs, and mode: model or template. The server retrieves the saved plan; it does not trust route metrics supplied by a chat prompt.

A route result contains status, pathXY, distanceM, ascentM, maxSlopeDeg, meanSlopeDeg, travelMin, dwellMin, reserveMin, totalRequiredMin, marginMin, profile, sourceIds, datasetVersion, modelVersion, and warnings. A round trip contains distinct outbound and return legs plus combined metrics. A rehearsal continuation contains current-to-target and target-to-base legs. Each profile sample contains distanceM, elevationM, and slopeDeg.

Statuses: ok, over_budget, no_path, invalid_input, data_unavailable. If there is no path, path and unsupported metrics are null, not invented zeroes. The service records a planId and input hash. B1 discards results whose requestId does not match the latest input. Reports and assistant responses always include the active planId; stale answers are invalidated after any mission change.

**Hour 1 handoff:** A3 and B1 publish the schema and sample responses for success, identical routes, over-budget, no-path, invalid input, and missing data. Fixtures are explicitly synthetic development inputs. Group B uses them immediately while Group A processes real data.

## 7. Two-day schedule

These are elapsed build hours after the team's permitted kickoff, not a requirement to work continuously. Assume a 09:00 start on November 14, adjust to the local event, preserve a full overnight rest period, and obey an earlier local pitch deadline. The official event page lists November 14–15 and a November 15, 23:59 local-time submission close; B1 must confirm how the team's registered event applies that deadline.

| Time | Group A | Group B | Shared acceptance gate |
|---|---|---|---|
| H0–1 | Confirm data inventory and API draft; implement schema/fixtures; initialize Python project | Confirm scaffold and screen flow; initialize React/Vite project and pin dependencies | Both groups use the same versioned contract |
| H1–3 | Verify crop, sources, grid and coordinates | Build map shell; 3D using labeled test grid; assistant fixtures | Data-access decision; scope fixed |
| H3–6 | Terrain preparation; shortest route; API stub | Layer controls, mission inputs, comparison cards, terrain viewer | First real terrain appears in both views |
| H6–9 | Second route mode, return legs, science records | Connect actual results, add evidence panel and route playback | Full base → destination → base flow |
| H9–12 | Rehearsal calculations; numerical checks | Corridor event, remaining-time control, grounded assistant | Real end-to-end rehearsal; deploy early |
| Overnight | Rest; no dependency on someone coding all night | Rest | Known issues recorded |
| H24–27 | Edge cases and scenario validation | 3D performance, usability and assistant evaluation | All core features operate together |
| H27–30 | Cross-check final metrics and sources | Mission report, public preview, backup packaging | Feature freeze |
| H30–33 | Independent science review | User trial, recording and pitch rehearsal | Submission candidate ready |
| Before local deadline | Final checks with whole team | Submit; verify receipt and public links | Aim for at least two hours of buffer |

## 8. Success measures and meaningful checks

- Numerical checks: flat terrain distances, known-plane slope, blocked corridors, invalid coordinates, no-data boundaries, round-trip time accounting, and a no-route case.
- Integration checks: the same three landmarks and route points agree in 2D and 3D; a changed scenario invalidates old reports and assistant context.
- Performance targets, to measure rather than promise: cached region load under five seconds, route response under two seconds for the chosen grid on the demo machine, 3D interaction near 30 fps on that machine. Reduce mesh density or crop extent when needed.
- Assistant evaluation: at least ten prepared questions, including unsupported questions; route facts match returned metrics and citations resolve to actual evidence.
- Usability: three unfamiliar testers can choose a destination, compare routes, trigger an event, and explain the result without coaching. Record failures and fix the main obstacle.
- Reproducibility: one teammate who did not package the app can run it and reproduce the stored scenario.

Use synthetic grids to test mathematics and real data to demonstrate the product. Human validation of scientific meaning remains necessary even when automated checks pass.

## 9. Submission and demonstration

Prepare a compact live sequence: select science target → compare routes → inspect the real terrain in 3D → inject a clearly hypothetical corridor closure → compare return choices → ask the assistant why → open supporting evidence.

Use a two-minute internal rehearsal target, then adapt the actual video/slides and pitch to the current 2026 submission instructions and local event requirements. Do not reuse old-year slide/video limits as current rules.

Include: project description, code and dependencies, runnable instructions, public demo, data sources and processing steps, assumptions, known limits, AI/tool attribution where required, and licenses. NASA's published terms require resource citations and appropriate license documentation. B1 verifies all six people are registered on the team and that the final submission is actually acknowledged.

Before kickoff, assign roles and review published data/docs. Confirm the current event's policy before undertaking challenge-specific implementation; this plan does not assert a blanket permission to build before the event.

## 10. What to cut if time runs short

Preserve a small version of all three requested capabilities: functional routing, a basic 3D terrain view, and a grounded AI assistant. Cut extra regions, fancy transitions, avatars, open-ended agent actions, elaborate textures, and multi-stop optimization first. If the AI provider fails, retain the mission explanation as a labeled deterministic fallback; do not describe that fallback as a live AI response. If 3D fails on a device, show the 2D view and document the limitation.

## Repository map and immediate next tasks

| Path | Owner | Current contents / next work |
|---|---|---|
| `server/` | Group A; B3 owns assistant module | Ownership README; implement Python service and modules |
| `server/tests/` | Group A | Test guidance; add numerical/API tests during implementation |
| `web/src/mission/`, `web/src/map/` | B1 | Ownership READMEs; implement state, inputs and 2D map |
| `web/src/terrain/` | B2 | Ownership README; implement actual-terrain mesh/playback |
| `web/src/assistant/`, `web/src/evidence/`, `web/src/report/` | B3 | Ownership READMEs; implement explanations, evidence and report |
| `web/public/`, `web/tests/` | Group B | Asset and integration-test guidance |
| `shared/`, `shared/fixtures/` | A3 + B1 | API design and fixture requirements; JSON schema/fixtures pending |
| `data/raw/`, `data/region/`, `data/sources/` | A1 + A3 | Data-handling READMEs; actual inputs and derived products pending |
| `docs/plans/` | Whole team | Shared plan plus the two detailed group plans |
| `docs/` | Owners named in templates | Architecture, processing, validation, demo, submission and runbook templates |
| `scripts/` | A1, A3 and B2 | Automation guidance; executable scripts pending |

**Next work by person:** A1 verifies the real terrain crop; A2 starts routing against synthetic mathematical test grids; A3/B1 finalize the machine-readable contract together; B1 initializes the frontend and fixture-backed mission flow; B2 builds the terrain viewer against that same grid format; B3 builds the evidence/report flow before connecting a model. A3 initializes the Python project and records its launch/test commands. B1 does the equivalent for the web project. The folder skeleton does not complete those tasks.

Use short task branches after the first commit exists. Group A and Group B work in the same repository and integrate small changes frequently. Do not create two independent applications that only meet at the end. See `CONTRIBUTING.md` for ownership and handoff rules.

## Sources

- Official brief: https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/
- Event dates, team size and submission window: https://www.spaceappschallenge.org/2026/
- Participant terms and source requirements: https://www.spaceappschallenge.org/legal/
- USGS Jezero products: https://astrogeology.usgs.gov/search/map/mars-2020-jezero-crater-landing-site-products
- USGS CTX science DEM: https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic
- HiRISE terrain quality documentation: https://stac.astrogeology.usgs.gov/docs/data/mars/hirise_dtms/
- Mars Trek layer documentation: https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars
- Perseverance map and context: https://science.nasa.gov/mission/mars-2020-perseverance/location-map/
- Science observations for destination cards: https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/
