# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project

MARS RETURN is a NASA Space Apps 2026 "Martian Map" entry: a mission rehearsal tool for Jezero Crater that plans round-trip routes over real terrain and answers "Can we still get back?" when a scenario changes.

Two groups of three people share the repo. **Group A's backend is implemented and tested. Group B's frontend (`web/`) and the assistant are not built yet** — `web/` holds only README placeholders. A folder or README existing does not mean the work is done.

## Commands

Run everything from the repository root (never from `server/`), using the project venv. Python 3.12+.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r server/requirements.lock

.venv/bin/python -m pytest server/tests                    # full suite, about 1 second
.venv/bin/python -m pytest server/tests/test_routing.py    # one file
.venv/bin/python -m pytest server/tests -k "name"          # one test
.venv/bin/python -m server.export_schema --check           # shared/schema.json matches runtime models

.venv/bin/python -m scripts.build_science      # real sampling-site stops + rover traverse from NASA waypoints
.venv/bin/python -m scripts.prepare_demo       # first run downloads ~450 MB of USGS CTX data
.venv/bin/python -m uvicorn server.api:app --host 127.0.0.1 --port 8000   # Swagger UI at /docs
.venv/bin/python -m scripts.validate_demo      # needs the raw DEM; rewrites docs/validation-results.json
.venv/bin/python -m scripts.generate_fixtures  # regenerate synthetic fixtures in shared/fixtures/
.venv/bin/python -m scripts.package_region --region-dir data/region --output data/packages/region.tar.gz
```

There is no linter or formatter configured. `.editorconfig` sets 4 spaces for Python, 2 elsewhere, LF endings.

## Layout

- `server/` — FastAPI backend.
  - `preprocess.py`, `region.py` — prepare and load the terrain bundle
  - `coordinates.py` — projection and pixel↔map conversion
  - `routing.py` — grid routing with two route objectives
  - `mission.py` — round-trip, rehearsal, return-envelope (`reach`) and closure stress arithmetic
  - `evidence.py` — source citations and `trusted_context` (server-calculated metrics by plan ID)
  - `models.py` — request/response models; `export_schema.py` writes `shared/schema.json` from them
  - `api.py` — the versioned API
  - `tests/` — pytest suite
- `scripts/` — data preparation, validation, fixture generation, packaging.
- `shared/` — `api-contract.md`, `schema.json`, and synthetic fixtures. This is the interface between the two groups.
- `data/sources/` — tracked source and acquisition records. `data/region/` — prepared bundle; only `manifest.json`, `science-stops.json` and `rover-traverse.json` are tracked. `data/raw/` — downloads, ignored by Git.
- `docs/` — architecture, data method, validation, demo script, submission checklist. `docs/plans/` holds the authoritative team plans; `03-group-a-winning-plan.md` is the current Group A plan.
- `web/` — planned React/TypeScript/Vite + Three.js frontend. Not started.

## Rules that are easy to break

- **Schema is generated.** After changing `server/models.py`, regenerate `shared/schema.json` with `python -m server.export_schema` and keep `shared/api-contract.md` in step. Shared interface changes need agreement from both groups (owners A3 and B1).
- **Synthetic is never real.** Fixtures in `shared/fixtures/` and synthetic test regions are for development only. Never present them as Mars terrain, and never fall back to them at runtime: missing or corrupt terrain returns 503.
- **Hypothetical stays labelled.** The base, blocked corridor, speed, time budget and slope ceiling are scenario inputs, not certified safety limits. Routes are model results. Keep missing-data masks and data resolution visible.
- **Bulk data stays out of Git.** Raw rasters, generated region assets and `data/packages/` are ignored. Track source records, checksums and small metadata only. No API keys or `.env` files.
- **One worker.** Saved plans and rehearsals live in process memory (128 entries, one hour). The region bundle loads once per process, so restart after data changes.
- **The assistant must not recalculate.** `/api/brief` (`server/assistant.py`, owner B3) reads metrics through `server.evidence.trusted_context` and cites evidence; it never computes route values. Answers are deterministic templates unless `MODEL_API_KEY` is set, and a model answer is kept only if its numbers and citations match the stored plan.
- **Ownership.** A1 data and coordinates, A2 routing and mission arithmetic, A3 API and evidence, B1 map and mission state, B2 3D terrain, B3 assistant and report. See `CONTRIBUTING.md`.
- **Record verification.** State the actual command run and its result in the change description.
