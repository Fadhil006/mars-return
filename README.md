# MARS RETURN

A Mars mission rehearsal project for the NASA Space Apps Martian Map challenge: explore real terrain, compare routes, and ask **“Can we still get back?”** when a scenario changes.

**Status:** Group A backend implemented: terrain preparation, real Perseverance sampling sites and traverse, two route objectives, round-trip/rehearsal calculations, a return envelope, a closure stress test, versioned API, NASA/USGS evidence, and tests. The web application and assistant remain Group B work. See [backend setup](server/README.md), [data processing](docs/data-method.md), and [validation](docs/validation.md) for verified results and outstanding limits.

## Start here

1. Read the [shared team plan](docs/plans/00-martian-map-team-plan.md).
2. Follow [Group A's plan](docs/plans/01-group-a-data-and-routing.md) or [Group B's plan](docs/plans/02-group-b-experience-and-demo.md).
3. Confirm the [shared API design](shared/api-contract.md) before implementing either side.
4. Use the [collaboration guide](CONTRIBUTING.md) for ownership and handoffs.

## Repository structure

```text
mars-return/
├── server/                 # A1/A2/A3: data processing, routing and API; B3: assistant
│   └── tests/              # Numerical, coordinate, budget and API tests
├── web/
│   ├── src/
│   │   ├── mission/        # B1: mission state, controls and route comparison
│   │   ├── map/            # B1: local 2D imagery and overlays
│   │   ├── terrain/        # B2: data-derived 3D terrain and playback
│   │   ├── assistant/      # B3: grounded explanations
│   │   ├── evidence/       # B3: citations and data limitations
│   │   └── report/         # B3: mission summary/export
│   ├── public/             # Small attributed static assets
│   └── tests/              # User-flow and cross-view checks
├── shared/
│   ├── api-contract.md     # Version-one interface; A3 + B1 own changes
│   └── fixtures/           # Explicitly synthetic development responses
├── data/
│   ├── raw/                # Local source downloads, ignored by Git
│   ├── region/             # Prepared region bundle; products still to create
│   └── sources/            # Source attribution and acquisition records
├── docs/
│   ├── plans/              # Shared plan and both detailed group plans
│   └── ...                 # Architecture, validation, demo and submission guides
└── scripts/                # Terrain preparation, validation and packaging tools
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

The backend uses Python/FastAPI + NumPy/Rasterio with a tested dependency lock. React/TypeScript/Vite + Three.js remains the proposed Group B stack. There is no runnable frontend yet.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r server/requirements.lock
.venv/bin/python -m scripts.prepare_demo  # first run downloads ~450 MB of verified USGS inputs
.venv/bin/python -m pytest server/tests
.venv/bin/python -m uvicorn server.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the API. Fetch `/api/region` for the current dataset version and hypothetical demo base/targets. Never use synthetic fixtures as real terrain. Runtime is local/offline after data preparation; no model key is needed for Group A.

Keep downloaded rasters and generated bulk data out of ordinary Git commits. Source records and reproducible acquisition steps are tracked. Keep secrets out of commits. `REGION_DATA_DIR` is read from the process environment; provider settings in `.env.example` are reserved for Group B and no `.env` file is loaded automatically.

## Scientific scope

Use actual imagery/elevation for the region. The base, blocked corridor, speed, time budget and slope ceiling are hypothetical scenario inputs. Derived routes are model results, not certified astronaut navigation or safety guidance. Preserve missing-data masks and show data resolution.

## Project links

- [GitHub repository](https://github.com/Fadhil006/mars-return)
- [Official challenge](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/)
- [Architecture](docs/architecture.md)
- [Submission checklist](docs/submission-checklist.md)
