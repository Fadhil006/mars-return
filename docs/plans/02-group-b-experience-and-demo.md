# Group B — Map Experience, 3D, AI, and Demonstration

Three-person implementation plan • Planning draft, 12 November 2026

> For agentic workers: Use superpowers:executing-plans if later authorized to implement. This document currently assigns work to the six human teammates; it does not authorize automatic implementation or delegation. Checkboxes track work still to be done.

**Goal:** Make a real-data Mars excursion understandable and interactive: inspect science, compare routes, rehearse in 3D, respond to a change and understand the evidence.

**Architecture:** One browser application owns the current mission state and displays Group A's versioned results in synchronized 2D, 3D and explanation views. It begins against clearly labeled development fixtures, then switches to the real service without changing the contract.

**Proposed stack:** React, TypeScript, Vite, Three.js, a simple bounded map/image canvas, browser integration tests, and a server-side model adapter. Avoid a new database, authentication system, global planetary viewer or agent framework.

**Spec:** [Shared project plan](00-martian-map-team-plan.md). Read its API and coordinate conventions before this document.

## Repository status — structure created, 12 November 2026

Repository: `/home/fadhil/Projects/mars-return` · Remote: `https://github.com/Fadhil006/mars-return.git`

The folders, ownership READMEs, shared API design, collaboration guide and documentation templates now exist. This is a structural scaffold: application modules, dependency manifests/lockfiles, machine-readable schemas, fixtures, data products and tests are still to be implemented. No working app, scientific result or passing application test suite is claimed.

The authoritative plans live in `docs/plans/` in the repository. The chat output copies are synchronized snapshots. All repository paths below are relative to the repository root. Existing README/template files are starting points; unchecked implementation tasks remain open.

## Global constraints

- The map, 3D view, report and assistant must refer to the same active planId and datasetVersion.
- Group A owns scientific numbers. The browser does not calculate competing route/time results.
- 3D geometry comes from actual elevation; unknown cells remain visibly absent or masked.
- Scenario events, travel speed, slope limits, base location and budget are labeled assumptions.
- Source dates, data resolution and limitations are easy to find.
- A failed route never displays an old successful route as current.
- Model credentials remain server-side; user text does not authorize arbitrary external requests or route changes.

## Review focus

1. Rapid input changes: an old request must not overwrite a newer mission. B1 tests request IDs and delayed responses.
2. Invalid or unavailable results: no-path, missing layers and expired plans need clear states. B1 owns these tests.
3. 3D correspondence: terrain orientation, vertical scale and route placement must match 2D. B2 checks A1's landmarks.
4. Unsupported assistant claims: the answer must distinguish missing evidence from known facts. B3 evaluates citation and metric consistency.
5. Degraded environment: model outage, slow network and unavailable WebGL must preserve an honest useful experience. B2/B3 test fallbacks.

## People and outputs

| Person | Owns | Deliverable | Reviewer |
|---|---|---|---|
| B1 | Product flow, 2D map, mission state and integration | End-to-end interactive planner | A3 |
| B2 | Terrain viewer, route playback, performance and deployment packaging | Real-data 3D rehearsal plus runnable build | A1 for data, B1 for interaction |
| B3 | Assistant, mission report, story and presentation | Grounded explanation experience | A3 |

B1 is Group B's coordinator and owns scope decisions and final submission confirmation. B3 owns the presentation content, with science review from A1/A3 and metric review from A2. This avoids leaving a single person responsible for all polish, hosting and documentation at the end.

## Implementation files and ownership

The parent directories now exist. The code, data and test files listed below are planned deliverables, not completed modules. The listed documentation files exist as starter templates and still need evidence from the build.

