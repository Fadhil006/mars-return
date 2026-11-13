# Mars excursion planner — design brief

Status: requirements baseline, 13 November 2026. No implementation authorized in this design phase. Visual direction and detailed interaction design remain open.

## Purpose and audience

Help a visitor understand a Mars science excursion, inspect the evidence, compare calculated routes, rehearse the trip and understand the consequences of a hypothetical change. The experience must be understandable to visitors unfamiliar with planetary mapping.

The user has confirmed that this project covers all three Group B roles and that everything should be designed before implementation.

## Source and limits

Based on `C:/Users/ADMIN/Downloads/02-group-b-experience-and-demo.md`, a planning draft dated 12 November 2026. The shared project plan, API contract, Group A fixtures and real region bundle have not been supplied. Requirements below come from the brief; names, exact layouts, sample values and interaction details still need design decisions. Nothing here establishes official event or submission rules.

## Required journey

1. Open an understandable initial mission, with the data status visible.
2. Choose a science destination from the map or an accessible list.
3. Inspect its evidence, sources and limitations.
4. Set mission assumptions and request routes.
5. Compare the returned routes and time margins.
6. Inspect matching terrain and rehearse along an actual returned route.
7. Pause at a position and introduce a hypothetical blockage or change remaining time.
8. Compare immediate return with continuation followed by return.
9. Ask for an explanation supported by the active plan and evidence.
10. Export a current mission summary including assumptions, sources and limitations.

## Required design surfaces

- Mission workspace: controls, 2D/3D viewing area, route comparison and evidence. The brief proposes controls left, viewing area center and results right; smaller screens use simple tabs.
- Destination evidence: scientific purpose, source title, mission, date where known, resolution and limitations.
- Route comparison: outbound/return geometry, distance, travel time, slope statistics, dwell, reserve and remaining margin, with units.
- Rehearsal: playback, pause, current position, hypothetical blocked polygon, reset and remaining-time controls.
- Explanation: starter questions, answer, source references, metric references and explicit model/fallback status.
- Report: printable/exportable objective, destination, base, routes, assumptions, metrics, versions, evidence and scenario assessment.

These are required experiences, not a decision to create separate pages for each.

## Behavior and trust requirements

- All views use the same active plan and dataset version.
- Input changes immediately mark previous results outdated and disable dependent assistant/export actions until matching results arrive.
- Late responses must not replace newer results.
- Scientific route/time calculations belong to Group A. Comparison differences can use returned values.
- Separate initial budget, remaining time, estimated travel time and animation speed.
- Clearly identify the hypothetical base, events and operating assumptions.
- Terrain comes from elevation; missing cells remain absent or masked. Start at true vertical scale.
- 2D and 3D share orientation, landmarks, route positions and current rehearsal position.
- The assistant explains supplied results; chat cannot alter routes, fetch arbitrary pages or execute actions.
- Authoritative metrics remain structured fields. Unsupported or inconsistent generated explanations fall back to a labeled template.
- Reports work without a successful model call and cannot export outdated results.
- No claims of physical survival, live weather, validated astronaut operations or unsupported discoveries.

## States to design explicitly

Initial sample mission; loading; valid result; outdated result; no path; over budget; invalid input or position; unavailable region/layer; missing terrain; identical routes; expired plan; blocked current position; assistant timeout or invalid answer; unavailable WebGL; narrow screen; scenario reset.

An unavailable route must never present an earlier successful route as current. The 2D workflow remains useful without WebGL.

## Group A dependencies

Need the authoritative shared plan/API contract, schema and fixtures, units and coordinate conventions, aligned imagery/elevation with missing-data masks, landmark checks, source-backed destinations/evidence, and route/rehearsal responses. Exact field names and service interfaces remain provisional until reviewed together.

Development examples must be visibly labeled and must not be presented as real scientific results.

## Design deliverables before implementation

1. Agreed information architecture and full mission journey.
2. Selected visual direction, typography, colors, spacing and component conventions.
3. Screen designs for the normal flow and important failure states.
4. Interaction specification covering mission changes, route freshness, playback, scenarios, assistant and export.
5. Small-screen and accessibility behavior, including keyboard operation and marker-list selection.
6. Technical design and integration contract, with unresolved Group A dependencies recorded.
7. Reviewable acceptance conditions and demo narrative.

## Scope boundary

One bounded region and one complete reproducible mission flow. Detailed avatars, voice, whole-planet navigation, multiple regions, accounts, a new database and unrelated chat are outside the initial scope.

## Decisions still open

Visual direction and product name; navigation and disclosure details; screen compositions; default mission; route-mode terminology; export format; model provider; deployment target; actual submission requirements. These must not be described as decisions already made by the user.
