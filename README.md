# MARS RETURN

A Mars mission rehearsal project for the NASA Space Apps Martian Map challenge: explore real terrain, compare routes, and ask **“Can we still get back?”** when a scenario changes.

**Status:** folder structure and planning documents only. No runnable frontend/backend, dependency installation, scientific datasets or application tests have been added yet.

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
│   ├── api-contract.md     # Draft interface; A3 + B1 own changes
│   └── fixtures/           # Synthetic development responses, still to create
├── data/
│   ├── raw/                # Local source downloads, ignored by Git
│   ├── region/             # Prepared region bundle; products still to create
│   └── sources/            # Source attribution and acquisition records
├── docs/
│   ├── plans/              # Shared plan and both detailed group plans
│   └── ...                 # Architecture, validation, demo and submission guides
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

The suggested stack is React/TypeScript/Vite + Three.js and Python/FastAPI + NumPy/Rasterio. A3 initializes the Python environment; B1 initializes the web application. They will add real setup commands and compatible dependency locks when those projects exist. There is no install or run command for this structural scaffold.

Keep downloaded rasters and generated bulk data out of ordinary Git commits. Record sources and reproducible acquisition steps. Keep secrets in ignored local environment files. The starter environment file names are proposed settings and are not read by code yet.

## Scientific scope

Use actual imagery/elevation for the region. The base, blocked corridor, speed, time budget and slope ceiling are hypothetical scenario inputs. Derived routes are model results, not certified astronaut navigation or safety guidance. Preserve missing-data masks and show data resolution.

## Project links

- [GitHub repository](https://github.com/Fadhil006/mars-return)
- [Official challenge](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/)
- [Architecture](docs/architecture.md)
- [Submission checklist](docs/submission-checklist.md)
