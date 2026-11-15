# Frontend tests

Vitest unit tests; run `npm test` from `web/`. They need no running API or browser.

- `mission.spec.ts` (B1): mission state reducer (late responses, failed and expired plans), coordinate helpers, formatting and the radiation estimate.
- `inputs.spec.ts` (B1): typed-number checking and imagery loading.
- `map.spec.ts` (B1): 2D map layers.
- `profile.spec.ts` (B1): elevation profile.
- `decide.spec.ts` (B1): decide-first feedback.
- `terrain.spec.ts` (B2): 3D scene coordinates, terrain mesh, block sides and auto relief.

The assistant is tested on the server side in `server/tests/test_assistant.py`. There are no browser (end-to-end) tests.
