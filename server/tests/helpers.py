"""Shared test helpers: tiny synthetic grids and region objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np

from server.mission import MODEL_VERSION, Region
from server.routing import Grid

TEST_DATASET_VERSION = "test-dataset-v1"


def make_manifest(
    rows: int,
    cols: int,
    cell_size_m: float = 10.0,
    *,
    dataset_version: str = TEST_DATASET_VERSION,
    science_stops: Sequence[dict[str, Any]] | None = None,
    sources: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    height = rows * cell_size_m
    width = cols * cell_size_m
    return {
        "schemaVersion": 1,
        "datasetVersion": dataset_version,
        "modelVersion": MODEL_VERSION,
        "region": {
            "name": "test region",
            "boundsXY": {"minX": 0.0, "minY": 0.0, "maxX": width, "maxY": height},
            "widthM": width,
            "heightM": height,
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
                "f": height,
            },
            "projection": "test",
        },
        "parameterBounds": {},
        "scienceStops": list(science_stops or []),
        "sources": list(sources or []),
        "checksums": {},
    }


def make_grid(
    rows: int = 10,
    cols: int = 10,
    cell_size_m: float = 10.0,
    *,
    elevation: np.ndarray | None = None,
    slope: np.ndarray | None = None,
    mask: np.ndarray | None = None,
) -> Grid:
    elev = np.zeros((rows, cols), dtype=np.float64) if elevation is None else np.asarray(elevation, dtype=np.float64)
    slp = np.zeros((rows, cols), dtype=np.float64) if slope is None else np.asarray(slope, dtype=np.float64)
    msk = np.ones((rows, cols), dtype=bool) if mask is None else np.asarray(mask, dtype=bool)
    return Grid(
        manifest=make_manifest(rows, cols, cell_size_m),
        elevation=elev,
        slope=slp,
        mask=msk,
    )


def make_stop(
    target_id: str = "target",
    xy: Sequence[float] = (95.0, 5.0),
    *,
    source_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    ids = list(source_ids or [f"test-source-{target_id}"])
    return {
        "targetId": target_id,
        "sourceId": ids[0],
        "name": target_id.title(),
        "xy": [float(xy[0]), float(xy[1])],
        "description": f"Test science target {target_id}.",
        "geology": "Synthetic test geology.",
        "sourceIds": ids,
        "provenance": {
            "mission": "test mission",
            "site": "test site",
            "sol": 1,
            "date": "2026-01-01",
            "latitudeDeg": 0.0,
            "longitudeDeg": 0.0,
            "citation": "Test citation.",
            "url": "local://test",
            "note": "synthetic test fixture",
        },
    }


def make_region(
    rows: int = 10,
    cols: int = 10,
    cell_size_m: float = 10.0,
    *,
    elevation: np.ndarray | None = None,
    slope: np.ndarray | None = None,
    mask: np.ndarray | None = None,
    stops: Sequence[dict[str, Any]] | None = None,
    base_xy: Sequence[float] | None = None,
) -> Region:
    stop_list = list(stops or [make_stop()])
    manifest = make_manifest(
        rows,
        cols,
        cell_size_m,
        science_stops=stop_list,
        sources=[
            {
                "sourceId": "usgs-jezero-dem",
                "title": "Test DEM",
                "publisher": "test",
                "url": "local://test-dem",
                "role": "elevation",
            }
        ],
    )
    grid = Grid(
        manifest=manifest,
        elevation=np.zeros((rows, cols)) if elevation is None else np.asarray(elevation, dtype=np.float64),
        slope=np.zeros((rows, cols)) if slope is None else np.asarray(slope, dtype=np.float64),
        mask=np.ones((rows, cols), dtype=bool) if mask is None else np.asarray(mask, dtype=bool),
    )
    sources = {record["sourceId"]: record for record in manifest["sources"]}
    for stop in stop_list:
        for source_id in stop.get("sourceIds", []):
            sources.setdefault(
                source_id,
                {
                    "sourceId": source_id,
                    "title": f"Source {source_id}",
                    "publisher": "test",
                    "url": f"local://{source_id}",
                    "role": "science stop citation",
                },
            )
    return Region(
        data_dir=Path("/tmp/opencode/test-region"),
        manifest=manifest,
        grid=grid,
        science_stops=stop_list,
        sources=sources,
    )


def request_for(
    region: Region,
    *,
    request_id: str = "req-test-001",
    base_xy: Sequence[float] = (5.0, 5.0),
    target_id: str | None = None,
    max_slope_deg: float = 15.0,
    speed: float = 30.0,
    budget: float = 180.0,
    reserve: float = 20.0,
    dwell: float = 10.0,
    blocked: Sequence[Any] | None = None,
) -> dict[str, Any]:
    stop = region.science_stops[0]
    return {
        "requestId": request_id,
        "schemaVersion": 1,
        "datasetVersion": region.dataset_version,
        "baseXY": [float(base_xy[0]), float(base_xy[1])],
        "targetId": target_id or str(stop["targetId"]),
        "maxSlopeDeg": max_slope_deg,
        "speedMPerMin": speed,
        "totalBudgetMin": budget,
        "reserveMin": reserve,
        "dwellMin": dwell,
        "blockedPolygonsXY": list(blocked or []),
    }


def rehearsal_request_for(
    region: Region,
    *,
    request_id: str = "req-reh-test-001",
    current_xy: Sequence[float] = (55.0, 5.0),
    base_xy: Sequence[float] = (5.0, 5.0),
    target_id: str | None = None,
    elapsed: float = 20.0,
    remaining: float = 60.0,
    max_slope_deg: float = 15.0,
    speed: float = 30.0,
    dwell: float = 10.0,
    reserve: float = 20.0,
    blocked: Sequence[Any] | None = None,
) -> dict[str, Any]:
    stop = region.science_stops[0]
    return {
        "requestId": request_id,
        "schemaVersion": 1,
        "datasetVersion": region.dataset_version,
        "currentXY": [float(current_xy[0]), float(current_xy[1])],
        "elapsedMin": elapsed,
        "remainingBudgetMin": remaining,
        "targetId": target_id or str(stop["targetId"]),
        "baseXY": [float(base_xy[0]), float(base_xy[1])],
        "maxSlopeDeg": max_slope_deg,
        "speedMPerMin": speed,
        "dwellMin": dwell,
        "reserveMin": reserve,
        "routeMode": "shortest",
        "blockedPolygonsXY": list(blocked or []),
    }
