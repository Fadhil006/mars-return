# Group A service

A1 owns `preprocess.py` and `coordinates.py`; A2 owns `routing.py` and
`mission.py`; A3 owns `api.py` and `evidence.py`. B3 will own `assistant.py`,
which is not implemented yet. Follow
[../docs/plans/01-group-a-data-and-routing.md](../docs/plans/01-group-a-data-and-routing.md).

Python modules and the dependency manifest now exist. Server setup, run, and
test instructions follow.

## Server setup, run, and test

All commands below are run from the repository root (for example,
`cd /path/to/mars-return`).

## 1. Environment (one time)

Requires Python 3.14+ (tested with CPython 3.14.8). The virtual environment is
local and git-ignored.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Exact pins live in `requirements.txt`:

| Package | Version |
| --- | --- |
| fastapi | 0.162.5 |
| uvicorn | 0.54.0 |
| numpy | 2.5.4 |
| rasterio | 1.5.2 |
| pillow | 13.0.0 |
| pydantic | 2.14.3 |
| pytest | 9.2.0 |
| httpx | 0.28.1 |

`httpx` is required by FastAPI's test client and is pinned explicitly.

## 2. Generate the local dataset

Offline synthetic fallback (~3 km x 3 km of Jezero Crater western-delta analog
terrain, 20 m cells, 150 x 150):

```bash
.venv/bin/python server/preprocess.py --synthetic-fallback
```

This writes, deterministically:

```text
data/region/
  elevation.json      # rows x cols, metres relative to Mars datum, null = no-data
  slope.json          # terrain slope in degrees computed from metric gradients
  mask.json           # true = usable cell, false = no-data / unknown
  imagery.webp        # hillshaded RGB preview aligned to the same grid
  science-stops.json  # 3 real Perseverance sample sites with provenance
  manifest.json       # bounds, transform, projection, Mars datum, sources,
                      # datasetVersion, parameter bounds, checksums
```

Real USGS rasters can be substituted (see `--help`):

```bash
.venv/bin/python server/preprocess.py \
  --dem /path/to/jezero_dem.tif \
  --ortho /path/to/jezero_ortho.tif \
  --crop-bounds MINX MINY MAXX MAXY \
  --cell-size 20 \
  --max-cells 512
```

The crop bounds are expressed in the source raster CRS. The preprocessing step
reprojects onto a local Mars-tangent metric plane, caps the grid at 512 x 512
cells, and keeps no-data as `null` / `false` rather than zero.

## 3. Run the API

```bash
.venv/bin/uvicorn server.api:app --host 127.0.0.1 --port 8000
```

Optional environment variables:

```bash
MARS_RETURN_DATA_DIR=/absolute/path/to/data/region   # default: data/region
MARS_RETURN_PLAN_TTL_SECONDS=1800                    # in-memory plan TTL
MARS_RETURN_PLAN_STORE_MAX=256                       # bounded store size
```

Endpoints:

```bash
curl -s http://127.0.0.1:8000/api/region | python -m json.tool
curl -s -X POST http://127.0.0.1:8000/api/plan \
  -H 'content-type: application/json' \
  -d @shared/fixtures/plan_success.request.json | python -m json.tool
```

(If you prefer one-file fixtures, the committed fixtures wrap `request` and
`response`; extract the `request` member when posting, or use the examples in
`docs/validation.md`.)

## 4. Test

```bash
.venv/bin/pytest server/tests -q
```

Useful subsets:

```bash
.venv/bin/pytest server/tests/test_coordinates.py -q
.venv/bin/pytest server/tests/test_routing.py -q
.venv/bin/pytest server/tests/test_mission.py -q
.venv/bin/pytest server/tests/test_api.py -q
```

## 5. Contract notes

- Coordinates are **local metric** `[x_m, y_m]`; East is +x, North is +y.
- Pixel convention: `row = 0` is the North edge, `col = 0` is the West edge.
- API statuses: `ok`, `over_budget`, `no_path`, `invalid_input`,
  `data_unavailable`.
- When no path exists, path and metric fields are `null` (never `0`) and
  `profile` is `[]`.
- `/api/brief` never trusts metrics from the prompt; it reads the stored plan
  by `planId` and cites `science-stops.json` source records.
