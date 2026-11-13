# MARS RETURN

A Mars mission rehearsal project for the NASA Space Apps Martian Map challenge:
explore real terrain, compare routes, and ask **“Can we still get back?”** when a
scenario changes.

**Status:** the Group A backend is implemented (shared contract, data
preprocessing, routing, mission/rehearsal arithmetic, API, evidence briefs, and
tests). The frontend has **not** been implemented. The `web/` tree exists on
this branch only because it is inherited from `origin/main`; it contains 10
tracked placeholder README files and no React/TypeScript/Vite application code.

## Start here

1. Read the [shared team plan](docs/plans/00-martian-map-team-plan.md).
2. Follow [Group A's plan](docs/plans/01-group-a-data-and-routing.md) or [Group B's plan](docs/plans/02-group-b-experience-and-demo.md).
3. Confirm the [shared API design](shared/api-contract.md) before implementing either side.
4. Use the [collaboration guide](CONTRIBUTING.md) for ownership and handoffs.

## Group A backend

Local, offline-first route planning service for a Mars rover traverse around
Jezero Crater. It contains the shared contract, data preprocessing, coordinate
transforms, routing, mission budget arithmetic, rehearsal planning,
evidence-backed briefs, and tests. There is no frontend application code in this
branch; `web/` still contains only placeholder READMEs inherited from
`origin/main`.

Quick start from the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python server/preprocess.py --synthetic-fallback
.venv/bin/pytest server/tests -q
.venv/bin/uvicorn server.api:app --port 8000
```

See [server/README.md](server/README.md) for full setup/run/test instructions,
and [docs/data-method.md](docs/data-method.md) /
[docs/validation.md](docs/validation.md) for methodology and measured results.

Key Group A files:

| Path | Purpose |
| --- | --- |
| `shared/schema.json` | Versioned request/response contract (`schemaVersion: 1`) |
| `shared/fixtures/` | Synthetic request/response fixtures |
| `server/coordinates.py` | Pixel <-> local metric coordinate transforms |
| `server/preprocess.py` | Raster -> bounded metric grid + manifest |
| `server/routing.py` | 8-neighbour A* (`shortest`, `slope_penalized`) |
| `server/mission.py` | Plan/rehearsal timings, ascent, budget margins |
| `server/evidence.py` | Science-stop evidence + template briefs |
| `server/api.py` | FastAPI service |
| `server/tests/` | Pytest unit + integration suite |
| `data/region/` | Committed synthetic fallback dataset |

## Repository structure

The Group A backend is implemented. The `web/` tree is inherited from
`origin/main` and is not part of the Group A implementation.

```text
mars-return/
├── server/                 # Group A: data processing, routing and API
│   ├── api.py              # FastAPI endpoints
│   ├── evidence.py         # Grounded template briefs
│   ├── coordinates.py      # Pixel <-> metric transforms
│   ├── preprocess.py       # Raster -> metric grid
│   ├── routing.py          # A* routing modes
│   ├── mission.py          # Budget and rehearsal arithmetic
│   └── tests/              # Numerical, coordinate, budget and API tests
├── web/                    # Frontend NOT implemented; placeholder READMEs only
│   ├── README.md
│   ├── public/README.md
│   ├── src/
│   │   ├── README.md
│   │   ├── assistant/README.md
│   │   ├── evidence/README.md
│   │   ├── map/README.md
│   │   ├── mission/README.md
│   │   ├── report/README.md
│   │   └── terrain/README.md
│   └── tests/README.md
├── shared/
│   ├── api-contract.md     # Draft interface; A3 + B1 own changes
│   ├── schema.json         # Implemented Group A contract
│   └── fixtures/           # Synthetic development responses
├── data/
│   ├── raw/                # Local source downloads, ignored by Git
│   ├── region/             # Prepared region bundle (committed synthetic fallback)
│   └── sources/            # Source attribution and acquisition records
├── docs/
│   ├── plans/              # Shared plan and both detailed group plans
│   └── ...                 # Architecture, data method, validation and demo guides
└── scripts/                # Future preparation, validation and packaging tools
```

## Team ownership

| Person | Responsibility |
|---|---|
| A1 | Data preparation, projection, coordinates and provenance |
| A2 | Routing, return paths and scenario arithmetic |
| A3 | Science destinations, API integration and numerical review |
| B1 | User flow, 2D map, mission state and final submission coordination |
| B2 | 3D terrain, route playback, performance and deployment packaging |
| B3 | AI explanations, source panels, mission report and presentation |

## Development status

The Group A backend is runnable with the pinned Python dependencies in
`requirements.txt` and passing tests. The suggested frontend stack remains
React/TypeScript/Vite + Three.js; the `web/` tree is still placeholder
documentation. Group B will add the web application, and B3 will add
`server/assistant.py`.

Keep downloaded source rasters and other large generated bulk data out of
ordinary Git commits. The small deterministic synthetic fallback in
`data/region/` is committed intentionally so the backend runs offline. Record
sources and reproducible acquisition steps. Keep secrets in ignored local
environment files.

## Scientific scope

Use actual imagery/elevation for the region. The base, blocked corridor, speed,
time budget and slope ceiling are hypothetical scenario inputs. Derived routes
are model results, not certified astronaut navigation or safety guidance.
Preserve missing-data masks and show data resolution.

## Project links

- [GitHub repository](https://github.com/Fadhil006/mars-return)
- [Official challenge](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/)
- [Architecture](docs/architecture.md)
- [Submission checklist](docs/submission-checklist.md)