| File/directory | Owner | Purpose |
|---|---|---|
| web/src/mission/types.ts | B1 with A3 | Types matching the shared schema |
| web/src/mission/api.ts | B1 | Validated service calls and request IDs |
| web/src/mission/state.ts | B1 | Inputs, results, invalidation and replay state |
| web/src/map/MissionMap.tsx | B1 | Bounded 2D imagery/layer view |
| web/src/mission/MissionControls.tsx | B1 | Destination and scenario controls |
| web/src/mission/RouteComparison.tsx | B1 | Route metrics, margins and status |
| web/src/evidence/EvidencePanel.tsx | B3 | Sources, dates and limits |
| web/src/terrain/TerrainView.tsx | B2 | Mesh, texture and camera |
| web/src/terrain/RoutePlayback.tsx | B2 | Position along the actual route |
| web/src/assistant/MissionAssistant.tsx | B3 | Questions, explanations and citations |
| server/assistant.py | B3 | Model adapter and deterministic fallback |
| web/src/report/MissionReport.tsx | B3 | Printable/exportable mission summary |
| web/tests/mission.spec.ts | B1 | Main integration flow and stale results |
| web/tests/terrain.spec.ts | B2 | Transform and visual reference checks |
| web/tests/assistant.spec.ts | B3 | Unsupported questions and context changes |
| docs/demo-script.md | B3 | Live demo and judging narrative |
| docs/submission-checklist.md | B1 | Current requirements and completion record |
| docs/run-demo.md | B2 with A3 | Hosted/local startup and backup steps |

## B1: Product, 2D map and integration owner

### Task B1.1 — Define the user journey and shared state (H0–3)

**Inputs:** Shared spec and A3's schema/fixtures.

**Output:** A clickable shell where the six members can agree on the complete flow.

- [ ] Initialize the React/TypeScript/Vite project in the existing `web/` folder, preserving its ownership READMEs. Record pinned dependencies, scripts and launch commands in `web/README.md`.
- [ ] Create one main screen: mission controls on the left, map/3D in the center, route comparison and evidence on the right. On smaller screens stack these into simple tabs.
- [ ] Use a short flow: choose destination → inspect evidence → compare routes → rehearse → change scenario → review return options → export.
- [ ] Build controls for destination, route mode, time budget, slope ceiling, speed, dwell and reserve. Keep advanced assumptions collapsed but clearly accessible.
- [ ] Separate input state, pending request state, last result and rehearsal position. Reset or invalidate downstream state when inputs change.
- [ ] Review `shared/api-contract.md` and agree all schema fields and units with A3. Use fixtures marked “Development sample data” until real region data is connected.
- [ ] Show an understandable initial mission instead of a blank map requiring geographic expertise.

**Acceptance:** Another teammate can describe the planned flow after clicking the shell, and Group A recognizes every field in the requests.

### Task B1.2 — Display the real region and route comparisons (H3–9)

**Interface:** renderRegion(regionBundle), submitPlan(PlanRequest) and displayPlan(PlanResult), implemented through the typed API layer.

- [ ] Render the aligned image in local meters, with visible bounds, scale and orientation. Match A1's north-up row convention.
- [ ] Add imagery, slope and science-stop layer controls. Explain that slope is derived from elevation, and distinguish geological interpretation from measured chemistry.
- [ ] Show the hypothetical base and source-backed destinations. Include an accessible list for choosing markers without precise mouse interaction.
- [ ] Connect the real route endpoint by H6–9. Show outbound and return legs with distinct styling, avoiding a fabricated separation when they overlap.
- [ ] Display distance, travel time estimate, slope statistics, dwell, reserve and remaining margin with units. Round for readability while retaining full-precision calculations on the server.
- [ ] Show a side-by-side comparison with differences calculated from returned numbers. Describe only the properties that actually improve.
- [ ] Make no_path, over_budget, invalid_input and data_unavailable distinct. Identical routes are an acceptable result, not an error.
- [ ] On any input change, mark the existing result as outdated and disable export/assistant actions until a matching result returns.

**Acceptance:** One actual mission is usable end-to-end; selecting a destination changes both the displayed evidence and service request; stale results cannot overwrite a newer selection.

### Task B1.3 — Make the rehearsal interactive (H9–12)

- [ ] Share one currentXY with B2's route-playback view.
- [ ] Provide a clear “Hypothetical corridor blocked” scenario control, with a visible polygon and reset action.
- [ ] Provide a remaining-time control distinct from the original total budget. Explain whether values are initial or remaining.
- [ ] Request immediate return and continuation-then-return from Group A. Show the feasibility/margin of both options, with no automatic claims about physical survival.
- [ ] When the event changes, invalidate previous suggestions and ask the assistant only about the new plan.
- [ ] Handle a blocked current position or missing route without moving the marker to make the result look successful.

