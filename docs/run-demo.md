# Runbook — B2 with A3

Local startup is documented below. Hosted deployment, the data package hand-off and the backup recording are not done; those sections say so.

## Supported environment and pinned dependencies

- Python 3.12+ with the pinned backend environment in `server/requirements.lock`.
- Node with npm for the browser application; versions are pinned in `web/package.json` and `web/package-lock.json`.
- A browser with WebGL for the 3D terrain. Without WebGL the 2D map keeps the same route and controls.

## Data package acquisition and checksum checks

The prepared region bundle in `data/region/` is required. Only `manifest.json`, `science-stops.json` and `rover-traverse.json` are tracked; the rest is generated:

```sh
.venv/bin/python -m scripts.prepare_demo       # first run downloads ~450 MB of USGS CTX data and verifies checksums
```

A missing or corrupt bundle makes the API answer 503 and the application shows "The planning data for this region could not be loaded." It never falls back to synthetic terrain.

- [ ] Packaged bundle hand-off (`scripts.package_region`) to a second machine: not verified.

## Local startup commands

From the repository root:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r server/requirements.lock
.venv/bin/python -m uvicorn server.api:app --host 127.0.0.1 --port 8000
```

Run one worker only: saved plans live in process memory (128 entries, one hour). Restart after changing the region data.

Development, in a second terminal:

```sh
cd web && npm install
npm run dev        # http://localhost:5173, /api proxied to http://127.0.0.1:8000
```

Single origin, no Vite:

```sh
cd web && npm install && npm run build
# restart the API; it serves web/dist at http://127.0.0.1:8000
```

Checks:

```sh
.venv/bin/python -m pytest server/tests
.venv/bin/python -m server.export_schema --check
cd web && npm test
```

## Hosted deployment and verification

- [ ] Not done. No public URL exists and nothing has been tested on a second device.

## Provider configuration and fallback mode

The assistant works with no provider. Without a key, `POST /api/brief` returns the deterministic explanation, labelled "Standard explanation" in the interface.

To enable model-written explanations, export these in the API's environment before starting it (the service does not read `.env` files):

```sh
export MODEL_API_KEY=...   # server-side only; never a VITE_ variable
export MODEL_NAME=...      # optional
```

A model answer is used only if every cited source and metric exists and every number in it matches the saved plan; otherwise the standard explanation is returned and labelled as such. If the model fails during a demonstration, say so and continue with the standard explanation.

## Backup presentation and reproduction check

- [ ] Not done. No recording exists, and no teammate has yet reproduced the local startup from this page.
