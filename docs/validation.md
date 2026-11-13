# Group A validation record

Initial real-data validation on 12 November 2026; expanded parallel verification on 13 November 2026, Linux / Python 3.14.8. This establishes backend behavior, not a completed Space Apps submission or certified Mars navigation.

## Dataset and environment

- Dataset: `4492c9ffb6cf016a`; model: `grid-constant-speed-v1`.
- Actual CTX elevation and matching orthoimage from the recorded USGS/PDS sources, source SHA-256 verified.
- 3 km square, 150 × 150 cells at 20 m; 22,500 elevation cells, 21,904 cells with valid slope neighborhoods and combined coverage.
- Exact installed dependencies: `server/requirements.lock`. Source/analysis CRS and transforms: `data/region/manifest.json`.
- Three observation points and base are hypothetical grid locations, **not published sample sites**. NASA Perseverance sample information is separate regional context.

## Automated checks

```sh
.venv/bin/python -m pytest server/tests -q
.venv/bin/python -m server.export_schema --check
git diff --check
```

Final result: **102 passed** in the project environment and **102 passed** in a separately created clean virtual environment on the same host. All 32 pinned dependencies installed there; `pip check` found no broken requirements, and schema consistency/whitespace checks passed. One dependency deprecation warning: Starlette's HTTPX TestClient integration recommends a newer client. The pinned combination currently passes; no warning was hidden.

Coverage includes coordinates/boundaries, known-plane slope, missing-data support under shifted resampling, invalid resolution/input rejection, layer checksums, A* versus independent Dijkstra for both objectives, obstacles/diagonal corners, distance-weighted slopes, zero-distance legs, round trips, reserve/dwell accounting, closure/reset, API errors, request limits, trusted-plan expiry/eviction, symlink rejection, fixtures and portable packaging.

Parallel GPT-6.1 Sol medium workers added API boundary regressions and 48 seeded tiny-grid comparisons per objective against an independent Dijkstra oracle. They found a finite-but-subnormal speed overflow: mission calculations now reject non-finite derived times with HTTP 422 instead of response-validation failure/500. Both planning and rehearsal have regression coverage. An initial clean-environment run overlapped unfinished tests and failed; the finalized suite was rerun successfully in both environments.

## Real-data scenarios

Reproduce with `.venv/bin/python -m scripts.validate_demo` after preparation. Full inputs, returned paths/profiles, outputs and versions are in `validation-results.json`.

| Scenario | Result | Distance | Required time | Margin |
|---|---|---:|---:|---:|
| Default shortest round trip | `ok` | 2,000.00 m | 96.67 min | +83.33 min |
| Default slope-penalized round trip | `ok` | 2,132.55 m | 101.08 min | +78.92 min |
| Closure: immediate return | `ok` | 500.00 m | 36.67 min | +13.33 min |
| Closure: continue then return | `over_budget` | 2,063.68 m | 98.79 min | −48.79 min |
| Full separating closure: either option | `no_path` | null | null | null |

Default assumptions: 30 m/min, 180-minute total budget, 10-minute dwell, 20-minute reserve, 15-degree slope ceiling. Closure rehearsal has 50 minutes remaining; its 130-minute elapsed history is not subtracted again.

Synthetic regression: 900 m outbound + 900 m return at 30 m/min, 10-minute dwell and 20-minute reserve requires 90 minutes, leaving 90 minutes from a 180-minute budget. This is arithmetic, not an astronaut prediction.

## Independent numeric and reproducibility checks

- Original DEM sampled directly at projected coordinates corresponding to local `[510,1510]`: **−2554.556640625 m**. Prepared elevation is identical; difference **0 m** at this checked sample. This does not establish accuracy everywhere.
- Independent follow-up audit verified the two raw-source hashes, all five declared asset hashes, the manifest-derived dataset version, and exact source/prepared elevation equality at additional local cell centers `[2250,2370]` and `[870,570]`. All three published hypothetical destinations also returned feasible results for both objectives through the API.
- Returned leg distances independently summed using Euclidean distances between XY vertices; all checked legs match within 1e-6 m.
- Removing the hypothetical closure restores the baseline result after intervening closure/no-path evaluations.
- Ran complete preparation twice: byte-identical manifest/version, with matching exported-layer checksums.
- A local validation run measured default plan calculation at **18.64 ms**, total validation **292.22 ms**. Single warm local measurements, not load benchmarks or latency guarantees.

## Portable bundle and actual HTTP smoke test

Created `data/packages/jezero-4492c9ffb6cf016a.tar.gz` (302,136 bytes; ignored by Git).

SHA-256: `e1e874ea8953813f3f611dcaf991e9481fc288d862e3ab572a7f0b15c826ffcb`.

Extracted it into a temporary directory, validated the extracted bundle, launched a separate Uvicorn process against that directory, and checked over actual localhost HTTP:

- `/api/region`: active dataset/version and source records.
- `/api/plan`: default real-data results.
- `/api/rehearse`: return-only and no-path results agree with the recorded calculations.
- All four layer assets and `/docs`: HTTP 200.

The process shut down cleanly. Runtime used packaged assets, not raw rasters or external data services. This was a second directory/process on the same machine, **not** an independent-machine installation test. Archive bytes include packaging timestamps; regenerating an archive may change its archive hash while layer checksums remain identical.

## Remaining gates and limits

- Independent three-landmark registration and Group B 2D/3D orientation/vertical-scale review remain outstanding.
- No working browser UI, assistant endpoint/model adapter, hosted deployment, or independent-machine installation was verified.
- Real named sample sites require coordinate provenance before becoming route targets. Current hypothetical points must keep their labels.
- Direct challenge-page TLS validation failed; the official-domain indexed description was read, but current Resources-tab and submission requirements need confirmation.
- Native DEM resolution only: preprocessing deliberately rejects up/downsampling until conservative coarsening is implemented and tested.
- Grid slope, constant speed, and hypothetical events do not model small hazards, live conditions, suit performance, fatigue, physiological safety, or actual return capability.
- Plan records are process-local and expire; use one worker. Public hosting needs appropriate reverse-proxy/rate-limit controls.