**Acceptance:** A visitor can change one assumption and understand both the updated route and the reason for the new margin.

### Task B1.4 — Usability, integration and submission (H24–33)

- [ ] Test the core flow with three unfamiliar people and record where they hesitate or misinterpret a label.
- [ ] Verify keyboard controls, readable contrast, units, loading indicators, errors and screen-size behavior.
- [ ] Run integration checks for delayed responses, invalid positions, unavailable data and scenario reset.
- [ ] Maintain the feature freeze at H30. Only fix issues affecting the core demo, correctness or submission.
- [ ] Confirm the actual 2026 submission fields, presentation limits and local deadline, and record them in the checklist.
- [ ] Verify all six participants, source/license documentation, public links and actual submission receipt.

## B2: 3D terrain and rehearsal owner

### Task B2.1 — Build a simple viewer against the shared contract (H1–6)

**Inputs:** Synthetic development grid first; A1's actual region bundle by H3–6.

**Output:** Real terrain that can be rotated and inspected, with no dependency on the completed route algorithm.

- [ ] Build a heightfield mesh with orbit/zoom controls. A restrained directional light and neutral Mars-colored material are sufficient initially.
- [ ] Define the conversion explicitly: local east → Three.js X; local north → negative Z; elevation relative to a stored origin → Y. Convert every route point with the same function.
- [ ] Start with true vertical scale 1×. If exaggeration is later offered, label it prominently and never alter analysis calculations.
- [ ] Texture the mesh with A1's aligned image; mask holes instead of filling missing terrain with a smooth invented surface.
- [ ] Cap the display mesh at approximately 256 × 256 vertices initially. Preserve the analysis grid separately and test performance on the actual demo laptop.
- [ ] Verify three landmarks and one elevation difference with A1. Keep a screenshot/reference record of the check.

**Acceptance:** The same landmarks occupy matching locations in 2D and 3D; the data-derived shape is clear at 1× scale; the viewer remains responsive.

### Task B2.2 — Put the mission on the terrain (H6–12)

- [ ] Draw the actual returned path over the surface with a small display-only offset to prevent flicker.
- [ ] Show the base, selected science stop and rehearsal marker with readable labels.
- [ ] Animate the marker along the path at a controllable presentation speed. The animation speed is not a prediction of astronaut speed.
- [ ] Let the user pause at a path point and send that actual local coordinate into B1's rehearsal state.
- [ ] Display the hypothetical blocked polygon in the terrain view. Replace paths only when their matching new result arrives.
- [ ] Offer one useful camera mode: overview or follow the route. Detailed walking avatars and first-person controls are optional extensions.

**Acceptance:** The same current position and scenario appear in both views; pressing the return action displays Group A's actual updated geometry.

### Task B2.3 — Deploy, measure and prepare the backup (H24–30)

- [ ] Measure terrain frame rate and region payload size on the demo laptop. Aim for approximately 30 fps, but report actual measurements.
- [ ] Reduce mesh density or texture size if needed; never substitute different terrain without labeling it.
- [ ] Test WebGL-unavailable behavior and keep the 2D workflow functional.
- [ ] Package the frontend, prepared data and API with A3; use one deployment origin where possible.
- [ ] Test the public URL on another device without being logged in.
- [ ] Prepare a local launch path and a prerecorded core demo, respecting the event's actual media limits.
- [ ] Ask a teammate who did not package it to run the local version without help.

## B3: Grounded assistant, mission report and presentation owner

### Task B3.1 — Build the explanation before the model (H1–6)

**Inputs:** A3's evidence records and fixture PlanResults.

**Output:** A clear explanation/report component that already displays metrics and sources correctly.

- [ ] Design three starter questions: “Why this route?”, “Can I still return?”, and “What evidence supports this destination?”
- [ ] Build a deterministic explanation from the structured result. This is the reliability fallback and reference behavior.
- [ ] Show key metric cards from server fields; do not ask a language model to regenerate or calculate those values.
- [ ] Add source cards with title, mission, date where known, resolution where relevant, and a readable limitation.
- [ ] Draft the science narrative with A3: what question the excursion investigates and why the selected stop matters.

