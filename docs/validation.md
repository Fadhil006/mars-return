# Group A validation record

Initial real-data validation on 12 November 2026; expanded on 13 November; re-run on 14 November 2026 after real sampling sites, the rover traverse layer and the reach/stress calculations were added. Linux / Python 3.14.8. This establishes backend behavior, not a completed Space Apps submission or certified Mars navigation.

## Dataset and environment

- Dataset: `9a4cd252af07db1a`; model: `grid-constant-speed-v1`.
- Actual CTX elevation and matching orthoimage from the recorded USGS/PDS sources, source SHA-256 verified.
- 3 km square, 150 × 150 cells at 20 m; 22,500 elevation cells, 21,904 cells with valid slope neighborhoods and combined coverage.
- Exact installed dependencies: `server/requirements.lock`. Source/analysis CRS and transforms: `data/region/manifest.json`.
- The base is a hypothetical grid location. The five destinations are **real Perseverance sampling sites**, each placed at the rover's last end-of-drive localization on or before its first sample was sealed (NASA Mars 2020 waypoints). They are rover positions, not drill-hole coordinates.

## Automated checks

```sh
.venv/bin/python -m pytest server/tests -q
.venv/bin/python -m server.export_schema --check
git diff --check
```

Result on 14 November: **110 passed** in the project environment. The 13 November run (102 tests) also passed in a separately created clean virtual environment on the same host; the clean-environment run has not been repeated for the 8 new tests. All 32 pinned dependencies installed there; `pip check` found no broken requirements, and schema consistency/whitespace checks passed. One dependency deprecation warning: Starlette's HTTPX TestClient integration recommends a newer client. The pinned combination currently passes; no warning was hidden.

Coverage includes coordinates/boundaries, known-plane slope, missing-data support under shifted resampling, invalid resolution/input rejection, layer checksums, A* versus independent Dijkstra for both objectives, obstacles/diagonal corners, distance-weighted slopes, zero-distance legs, round trips, reserve/dwell accounting, closure/reset, API errors, request limits, trusted-plan expiry/eviction, symlink rejection, fixtures and portable packaging.

Parallel GPT-6.1 Sol medium workers added API boundary regressions and 48 seeded tiny-grid comparisons per objective against an independent Dijkstra oracle. They found a finite-but-subnormal speed overflow: mission calculations now reject non-finite derived times with HTTP 422 instead of response-validation failure/500. Both planning and rehearsal have regression coverage. An initial clean-environment run overlapped unfinished tests and failed; the finalized suite was rerun successfully in both environments.

## Real-data scenarios

Reproduce with `.venv/bin/python -m scripts.validate_demo` after preparation. Full inputs, returned paths/profiles, outputs and versions are in `validation-results.json`.

| Scenario | Result | Distance | Required time | Margin |
|---|---|---:|---:|---:|
| Default shortest round trip (base to Sid) | `ok` | 2,209.71 m | 103.66 min | +76.34 min |
| Default slope-penalized round trip | `ok` | 2,242.84 m | 104.76 min | +75.24 min |
| Closure: immediate return | `ok` | 540.00 m | 38.00 min | +12.00 min |
| Closure: continue then return | `over_budget` | 2,061.67 m | 98.72 min | −48.72 min |
| Full separating closure: either option | `no_path` | null | null | null |

### All five sampling sites, shortest objective, with the closure stress test

Stress test: eight 60 m-radius closures placed in turn along the planned way home; the return is recalculated from the site each time.

| Site (NASA samples) | Round trip | Margin | Closures survived | Worst margin | Largest detour |
|---|---:|---:|---:|---:|---:|
| Roubion, Polygon Valley (1) | 2,885.00 m | +53.83 min | 8/8 | +50.94 min | 86.86 m |
| Rochette, Artuby Ridge (2, 3) | 2,193.62 m | +76.88 min | 8/8 | +75.77 min | 33.14 m |
| Brac, South Séítah (4, 5) | 1,727.35 m | +92.42 min | 8/8 | +90.86 min | 46.86 m |
| Issole, South Séítah (6, 7) | 1,804.51 m | +89.85 min | 8/8 | +88.75 min | 33.14 m |
| Sid, Octavia E. Butler Landing (8, 9) | 2,209.71 m | +76.34 min | 8/8 | +75.24 min | 33.14 m |

At 20 m resolution and a 15-degree limit this part of the crater floor is forgiving: every single closure has a short detour. That is a result, not a guarantee; hazards smaller than a cell are invisible to it.

### Return envelope with 50 minutes remaining (30 walking minutes after reserve)

| Case | Ground reachable at all | Ground from which return still fits |
|---|---:|---:|
| No closure | 8.751 km² | 1.929 km² |
| With the rehearsal closure | 8.645 km² | 1.848 km² |

The envelope's return time at Sid equals the point-to-point return leg to within 1e-6 m.

## Cross-mission check: rover localizations against the orbital grid

125 Perseverance end-of-drive localizations (sols 13–404) fall inside the crop. Rover elevation minus prepared CTX elevation at the containing cell: mean **−0.82 m**, median −0.87 m, standard deviation **1.98 m**, largest absolute difference 4.79 m. The steepest grid slope at any real rover stop is 6.77 degrees, inside the default 15-degree limit.

This compares two NASA products against each other. It shows they are registered consistently in this frame; it is not an independent survey, and both use the same reference surface conventions.

Default assumptions: 30 m/min, 180-minute total budget, 10-minute dwell, 20-minute reserve, 15-degree slope ceiling. Closure rehearsal has 50 minutes remaining; its 130-minute elapsed history is not subtracted again.

Synthetic regression: 900 m outbound + 900 m return at 30 m/min, 10-minute dwell and 20-minute reserve requires 90 minutes, leaving 90 minutes from a 180-minute budget. This is arithmetic, not an astronaut prediction.

## Independent numeric and reproducibility checks

- Original DEM sampled directly at projected coordinates corresponding to local `[510,1510]`: **−2554.556640625 m**. Prepared elevation is identical; difference **0 m** at this checked sample. This does not establish accuracy everywhere.
- Independent follow-up audit verified the two raw-source hashes, all five declared asset hashes, the manifest-derived dataset version, and exact source/prepared elevation equality at additional local cell centers `[2250,2370]` and `[870,570]`. All three published hypothetical destinations also returned feasible results for both objectives through the API.
- Returned leg distances independently summed using Euclidean distances between XY vertices; all checked legs match within 1e-6 m.
- Removing the hypothetical closure restores the baseline result after intervening closure/no-path evaluations.
- Ran complete preparation twice: byte-identical manifest/version, with matching exported-layer checksums.
- A local validation run measured default plan calculation at **18.64 ms**, total validation **292.22 ms**. Single warm local measurements, not load benchmarks or latency guarantees.

## Portable bundle and actual HTTP smoke test (13 November, previous dataset)

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
- Sampling-site positions are rover localizations; the drill targets lie within arm's reach of them and no positional uncertainty is published.
- The 13 November portable-bundle and HTTP smoke test below was not repeated for dataset `9a4cd252af07db1a` or the two new endpoints.
- Direct challenge-page TLS validation failed; the official-domain indexed description was read, but current Resources-tab and submission requirements need confirmation.
- Native DEM resolution only: preprocessing deliberately rejects up/downsampling until conservative coarsening is implemented and tested.
- Grid slope, constant speed, and hypothetical events do not model small hazards, live conditions, suit performance, fatigue, physiological safety, or actual return capability.
- Plan records are process-local and expire; use one worker. Public hosting needs appropriate reverse-proxy/rate-limit controls.
