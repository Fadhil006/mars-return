# Group A service

Python 3.12+ (required by pinned NumPy/Rasterio); dependency lock verified on Python 3.14/Linux. From the repository root:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r server/requirements.lock
.venv/bin/python -m pytest server/tests
.venv/bin/python -m server.export_schema --check
```

`pyproject.toml` lists direct dependencies; `requirements.lock` pins the tested environment including test tools. Run modules from the repository root, not from `server/`.

A1 owns preprocessing and coordinates; A2 routing and mission arithmetic; A3 API, validation and evidence lookup. B3 owns the assistant/model adapter. Synthetic tests are never evidence of actual Mars terrain accuracy.

## Prepare and run

```sh
.venv/bin/python -m scripts.prepare_demo
.venv/bin/python -m uvicorn server.api:app --host 127.0.0.1 --port 8000
```

The first preparation downloads about 450 MB of real USGS CTX inputs and checks their recorded SHA-256 values. Subsequent preparations reuse verified raw files. Bulk files stay ignored by Git; `manifest.json` and the explicitly hypothetical observation points are tracked. `/api/region` publishes the dataset version required by requests and the default scenario. Swagger UI is at `/docs`.

Use the repository root as the working directory. `REGION_DATA_DIR` defaults to `data/region`; relative paths resolve against the repository root. The bundle loads once per process: restart after data changes. Missing/corrupt terrain returns 503, never synthetic fallback data.

Run **one worker**: saved plan/rehearsal evaluations are bounded to 128 entries for one hour in process memory. Restart/expiry/eviction requires recalculation. Bind locally by default; public deployments should apply request/rate limits at their reverse proxy. Bodies are limited to 256 KiB in the app.

`POST /api/reach` returns the return-time map from base; `POST /api/stress` closes each stretch of the way home in turn. See `shared/api-contract.md`.

## Reproduce evidence and package

```sh
.venv/bin/python -m scripts.validate_demo
mkdir -p data/packages
.venv/bin/python -m scripts.package_region --region-dir data/region --output data/packages/region.tar.gz
```

Validation checks three real-terrain scenarios, all five sampling sites with the stress test, the return envelope, rover elevations against the CTX grid, geometry-derived distances, event reset, and a prepared elevation against the original source raster. It writes `docs/validation-results.json`; it requires the raw DEM. Packaging validates the bundle, rejects symlinks, and prints the archive SHA-256. It refuses to replace an existing archive. A recipient can extract the fixed assets into `data/region/` and run the service without raw rasters or runtime network access.

The assistant endpoint `/api/brief` is **not implemented** here; B3 can use `server.evidence.trusted_context` to retrieve server-calculated metrics by plan ID. No credentials are used or exposed by Group A.