### Task B3.2 — Connect a narrowly scoped AI assistant (H6–12)

**Interface:** build_brief(plan_id, selected_route_mode, question) → answer, sourceIds, metricRefs, mode. A3 supplies server-side lookup of the trusted plan/evidence; B3 owns the model adapter and answer behavior.

- [ ] Use one available model provider chosen by the team. Keep credentials server-side and set a short timeout.
- [ ] Send only the current structured route summary, allowed source excerpts, their IDs, model assumptions and question. A small curated evidence set does not require a vector database.
- [ ] Instruct the assistant to explain calculations already performed, distinguish observations from assumptions, and say when the supplied evidence is insufficient.
- [ ] Require structured sourceIds/metricRefs in the response. Check that every referenced ID exists; reject malformed output.
- [ ] Keep authoritative numbers in deterministic UI fields. Check any numeric claims in generated prose against the allowed plan values; use the template if consistency cannot be established.
- [ ] Do not let chat text alter the map, run code, fetch arbitrary pages or create a new route. Scenario editing remains in explicit UI controls.
- [ ] If the model times out or fails validation, show the deterministic explanation labeled accordingly. Never claim a fallback is generated live by AI.

**Acceptance:** The assistant adds understandable reasoning without inventing terrain, route numbers, current weather, discovery claims or mission authority.

### Task B3.3 — Evaluate the assistant and export a mission summary (H24–27)

- [ ] Test ten questions spanning route comparison, time arithmetic, data sources, resolution, unsupported live weather, unknown obstacles, medical safety, changed scenario, unavailable path and expired plan.
- [ ] Have A3 independently inspect the answers and citations. Record failures and fixes; do not report an accuracy percentage from an informal tiny sample.
- [ ] Build a printable/exportable summary from the current plan: objective, selected destination, base, route(s), assumptions, metrics, sources, dataset/model versions and limitations.
- [ ] Require recalculation before export if any mission input has changed. Include the hypothetical event and resulting return assessment when present.
- [ ] Ensure the report works without a successful model call.

### Task B3.4 — Build a short, evidence-backed pitch (H27–33)

- [ ] Open with the decision problem: an explorer needs to accomplish science while preserving time to return.
- [ ] Show the initial route and explain the chosen scientific destination.
- [ ] Switch to the actual 3D terrain and pause the rehearsal.
- [ ] Apply the clearly hypothetical closure or time reduction. Show how the computed return options change.
- [ ] Ask the assistant why; open the evidence behind the explanation.
- [ ] End with what works now, what was measured, and what future validation would be necessary.
- [ ] Have A2 verify all quantitative claims and A1 verify data attribution.
- [ ] Adapt the recording/slides to the current official and local requirements; a two-minute rehearsal is only an internal planning target.

## Shared handoffs with Group A

| Deadline | Receive | Return |
|---|---|---|
| H1 | Schema and synthetic fixtures | Screen needs, field mismatch report |
| H3 | Real-data feasibility decision | Confirm crop fits the user flow |
| H6 | Region files and landmarks | 2D/3D alignment checks |
| H9 | Actual plan results and evidence | Fully integrated round trip |
| H12 | Rehearsal response | End-to-end scenario demo |
| H27 | Final versions and validated numbers | Assistant/report consistency review |
| H30 | Frozen service/data | Frozen submission candidate |

## Group B definition of done

- [ ] A new visitor can complete the mission flow without coaching.
- [ ] All three requested capabilities work: real route planning, data-derived 3D and grounded AI explanation.
- [ ] Rehearsal changes are visible and their consequences are understandable.
- [ ] Sources and assumptions are accessible in the interface and report.
- [ ] Stale results, unavailable paths and provider failures are handled honestly.
- [ ] Deployment, local backup and recording are tested.
- [ ] Submission content agrees with implemented behavior and verified numbers.

## Scope protection

Keep simple versions of the three core capabilities. Cut elaborate characters, decorative planet transitions, voice, unrelated chat, multiple regions and extra controls before cutting the working mission flow. If a core capability fails, state that clearly in the submission instead of masking it with a prerecorded or invented result. A limited, reproducible real-data demonstration is more useful than an expansive interface whose outputs cannot be defended.
