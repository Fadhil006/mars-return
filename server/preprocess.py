"""Preprocess Mars rasters into a bounded local metric grid.

The service consumes a small, self-contained region directory:

    elevation.json  2-D array of metres (null = unknown)
    slope.json      2-D array of terrain slope in degrees (null = unknown)
    mask.json       2-D array of booleans (false = no-data / unusable)
    imagery.webp    RGB preview aligned to the same grid
    science-stops.json
    manifest.json

Two modes:

* ``prepare_region(source_paths=..., crop_bounds=...)`` reprojects a USGS DEM
  and orthoimage onto a local Mars tangent plane. Cell size is 10 m or 20 m and
  the grid is capped at 512 x 512 cells.
* ``prepare_region(synthetic_fallback=True)`` generates a deterministic
  ~3 km x 3 km western Jezero delta analog so the backend works offline with
  no external downloads.

Slope is always computed from metric elevation gradients; raw degree rasters
are never treated as slope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image

try:  # rasterio is only needed for the real-raster path
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.warp import reproject, transform, transform_bounds
except ImportError:  # pragma: no cover - documented in server/README.md
    rasterio = None  # type: ignore[assignment]

__all__ = [
    "MARS_RADIUS_M",
    "MODEL_VERSION",
    "SCHEMA_VERSION",
    "SYNTHETIC_DATASET_VERSION",
    "prepare_region",
    "prepare_synthetic_region",
    "build_synthetic_terrain",
    "synthetic_science_stops",
    "compute_slope_deg",
    "main",
]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MARS_RADIUS_M = 3_389_500.0
SCHEMA_VERSION = 1
MODEL_VERSION = "group-a-1.0.0"
SYNTHETIC_DATASET_VERSION = "jezero-synthetic-2026.11-v1"
SYNTHETIC_GENERATED_AT = "2026-11-13T00:00:00Z"
DEFAULT_ROWS = 150
DEFAULT_COLS = 150
DEFAULT_CELL_SIZE_M = 20.0
MAX_CELLS = 512

PARAMETER_BOUNDS: dict[str, dict[str, float]] = {
    "maxSlopeDeg": {"min": 5.0, "max": 30.0, "default": 15.0},
    "speedMPerMin": {"min": 1.0, "max": 120.0, "default": 30.0},
    "totalBudgetMin": {"min": 0.0, "max": 1440.0, "default": 180.0},
    "reserveMin": {"min": 0.0, "max": 1440.0, "default": 20.0},
    "dwellMin": {"min": 0.0, "max": 720.0, "default": 10.0},
}

SOURCE_RECORDS: list[dict[str, Any]] = [
    {
        "sourceId": "usgs-jezero-dem",
        "title": "Mars 2020 Perseverance landing site digital elevation model",
        "publisher": "USGS Astrogeology Science Center",
        "url": "https://astrogeology.usgs.gov/search/map/mars_2020_perseverance_landing_site_dem",
        "accessed": "2026-11-13",
        "license": "Public domain (US Government)",
        "role": "elevation",
        "notes": "DEM source for slope and ascent calculations.",
    },
    {
        "sourceId": "usgs-jezero-ortho",
        "title": "Jezero Crater orthoimage mosaic",
        "publisher": "USGS Astrogeology Science Center / NASA HiRISE",
        "url": "https://astrogeology.usgs.gov/search/map/mars_2020_perseverance_landing_site_orthoimage",
        "accessed": "2026-11-13",
        "license": "Public domain (US Government)",
        "role": "orthoimagery",
        "notes": "Orthoimage source for the regional imagery layer.",
    },
    {
        "sourceId": "nasa-perseverance-samples",
        "title": "Mars Rock Samples collected by Perseverance",
        "publisher": "NASA Science",
        "url": "https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/",
        "accessed": "2026-11-13",
        "license": "Public domain (NASA)",
        "role": "science-stop provenance",
        "notes": "Sample names, sols, sites, rock types and science notes.",
    },
    {
        "sourceId": "synthetic-jezero-analog",
        "title": "Offline synthetic Jezero western-delta analog",
        "publisher": "mars-return project",
        "url": "local://data/region",
        "accessed": "2026-11-13",
        "license": "Project-generated synthetic data",
        "role": "synthetic fallback terrain",
        "notes": (
            "Deterministic terrain generator used when USGS rasters are not "
            "available. It is a physically plausible analog, not a measured "
            "DEM; coordinates are local grid positions."
        ),
    },
]


def synthetic_science_stops(base_xy: Sequence[float] = (400.0, 400.0)) -> list[dict[str, Any]]:
    """Three real Perseverance sample sites placed on the synthetic grid.

    Sample metadata comes from NASA's Mars Rock Samples table (accessed
    2026-11-13). Local ``xy`` values are synthetic grid positions chosen to be
    reachable from the default base; they are not rover odometry.
    """

    return [
        {
            "targetId": "hazeltop",
            "sourceId": "nasa-perseverance-sample-hazeltop",
            "name": "Hazeltop",
            "xy": [1300.0, 400.0],
            "description": (
                "Sedimentary rock core from the Wildcat Ridge member of the "
                "Jezero delta front; drilled and sealed by Perseverance."
            ),
            "geology": (
                "Fine-grained delta-front sedimentary rock with sulfate and "
                "clay-bearing signals, sampled to study ancient lake chemistry."
            ),
            "sourceIds": [
                "nasa-perseverance-sample-hazeltop",
                "nasa-perseverance-samples",
                "usgs-jezero-dem",
            ],
            "provenance": {
                "mission": "NASA Mars 2020 Perseverance",
                "site": "Wildcat Ridge, Delta Front, Jezero Crater",
                "sol": 509,
                "date": "2022-07-27",
                "latitudeDeg": 18.444,
                "longitudeDeg": 77.451,
                "citation": (
                    "NASA Science, Mars Rock Samples, sample 12 (Hazeltop), "
                    "sol 509; accessed 2026-11-13."
                ),
                "url": "https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/",
                "note": (
                    "xy is a local synthetic-grid position; latitude/longitude "
                    "is approximate contextual provenance, not a surveyed fix."
                ),
            },
        },
        {
            "targetId": "montdenier",
            "sourceId": "nasa-perseverance-sample-montdenier",
            "name": "Montdenier",
            "xy": [1100.0, 1200.0],
            "description": (
                "Igneous rock core from the Rochette outcrop at Artuby Ridge, "
                "one of the first two cores cached by Perseverance."
            ),
            "geology": (
                "Olivine-bearing basaltic lava-flow rock, sampled to date "
                "Jezero floor volcanism and assess aqueous alteration."
            ),
            "sourceIds": [
                "nasa-perseverance-sample-montdenier",
                "nasa-perseverance-samples",
                "usgs-jezero-dem",
            ],
            "provenance": {
                "mission": "NASA Mars 2020 Perseverance",
                "site": "Artuby Ridge (Rochette), Jezero Crater floor",
                "sol": 194,
                "date": "2021-09-06",
                "latitudeDeg": 18.430,
                "longitudeDeg": 77.452,
                "citation": (
                    "NASA Science, Mars Rock Samples, sample 2 (Montdenier), "
                    "sol 194; accessed 2026-11-13."
                ),
                "url": "https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/",
                "note": (
                    "xy is a local synthetic-grid position; latitude/longitude "
                    "is approximate contextual provenance, not a surveyed fix."
                ),
            },
        },
        {
            "targetId": "mageik",
            "sourceId": "nasa-perseverance-sample-mageik",
            "name": "Mageik",
            "xy": [1800.0, 900.0],
            "description": (
                "Sedimentary rock core from the Amalik member of the delta "
                "front, sealed during the 2022 delta campaign."
            ),
            "geology": (
                "Delta-front mudstone/sandstone package used to reconstruct "
                "fluvial-lacustrine depositional conditions."
            ),
            "sourceIds": [
                "nasa-perseverance-sample-mageik",
                "nasa-perseverance-samples",
                "usgs-jezero-dem",
            ],
            "provenance": {
                "mission": "NASA Mars 2020 Perseverance",
                "site": "Amalik, Delta Front, Jezero Crater",
                "sol": 619,
                "date": "2022-11-16",
                "latitudeDeg": 18.451,
                "longitudeDeg": 77.438,
                "citation": (
                    "NASA Science, Mars Rock Samples, sample 15 (Mageik), "
                    "sol 619; accessed 2026-11-13."
                ),
                "url": "https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/",
                "note": (
                    "xy is a local synthetic-grid position; latitude/longitude "
                    "is approximate contextual provenance, not a surveyed fix."
                ),
            },
        },
    ]


def _smooth(array: np.ndarray, passes: int) -> np.ndarray:
    """Small separable box blur used to build correlated synthetic relief."""

    out = np.asarray(array, dtype=np.float64)
    for _ in range(max(0, int(passes))):
        padded = np.pad(out, 1, mode="edge")
        out = (
            padded[:-2, 1:-1]
            + padded[2:, 1:-1]
            + padded[1:-1, :-2]
            + padded[1:-1, 2:]
            + 4.0 * padded[1:-1, 1:-1]
        ) / 8.0
    return out


def build_synthetic_terrain(
    rows: int = DEFAULT_ROWS,
    cols: int = DEFAULT_COLS,
    cell_size_m: float = DEFAULT_CELL_SIZE_M,
) -> tuple[np.ndarray, np.ndarray]:
    """Create deterministic western-Jezero-delta analog elevation and mask.

    The result is intentionally varied but gentle enough to traverse at the
    default 15 deg slope ceiling across most of the region, with a steep eastern
    wall and two no-data holes for constraint testing. Elevations are metres
    relative to the Mars datum (roughly Jezero floor level, -2600 m).
    """

    if rows < 16 or cols < 16:
        raise ValueError("rows and cols must be at least 16")
    if cell_size_m not in (10.0, 20.0):
        raise ValueError("cell size must be 10 m or 20 m")

    width_m = cols * cell_size_m
    height_m = rows * cell_size_m
    xs = (np.arange(cols) + 0.5) * cell_size_m
    ys = height_m - (np.arange(rows) + 0.5) * cell_size_m
    x, y = np.meshgrid(xs, ys)

    # Broad western rise toward the delta apex plus a gentle basin to the east.
    elev = -2602.0 + 0.020 * (width_m - x)
    apex_x, apex_y = 0.10 * width_m, 0.50 * height_m
    radius = np.hypot(x - apex_x, y - apex_y)
    elev += 34.0 * np.exp(-((radius / (0.52 * width_m)) ** 2))
    elev -= 14.0 * np.exp(-(((x - 0.86 * width_m) / (0.22 * width_m)) ** 2))

    # Sinuous delta-front ridge and a shallow distributary channel.
    ridge_y = 0.50 * height_m + 210.0 * np.sin(x / (0.17 * width_m))
    elev += 13.0 * np.exp(-(((y - ridge_y) / (0.045 * height_m)) ** 2)) * np.exp(
        -(((x - 0.47 * width_m) / (0.32 * width_m)) ** 2)
    )
    channel_y = 0.34 * height_m + 150.0 * np.sin(x / (0.13 * width_m) + 0.7)
    elev -= 10.0 * np.exp(-(((y - channel_y) / (0.025 * height_m)) ** 2)) * np.exp(
        -(((x - 0.50 * width_m) / (0.34 * width_m)) ** 2)
    )
    channel2_y = 0.70 * height_m + 110.0 * np.sin(x / (0.11 * width_m) + 2.1)
    elev -= 7.0 * np.exp(-(((y - channel2_y) / (0.022 * height_m)) ** 2)) * np.exp(
        -(((x - 0.52 * width_m) / (0.28 * width_m)) ** 2)
    )

    # Correlated multi-scale roughness (deterministic seed).
    rng = np.random.default_rng(2026)
    noise = rng.normal(0.0, 1.0, (rows, cols))
    elev += 3.6 * _smooth(noise, 18)
    elev += 1.7 * _smooth(noise, 7)
    elev += 0.55 * _smooth(noise, 2)

    # Steep eastern crater-wall analog (well outside the traverse corridor).
    elev += 150.0 / (1.0 + np.exp(-(x - 0.915 * width_m) / (0.018 * width_m)))

    mask = np.ones((rows, cols), dtype=bool)

    # Two irregular no-data holes: an unnamed pit and a patch of shadowed slope.
    hole1 = np.hypot(x - 0.77 * width_m, y - 0.77 * height_m) < 0.032 * width_m
    hole2 = (
        np.hypot((x - 0.20 * width_m) / 1.35, (y - 0.80 * height_m) / 0.75)
        < 0.030 * width_m
    )
    mask &= ~(hole1 | hole2)

    # Conservative border ring: outer half-cell is unknown.
    mask[0, :] = False
    mask[-1, :] = False
    mask[:, 0] = False
    mask[:, -1] = False

    elevation = np.where(mask, elev, np.nan)
    return elevation, mask


def compute_slope_deg(elevation: np.ndarray, cell_size_m: float) -> np.ndarray:
    """Terrain slope in degrees from metric elevation gradients.

    ``np.gradient`` is evaluated with the cell size in metres, so the result is
    ``atan(|grad h|)`` in degrees. No-data cells and their immediate neighbours
    become ``NaN`` (conservative), never zero.
    """

    elev = np.asarray(elevation, dtype=np.float64)
    if elev.ndim != 2:
        raise ValueError("elevation must be 2-D")
    if cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive")
    if min(elev.shape) < 2:
        return np.full(elev.shape, np.nan)

    grad_row, grad_col = np.gradient(elev, cell_size_m)
    slope = np.degrees(np.arctan(np.hypot(grad_row, grad_col)))
    slope[~np.isfinite(elev)] = np.nan
    slope[~np.isfinite(grad_row) | ~np.isfinite(grad_col)] = np.nan
    return slope


def _render_hillshade(elevation: np.ndarray, mask: np.ndarray, cell_size_m: float) -> np.ndarray:
    """Render a Mars-toned hillshade RGB preview from metric elevation."""

    rows, cols = elevation.shape
    filled = np.where(mask & np.isfinite(elevation), elevation, np.nan)
    if np.isfinite(filled).any():
        lo = float(np.nanpercentile(filled, 3))
        hi = float(np.nanpercentile(filled, 97))
    else:  # pragma: no cover - synthetic data always has relief
        lo, hi = 0.0, 1.0
    span = max(hi - lo, 1e-6)
    t = np.clip((filled - lo) / span, 0.0, 1.0)
    t = np.nan_to_num(t, nan=0.0)

    low = np.array([92.0, 57.0, 39.0])
    high = np.array([214.0, 169.0, 126.0])
    rgb = low[None, None, :] + t[:, :, None] * (high - low)[None, None, :]

    # Light from the north-west; gradient sign follows row/col indexing.
    safe = np.where(np.isfinite(filled), filled, np.nanmedian(filled) if np.isfinite(filled).any() else 0.0)
    grad_row, grad_col = np.gradient(safe, cell_size_m)
    light = np.array([-0.62, -0.62, 0.48])
    light = light / np.linalg.norm(light)
    nx = -grad_col
    ny = -(-grad_row)
    nz = np.ones_like(nx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = (nx * light[0] + ny * light[1] + nz * light[2]) / norm
    brightness = np.clip(0.52 + 0.78 * shade, 0.28, 1.28)
    rgb *= brightness[:, :, None]

    rgb[~mask] = np.array([34.0, 31.0, 29.0])
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _json_grid(array: np.ndarray, digits: int = 2) -> list[list[float | None]]:
    """Serialise a 2-D float array, preserving unknown cells as ``null``."""

    out: list[list[float | None]] = []
    for row in np.asarray(array, dtype=np.float64):
        out.append([None if not np.isfinite(v) else round(float(v), digits) for v in row])
    return out


def _json_mask(mask: np.ndarray) -> list[list[bool]]:
    return [[bool(v) for v in row] for row in np.asarray(mask, dtype=bool)]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _layer_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _validate_cell_size(cell_size_m: float) -> float:
    cell = float(cell_size_m)
    if cell not in (10.0, 20.0):
        raise ValueError("cell_size_m must be 10 or 20 metres")
    return cell


def _build_manifest(
    *,
    rows: int,
    cols: int,
    cell_size_m: float,
    output_dir: Path,
    dataset_version: str,
    generated_at: str,
    science_stops: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    checksums: dict[str, str],
    resolution_note: str,
    projection: str,
) -> dict[str, Any]:
    width_m = cols * cell_size_m
    height_m = rows * cell_size_m
    return {
        "schemaVersion": SCHEMA_VERSION,
        "datasetVersion": dataset_version,
        "modelVersion": MODEL_VERSION,
        "generatedAt": generated_at,
        "region": {
            "name": "Jezero Crater western delta (local metric grid)",
            "boundsXY": {"minX": 0.0, "minY": 0.0, "maxX": width_m, "maxY": height_m},
            "widthM": width_m,
            "heightM": height_m,
        },
        "grid": {
            "rows": rows,
            "cols": cols,
            "cellSizeM": cell_size_m,
            "transform": {
                "a": cell_size_m,
                "b": 0.0,
                "c": 0.0,
                "d": 0.0,
                "e": -cell_size_m,
                "f": height_m,
            },
            "projection": projection,
            "pixelRegistration": "north-up; row 0 = north edge, col 0 = west edge; values at cell centres",
        },
        "mars": {
            "datum": "Mars 2000 / IAU_2015:49900",
            "meanRadiusM": MARS_RADIUS_M,
            "referenceEllipsoid": "IAU 2015 Mars sphere (R = 3,389,500 m)",
        },
        "layers": {
            "elevation": _layer_path(output_dir / "elevation.json"),
            "slope": _layer_path(output_dir / "slope.json"),
            "mask": _layer_path(output_dir / "mask.json"),
            "imagery": _layer_path(output_dir / "imagery.webp"),
            "scienceStops": _layer_path(output_dir / "science-stops.json"),
        },
        "parameterBounds": PARAMETER_BOUNDS,
        "scienceStops": science_stops,
        "sources": sources,
        "checksums": checksums,
        "notes": [resolution_note],
    }


def prepare_synthetic_region(
    output_dir: str | Path = "data/region",
    *,
    rows: int = DEFAULT_ROWS,
    cols: int = DEFAULT_COLS,
    cell_size_m: float = DEFAULT_CELL_SIZE_M,
) -> dict[str, Any]:
    """Generate the offline synthetic dataset and return the manifest."""

    cell = _validate_cell_size(cell_size_m)
    if max(rows, cols) > MAX_CELLS:
        raise ValueError(f"grid must not exceed {MAX_CELLS} x {MAX_CELLS} cells")
    out = Path(output_dir)
    elevation, mask = build_synthetic_terrain(rows=rows, cols=cols, cell_size_m=cell)
    slope = compute_slope_deg(elevation, cell)
    imagery = _render_hillshade(elevation, mask, cell)
    stops = synthetic_science_stops()

    out.mkdir(parents=True, exist_ok=True)
    stops_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "datasetVersion": SYNTHETIC_DATASET_VERSION,
        "stops": stops,
    }
    _write_json(out / "science-stops.json", stops_payload)
    _write_json(out / "elevation.json", _json_grid(elevation))
    _write_json(out / "slope.json", _json_grid(slope))
    _write_json(out / "mask.json", _json_mask(mask))
    Image.fromarray(imagery, mode="RGB").save(out / "imagery.webp", format="WEBP", quality=88, method=4)

    checksums = {
        name: _sha256_file(out / name)
        for name in ("elevation.json", "slope.json", "mask.json", "imagery.webp", "science-stops.json")
    }
    manifest = _build_manifest(
        rows=rows,
        cols=cols,
        cell_size_m=cell,
        output_dir=out,
        dataset_version=SYNTHETIC_DATASET_VERSION,
        generated_at=SYNTHETIC_GENERATED_AT,
        science_stops=stops,
        sources=SOURCE_RECORDS,
        checksums=checksums,
        resolution_note=(
            "Synthetic offline fallback: deterministic western-Jezero-delta analog, "
            "not a measured DEM. Cell size 20 m, grid capped at 512 cells."
        ),
        projection="LOCAL_METRIC_TANGENT_PLANE (synthetic analog; +x East, +y North)",
    )
    _write_json(out / "manifest.json", manifest)
    return manifest


def _source_science_stops(path: str | Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, Mapping) and isinstance(payload.get("stops"), list):
        return payload["stops"]
    raise ValueError("science stops file must be a list or an object with a 'stops' list")


def _prepare_from_rasters(
    *,
    dem_path: Path,
    ortho_path: Path | None,
    crop_bounds: Sequence[float] | None,
    output_dir: Path,
    cell_size_m: float,
    max_cells: int,
    science_stops: list[dict[str, Any]],
) -> dict[str, Any]:
    if rasterio is None:  # pragma: no cover - environment guard
        raise RuntimeError("rasterio is required for real-raster preprocessing")

    cell = _validate_cell_size(cell_size_m)
    if max_cells < 1 or max_cells > MAX_CELLS:
        raise ValueError(f"max_cells must be between 1 and {MAX_CELLS}")

    with rasterio.open(dem_path) as dem:
        if dem.crs is None:
            raise ValueError("DEM must have a CRS")
        bounds = crop_bounds if crop_bounds is not None else dem.bounds
        if len(bounds) != 4:
            raise ValueError("crop_bounds must be (minx, miny, maxx, maxy)")
        left, bottom, right, top = (float(v) for v in bounds)
        if not (right > left and top > bottom):
            raise ValueError("crop_bounds must have maxx>minx and maxy>miny")
        dem_bounds = dem.bounds
        left = max(left, dem_bounds.left)
        bottom = max(bottom, dem_bounds.bottom)
        right = min(right, dem_bounds.right)
        top = min(top, dem_bounds.top)
        if not (right > left and top > bottom):
            raise ValueError("crop_bounds do not overlap the DEM")

        cx = (left + right) / 2.0
        cy = (bottom + top) / 2.0
        lon_arr, lat_arr = transform(dem.crs, "EPSG:4326", [cx], [cy])
        lon, lat = float(lon_arr[0]), float(lat_arr[0])
        dst_crs = (
            f"+proj=aeqd +lat_0={lat:.8f} +lon_0={lon:.8f} +x_0=0 +y_0=0 "
            f"+R={MARS_RADIUS_M:.1f} +units=m +no_defs +type=crs"
        )
        dst_bounds = transform_bounds(dem.crs, dst_crs, left, bottom, right, top, densify_pts=21)
        minx, miny, maxx, maxy = dst_bounds
        span_x = max(maxx - minx, cell)
        span_y = max(maxy - miny, cell)
        resolution = cell
        width = max(1, int(math.ceil(span_x / resolution)))
        height = max(1, int(math.ceil(span_y / resolution)))
        if width > max_cells or height > max_cells:
            raise ValueError(
                f"crop is {width}x{height} cells at {resolution:g} m; reduce the crop "
                f"or use 20 m cells (limit {max_cells}x{max_cells})"
            )
        # Reprojection transform before shifting the local origin to (0, 0).
        src_transform = from_origin(minx, maxy, resolution, resolution)

        elevation = np.full((height, width), np.nan, dtype=np.float64)
        reproject(
            source=rasterio.band(dem, 1),
            destination=elevation,
            src_transform=dem.transform,
            src_crs=dem.crs,
            src_nodata=dem.nodata,
            dst_transform=src_transform,
            dst_crs=dst_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )

    mask = np.isfinite(elevation)
    # Reject implausible sentinel elevations if a DEM uses a large negative nodata.
    mask &= elevation > -20000.0
    elevation = np.where(mask, elevation, np.nan)
    slope = compute_slope_deg(elevation, resolution)

    imagery: np.ndarray | None = None
    if ortho_path is not None:
        with rasterio.open(ortho_path) as ortho:
            if ortho.crs is None:
                raise ValueError("orthoimage must have a CRS")
            bands = min(3, ortho.count)
            rgb = np.zeros((3, height, width), dtype=np.float32)
            for band in range(bands):
                reproject(
                    source=rasterio.band(ortho, band + 1),
                    destination=rgb[band],
                    src_transform=ortho.transform,
                    src_crs=ortho.crs,
                    src_nodata=ortho.nodata,
                    dst_transform=src_transform,
                    dst_crs=dst_crs,
                    dst_nodata=np.nan,
                    resampling=Resampling.bilinear,
                )
            if bands == 1:
                rgb[1] = rgb[0]
                rgb[2] = rgb[0]
            valid = np.isfinite(rgb).all(axis=0) & mask
            lo = float(np.nanpercentile(rgb[:, valid], 2)) if valid.any() else 0.0
            hi = float(np.nanpercentile(rgb[:, valid], 98)) if valid.any() else 1.0
            span = max(hi - lo, 1e-6)
            scaled = np.clip((rgb - lo) / span, 0.0, 1.0) * 255.0
            imagery = np.nan_to_num(scaled, nan=0.0).astype(np.uint8).transpose(1, 2, 0)
            imagery[~valid] = np.array([34, 31, 29], dtype=np.uint8)
            mask &= valid
    if imagery is None:
        imagery = _render_hillshade(elevation, mask, resolution)

    if not mask.any():
        raise ValueError("no valid elevation cells after reprojection")

    out = output_dir
    out.mkdir(parents=True, exist_ok=True)

    dataset_digest = hashlib.sha256(
        np.round(np.nan_to_num(elevation, nan=-9999.0), 2).tobytes() + mask.tobytes()
    ).hexdigest()[:12]
    dataset_version = f"jezero-preprocessed-{dataset_digest}"
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    stops_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "datasetVersion": dataset_version,
        "stops": science_stops,
    }
    _write_json(out / "science-stops.json", stops_payload)
    _write_json(out / "elevation.json", _json_grid(elevation))
    _write_json(out / "slope.json", _json_grid(slope))
    _write_json(out / "mask.json", _json_mask(mask))
    Image.fromarray(imagery, mode="RGB").save(out / "imagery.webp", format="WEBP", quality=88, method=4)

    checksums = {
        name: _sha256_file(out / name)
        for name in ("elevation.json", "slope.json", "mask.json", "imagery.webp", "science-stops.json")
    }
    manifest = _build_manifest(
        rows=height,
        cols=width,
        cell_size_m=resolution,
        output_dir=out,
        dataset_version=dataset_version,
        generated_at=generated_at,
        science_stops=science_stops,
        sources=SOURCE_RECORDS,
        checksums=checksums,
        resolution_note=(
            f"Reprojected {dem_path.name} onto a Mars aeqd tangent plane centred at "
            f"lat {lat:.5f}, lon {lon:.5f}; resolution {resolution:.3f} m; "
            f"grid {height}x{width} (max {MAX_CELLS})."
        ),
        projection=f"MARS_LOCAL_AEQD (R={MARS_RADIUS_M:.0f} m; +x East, +y North)",
    )
    _write_json(out / "manifest.json", manifest)
    return manifest


def prepare_region(
    source_paths: Mapping[str, str | Path] | None = None,
    crop_bounds: Sequence[float] | None = None,
    output_dir: str | Path = "data/region",
    *,
    synthetic_fallback: bool = False,
    cell_size_m: float = DEFAULT_CELL_SIZE_M,
    max_cells: int = MAX_CELLS,
    science_stops_path: str | Path | None = None,
) -> dict[str, Any]:
    """Prepare a region directory and return its manifest.

    ``source_paths`` must contain ``dem`` and may contain ``ortho``. When
    ``synthetic_fallback`` is true (or no DEM is supplied) a deterministic
    offline dataset is generated instead.
    """

    if synthetic_fallback or source_paths is None or not source_paths.get("dem"):
        return prepare_synthetic_region(output_dir, cell_size_m=cell_size_m)

    dem = Path(source_paths["dem"])
    ortho = Path(source_paths["ortho"]) if source_paths.get("ortho") else None
    if not dem.exists():
        raise FileNotFoundError(f"DEM not found: {dem}")
    if ortho is not None and not ortho.exists():
        raise FileNotFoundError(f"orthoimage not found: {ortho}")

    return _prepare_from_rasters(
        dem_path=dem,
        ortho_path=ortho,
        crop_bounds=crop_bounds,
        output_dir=Path(output_dir),
        cell_size_m=cell_size_m,
        max_cells=max_cells,
        science_stops=_source_science_stops(science_stops_path),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare the Mars Return regional dataset.")
    parser.add_argument(
        "--synthetic-fallback",
        action="store_true",
        help="Generate the deterministic offline Jezero-delta analog (no downloads).",
    )
    parser.add_argument("--dem", type=Path, help="USGS Jezero DEM GeoTIFF.")
    parser.add_argument("--ortho", type=Path, help="Optional orthoimage GeoTIFF.")
    parser.add_argument(
        "--crop-bounds",
        nargs=4,
        type=float,
        metavar=("MINX", "MINY", "MAXX", "MAXY"),
        help="Crop bounds in the source raster CRS.",
    )
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "region")
    parser.add_argument("--cell-size", type=float, default=DEFAULT_CELL_SIZE_M)
    parser.add_argument("--max-cells", type=int, default=MAX_CELLS)
    parser.add_argument("--science-stops", type=Path, help="Optional science-stops JSON.")
    args = parser.parse_args(argv)

    if not args.synthetic_fallback and args.dem is None:
        parser.error("provide --dem/--ortho or --synthetic-fallback")

    manifest = prepare_region(
        source_paths={"dem": args.dem, "ortho": args.ortho} if args.dem else None,
        crop_bounds=args.crop_bounds,
        output_dir=args.output_dir,
        synthetic_fallback=args.synthetic_fallback,
        cell_size_m=args.cell_size,
        max_cells=args.max_cells,
        science_stops_path=args.science_stops,
    )
    grid = manifest["grid"]
    print(
        f"wrote {args.output_dir} | datasetVersion={manifest['datasetVersion']} "
        f"| {grid['rows']}x{grid['cols']} @ {grid['cellSizeM']} m "
        f"| stops={len(manifest['scienceStops'])}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
