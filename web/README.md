# Browser application

React + TypeScript + Vite, with Three.js for the terrain view. Ownership: `mission/` and `map/` B1, `terrain/` B2, `assistant/`, `evidence/` and `report/` B3. Keep the interface aligned with `../shared/api-contract.md`; `src/mission/types.ts` mirrors `../shared/schema.json`.

The design is in `../docs/design/design.md`; the build plan is `../docs/plans/04-group-b-build-plan.md`.

## Commands

Run these from `web/`. The API must be running for anything beyond the unit tests (see `../docs/run-demo.md`).

```sh
npm install
npm run dev        # Vite on http://localhost:5173, proxying /api to http://127.0.0.1:8000
npm run build      # typecheck, then build web/dist; the API serves it on port 8000
npm run typecheck  # tsc --noEmit
npm test           # vitest unit tests in tests/
```

## Layout

- `src/mission/` — contract types, API calls, the single mission reducer (`state.ts`), controls, route comparison, rehearsal strip.
- `src/map/` — 2D map in local metres and the grid layers (slope, missing data, return envelope).
- `src/terrain/` — 3D heightfield at 1× vertical scale.
- `src/evidence/`, `src/assistant/`, `src/report/` — sources and limits, the grounded assistant, the printable mission summary.
- Styles: tokens and shared primitives in `src/styles.css`; each component imports its own CSS file.

## Rules

- The browser displays Group A's numbers. It calculates only differences between returned values, the playback position, and the scenario inputs it sends.
- Any input change marks results outdated; rehearsal, assistant, stress test and report are disabled until matching results return.
- The assistant panel only shows what `POST /api/brief` returns. No provider key ever reaches the browser.
