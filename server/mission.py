"""Mission arithmetic: round-trip plans, rehearsals, budgets and profiles.

All distances are metres, slopes are degrees, times are minutes. When a leg
has no path, every path/metric field is ``None`` (never zero) and the profile is
an empty list.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from server.routing import Grid, RouteResult, rasterize_blocked, route

__all__ = [
    "SCHEMA_VERSION",
    "MODEL_VERSION",
    "DEFAULT_SPEED_MPER_MIN",
    "DEFAULT_TOTAL_BUDGET_MIN",
    "DEFAULT_DWELL_MIN",
    "DEFAULT_RESERVE_MIN",
    "DEFAULT_MAX_SLOPE_DEG",
    "DataUnavailableError",
    "Region",
    "load_region",
    "evaluate_plan",
    "evaluate_rehearsal",
    "compute_plan_id",
    "compute_rehearsal_id",
]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
MODEL_VERSION = "group-a-1.0.0"
DEFAULT_SPEED_MPER_MIN = 30.0
DEFAULT_TOTAL_BUDGET_MIN = 180.0
DEFAULT_DWELL_MIN = 10.0
DEFAULT_RESERVE_MIN = 20.0
DEFAULT_MAX_SLOPE_DEG = 15.0
MAX_PROFILE_SAMPLES = 64


class DataUnavailableError(RuntimeError):
    """Raised when the regional dataset is missing or internally inconsistent."""


@dataclass
class Region:
    data_dir: Path
    manifest: dict[str, Any]
    grid: Grid
    science_stops: list[dict[str, Any]]
    sources: dict[str, dict[str, Any]]
    warnings: list[dict[str, str]] = field(default_factory=list)

    @property
    def dataset_version(self) -> str:
        return str(self.manifest.get("datasetVersion", ""))

    @property
    def model_version(self) -> str:
        return str(self.manifest.get("modelVersion", MODEL_VERSION))

    def stop(self, target_id: str) -> dict[str, Any] | None:
        for stop in self.science_stops:
            if stop.get("targetId") == target_id:
                return stop
        return None

    def target_source_ids(self, target_id: str) -> list[str]:
        stop = self.stop(target_id)
        if not stop:
            return []
        ids = [str(v) for v in stop.get("sourceIds", []) if isinstance(v, str)]
        if stop.get("sourceId") and stop["sourceId"] not in ids:
            ids.insert(0, str(stop["sourceId"]))
        if "usgs-jezero-dem" not in ids and "usgs-jezero-dem" in self.sources:
            ids.append("usgs-jezero-dem")
        return _unique(ids)


def _unique(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _warn(code: str, message: str, severity: str = "warning") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _r(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return round(out, digits)


def _num(value: Any) -> float | None:
    """Return a finite float or None (bools and strings are not numbers)."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    out = float(value)
    return out if math.isfinite(out) else None


def _xy(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    x, y = _num(value[0]), _num(value[1])
    if x is None or y is None:
        return None
    return x, y


def _sha256_json(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_plan_id(request: Mapping[str, Any], region: Region) -> str:
    digest = _sha256_json(
        {
            "request": request,
            "datasetVersion": region.dataset_version,
            "modelVersion": region.model_version,
        }
    )
    return "plan-" + digest[:20]


def compute_rehearsal_id(request: Mapping[str, Any], region: Region) -> str:
    digest = _sha256_json(
        {
            "request": request,
            "datasetVersion": region.dataset_version,
            "modelVersion": region.model_version,
        }
    )
    return "reh-" + digest[:20]


# ---------------------------------------------------------------------------
# Region loading
# ---------------------------------------------------------------------------

def _load_float_grid(path: Path) -> np.ndarray:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DataUnavailableError(f"missing layer {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise DataUnavailableError(f"invalid JSON in {path.name}: {exc}") from exc
    if not isinstance(raw, list) or not raw:
        raise DataUnavailableError(f"{path.name} must be a non-empty 2-D array")
    width = len(raw[0]) if isinstance(raw[0], list) else 0
    if width == 0:
        raise DataUnavailableError(f"{path.name} must be a non-empty 2-D array")
    out = np.full((len(raw), width), np.nan, dtype=np.float64)
    for r, row in enumerate(raw):
        if not isinstance(row, list) or len(row) != width:
            raise DataUnavailableError(f"{path.name} is ragged at row {r}")
        for c, value in enumerate(row):
            if value is None:
                continue
            num = _num(value)
            if num is None:
                raise DataUnavailableError(f"{path.name}[{r}][{c}] is not numeric/null")
            out[r, c] = num
    return out


def _load_bool_grid(path: Path) -> np.ndarray:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DataUnavailableError(f"missing layer {path.name}") from exc
    if not isinstance(raw, list) or not raw:
        raise DataUnavailableError(f"{path.name} must be a non-empty 2-D array")
    width = len(raw[0]) if isinstance(raw[0], list) else 0
    out = np.zeros((len(raw), width), dtype=bool)
    for r, row in enumerate(raw):
        if not isinstance(row, list) or len(row) != width:
            raise DataUnavailableError(f"{path.name} is ragged at row {r}")
        for c, value in enumerate(row):
            if not isinstance(value, bool):
                raise DataUnavailableError(f"{path.name}[{r}][{c}] is not boolean")
            out[r, c] = value
    return out


def _verify_checksums(data_dir: Path, manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    checksums = manifest.get("checksums")
    if not isinstance(checksums, Mapping):
        return warnings
    for name, expected in checksums.items():
        path = data_dir / str(name)
        if not path.exists():
            warnings.append(_warn("checksum_missing", f"Layer {name} listed in manifest is missing.", "error"))
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        actual = "sha256:" + digest
        if actual != expected:
            warnings.append(
                _warn(
                    "checksum_mismatch",
                    f"Layer {name} does not match its manifest checksum; dataset may have changed.",
                    "warning",
                )
            )
    return warnings


def load_region(
    data_dir: str | Path | None = None,
    *,
    verify_checksums: bool = True,
) -> Region:
    """Load a prepared region directory into a :class:`Region`."""

    directory = Path(data_dir) if data_dir is not None else PROJECT_ROOT / "data" / "region"
    manifest_path = directory / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DataUnavailableError(f"manifest not found in {directory}") from exc
    except json.JSONDecodeError as exc:
        raise DataUnavailableError(f"invalid manifest JSON: {exc}") from exc
    if not isinstance(manifest, Mapping):
        raise DataUnavailableError("manifest must be a JSON object")

    elevation = _load_float_grid(directory / "elevation.json")
    slope = _load_float_grid(directory / "slope.json")
    mask = _load_bool_grid(directory / "mask.json")
    if elevation.shape != slope.shape or elevation.shape != mask.shape:
        raise DataUnavailableError(
            f"layer shapes differ: elevation={elevation.shape}, slope={slope.shape}, mask={mask.shape}"
        )

    grid = Grid(manifest=manifest, elevation=elevation, slope=slope, mask=mask)

    stops_path = directory / "science-stops.json"
    try:
        stop_payload = json.loads(stops_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        stop_payload = {"stops": manifest.get("scienceStops", [])}
    except json.JSONDecodeError as exc:
        raise DataUnavailableError(f"invalid science-stops JSON: {exc}") from exc
    if isinstance(stop_payload, list):
        stops = stop_payload
    elif isinstance(stop_payload, Mapping) and isinstance(stop_payload.get("stops"), list):
        stops = stop_payload["stops"]
    elif isinstance(manifest.get("scienceStops"), list):
        stops = manifest["scienceStops"]
    else:
        stops = []
    stops = [s for s in stops if isinstance(s, Mapping) and s.get("targetId")]

    sources: dict[str, dict[str, Any]] = {}
    for record in manifest.get("sources", []):
        if isinstance(record, Mapping) and isinstance(record.get("sourceId"), str):
            sources[record["sourceId"]] = dict(record)
    for stop in stops:
        for source_id in stop.get("sourceIds", []):
            if isinstance(source_id, str) and source_id not in sources:
                sources[source_id] = {
                    "sourceId": source_id,
                    "title": source_id,
                    "publisher": "",
                    "url": "",
                    "role": "science stop citation",
                }

    warnings = _verify_checksums(directory, manifest) if verify_checksums else []
    return Region(
        data_dir=directory,
        manifest=dict(manifest),
        grid=grid,
        science_stops=[dict(s) for s in stops],
        sources=sources,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_common(region: Region, request: Mapping[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if request.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(
            _warn(
                "unsupported_schema_version",
                f"schemaVersion must be {SCHEMA_VERSION}.",
                "error",
            )
        )
    dataset = request.get("datasetVersion")
    if not isinstance(dataset, str) or dataset != region.dataset_version:
        errors.append(
            _warn(
                "unsupported_dataset_version",
                f"datasetVersion must match the loaded dataset ({region.dataset_version}).",
                "error",
            )
        )
    slope = _num(request.get("maxSlopeDeg"))
    if slope is None or not (5.0 <= slope <= 30.0):
        errors.append(_warn("invalid_max_slope", "maxSlopeDeg must be within 5..30 degrees.", "error"))
    speed = _num(request.get("speedMPerMin"))
    if speed is None or speed <= 0:
        errors.append(_warn("invalid_speed", "speedMPerMin must be > 0.", "error"))
    if _xy(request.get("baseXY")) is None:
        errors.append(_warn("invalid_base", "baseXY must be finite [x_m, y_m].", "error"))
    target_id = request.get("targetId")
    if not isinstance(target_id, str) or not target_id:
        errors.append(_warn("invalid_target", "targetId must be a non-empty string.", "error"))
    elif region.stop(target_id) is None:
        errors.append(_warn("unknown_target", f"Unknown targetId {target_id!r}.", "error"))
    polygons = request.get("blockedPolygonsXY")
    if polygons is None:
        polygons = []
    if not isinstance(polygons, list):
        errors.append(_warn("invalid_blocked_polygons", "blockedPolygonsXY must be an array.", "error"))
    else:
        for index, ring in enumerate(polygons):
            if not isinstance(ring, (list, tuple)) or len(ring) < 3:
                errors.append(
                    _warn(
                        "invalid_blocked_polygons",
                        f"blockedPolygonsXY[{index}] must have at least 3 vertices.",
                        "error",
                    )
                )
                continue
            for point in ring:
                if _xy(point) is None:
                    errors.append(
                        _warn(
                            "invalid_blocked_polygons",
                            f"blockedPolygonsXY[{index}] contains a non-finite vertex.",
                            "error",
                        )
                    )
                    break
    return errors


def _validate_plan(region: Region, request: Mapping[str, Any]) -> list[dict[str, str]]:
    errors = _validate_common(region, request)
    budget = _num(request.get("totalBudgetMin"))
    reserve = _num(request.get("reserveMin"))
    dwell = _num(request.get("dwellMin"))
    if budget is None or budget < 0:
        errors.append(_warn("invalid_budget", "totalBudgetMin must be >= 0.", "error"))
    if reserve is None or reserve < 0:
        errors.append(_warn("invalid_reserve", "reserveMin must be >= 0.", "error"))
    if dwell is None or dwell < 0:
        errors.append(_warn("invalid_dwell", "dwellMin must be >= 0.", "error"))
    if budget is not None and reserve is not None and reserve > budget:
        errors.append(
            _warn(
                "invalid_budget",
                f"reserveMin ({reserve:g}) must not exceed totalBudgetMin ({budget:g}).",
                "error",
            )
        )
    return errors


def _validate_rehearsal(region: Region, request: Mapping[str, Any]) -> list[dict[str, str]]:
    errors = _validate_common(region, request)
    current = _xy(request.get("currentXY"))
    if current is None:
        errors.append(_warn("invalid_current", "currentXY must be finite [x_m, y_m].", "error"))
    elapsed = _num(request.get("elapsedMin"))
    remaining = _num(request.get("remainingBudgetMin"))
    dwell = _num(request.get("dwellMin"))
    reserve = _num(request.get("reserveMin"))
    if elapsed is None or elapsed < 0:
        errors.append(_warn("invalid_elapsed", "elapsedMin must be >= 0.", "error"))
    if remaining is None or remaining < 0:
        errors.append(_warn("invalid_remaining", "remainingBudgetMin must be >= 0.", "error"))
    if dwell is None or dwell < 0:
        errors.append(_warn("invalid_dwell", "dwellMin must be >= 0.", "error"))
    if reserve is None or reserve < 0:
        errors.append(_warn("invalid_reserve", "reserveMin must be >= 0.", "error"))
    mode = request.get("routeMode", "shortest")
    if mode not in ("shortest", "slope_penalized"):
        errors.append(_warn("invalid_route_mode", "routeMode must be shortest or slope_penalized.", "error"))
    return errors


# ---------------------------------------------------------------------------
# Result construction helpers
# ---------------------------------------------------------------------------

def _empty_leg(status: str, source_ids: list[str], warnings: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "pathXY": None,
        "distanceM": None,
        "ascentM": None,
        "maxSlopeDeg": None,
        "meanSlopeDeg": None,
        "travelMin": None,
        "profile": [],
        "sourceIds": list(source_ids),
        "datasetVersion": "",
        "modelVersion": "",
        "warnings": list(warnings or []),
    }


def _empty_route(
    mode: str,
    status: str,
    request: Mapping[str, Any],
    source_ids: list[str],
    warnings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    dwell = _num(request.get("dwellMin")) or 0.0
    reserve = _num(request.get("reserveMin")) or 0.0
    leg = _empty_leg(status, source_ids, warnings)
    return {
        "mode": mode,
        "status": status,
        "outbound": leg,
        "return": _empty_leg(status, source_ids, warnings),
        "pathXY": None,
        "distanceM": None,
        "ascentM": None,
        "maxSlopeDeg": None,
        "meanSlopeDeg": None,
        "travelMin": None,
        "dwellMin": dwell,
        "reserveMin": reserve,
        "totalRequiredMin": None,
        "marginMin": None,
        "profile": [],
        "sourceIds": list(source_ids),
        "datasetVersion": "",
        "modelVersion": "",
        "warnings": list(warnings or []),
    }


def _downsample(indices: list[int], max_samples: int = MAX_PROFILE_SAMPLES) -> list[int]:
    if len(indices) <= max_samples:
        return indices
    if max_samples < 2:  # pragma: no cover - internal guard
        return indices[-1:]
    step = (len(indices) - 1) / (max_samples - 1)
    picked = [indices[int(round(i * step))] for i in range(max_samples)]
    out: list[int] = []
    for idx in picked:
        if not out or out[-1] != idx:
            out.append(idx)
    return out


def _profile_for_path(grid: Grid, rc: Sequence[tuple[int, int]]) -> tuple[list[dict[str, Any]], float]:
    """Return a downsampled profile and the exact path distance in metres."""

    if not rc:
        return [], 0.0
    distances = [0.0]
    for (r0, c0), (r1, c1) in zip(rc, rc[1:]):
        distances.append(distances[-1] + grid.step_distance_m(r1 - r0, c1 - c0))
    total = distances[-1]
    indices = _downsample(list(range(len(rc))))
    profile = []
    for idx in indices:
        r, c = rc[idx]
        elev = grid.elevation_at(r, c)
        slope = grid.slope_at(r, c)
        profile.append(
            {
                "distanceM": _r(distances[idx]) or 0.0,
                "elevationM": _r(elev) if elev is not None else None,
                "slopeDeg": _r(slope),
            }
        )
    return profile, total


def _leg_from_route(
    grid: Grid,
    result: RouteResult,
    speed: float,
    source_ids: list[str],
) -> dict[str, Any]:
    if result.status != "ok" or not result.path_rc:
        return _empty_leg("no_path", source_ids, result.warnings)

    rc = result.path_rc
    elevations = [grid.elevation_at(r, c) for r, c in rc]
    slopes = [grid.slope_at(r, c) for r, c in rc]
    if any(e is None for e in elevations) or any(s is None for s in slopes):
        return _empty_leg(
            "no_path",
            source_ids,
            [_warn("invalid_path_data", "Path crosses an unknown elevation/slope cell.", "error")],
        )

    distance = float(result.distance_m or 0.0)
    ascent = sum(max(0.0, elevations[i] - elevations[i - 1]) for i in range(1, len(elevations)))

    # Distance-weighted mean slope with half-segment endpoint weights.
    if len(rc) == 1:
        mean_slope = float(slopes[0])
    else:
        seg = [
            grid.step_distance_m(rc[i][0] - rc[i - 1][0], rc[i][1] - rc[i - 1][1])
            for i in range(1, len(rc))
        ]
        weights = [seg[0] / 2.0]
        for i in range(1, len(rc) - 1):
            weights.append((seg[i - 1] + seg[i]) / 2.0)
        weights.append(seg[-1] / 2.0)
        total_weight = sum(weights)
        mean_slope = (
            sum(float(s) * w for s, w in zip(slopes, weights)) / total_weight
            if total_weight > 0
            else float(slopes[0])
        )

    profile, _ = _profile_for_path(grid, rc)
    travel = distance / speed
    xy = [grid.pixel_to_xy(r, c) for r, c in rc]
    return {
        "status": "ok",
        "pathXY": xy,
        "distanceM": _r(distance),
        "ascentM": _r(ascent),
        "maxSlopeDeg": _r(max(float(s) for s in slopes)),
        "meanSlopeDeg": _r(mean_slope),
        "travelMin": _r(travel),
        "profile": profile,
        "sourceIds": list(source_ids),
        "datasetVersion": "",
        "modelVersion": "",
        "warnings": list(result.warnings),
    }


def _combine_profiles(
    outbound: Mapping[str, Any],
    return_leg: Mapping[str, Any],
) -> list[dict[str, Any]]:
    combined: list[dict[str, Any]] = []
    for sample in outbound.get("profile", []):
        combined.append(dict(sample))
    offset = float(outbound.get("distanceM") or 0.0)
    for sample in return_leg.get("profile", []):
        item = dict(sample)
        item["distanceM"] = _r(offset + float(sample.get("distanceM", 0.0)))
        combined.append(item)
    return combined


def _combine_legs(
    outbound: Mapping[str, Any],
    return_leg: Mapping[str, Any],
    speed: float,
    dwell: float,
    reserve: float,
    budget: float,
    source_ids: list[str],
    dataset_version: str,
    model_version: str,
) -> dict[str, Any]:
    if outbound.get("status") != "ok" or return_leg.get("status") != "ok":
        warnings = list(outbound.get("warnings", [])) + list(return_leg.get("warnings", []))
        result = _empty_leg("no_path", source_ids, warnings)
        return {
            "mode": "combined",
            "status": "no_path",
            "outbound": dict(outbound),
            "return": dict(return_leg),
            "pathXY": None,
            "distanceM": None,
            "ascentM": None,
            "maxSlopeDeg": None,
            "meanSlopeDeg": None,
            "travelMin": None,
            "dwellMin": dwell,
            "reserveMin": reserve,
            "totalRequiredMin": None,
            "marginMin": None,
            "profile": [],
            "sourceIds": list(source_ids),
            "datasetVersion": dataset_version,
            "modelVersion": model_version,
            "warnings": warnings,
        }

    d_out = float(outbound["distanceM"])
    d_ret = float(return_leg["distanceM"])
    distance = d_out + d_ret
    travel = distance / speed
    required = travel + dwell + reserve
    margin = budget - required
    mean = (
        (float(outbound["meanSlopeDeg"]) * d_out + float(return_leg["meanSlopeDeg"]) * d_ret) / distance
        if distance > 0
        else float(outbound["meanSlopeDeg"])
    )
    path = list(outbound["pathXY"] or [])
    ret_path = list(return_leg["pathXY"] or [])
    if ret_path:
        path += ret_path[1:]
    return {
        "mode": "combined",
        "status": "ok" if margin >= -1e-9 else "over_budget",
        "outbound": dict(outbound),
        "return": dict(return_leg),
        "pathXY": path or None,
        "distanceM": _r(distance),
        "ascentM": _r(float(outbound["ascentM"]) + float(return_leg["ascentM"])),
        "maxSlopeDeg": _r(max(float(outbound["maxSlopeDeg"]), float(return_leg["maxSlopeDeg"]))),
        "meanSlopeDeg": _r(mean),
        "travelMin": _r(travel),
        "dwellMin": _r(dwell),
        "reserveMin": _r(reserve),
        "totalRequiredMin": _r(required),
        "marginMin": _r(margin),
        "profile": _combine_profiles(outbound, return_leg),
        "sourceIds": list(source_ids),
        "datasetVersion": dataset_version,
        "modelVersion": model_version,
        "warnings": list(outbound.get("warnings", [])) + list(return_leg.get("warnings", [])),
    }


def _aggregate_status(statuses: Sequence[str]) -> str:
    if "invalid_input" in statuses:
        return "invalid_input"
    if "data_unavailable" in statuses:
        return "data_unavailable"
    if "no_path" in statuses:
        return "no_path"
    if "over_budget" in statuses:
        return "over_budget"
    return "ok"


def _invalid_plan_response(
    region: Region,
    request: Mapping[str, Any],
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    source_ids: list[str] = []
    target_id = request.get("targetId")
    if isinstance(target_id, str):
        source_ids = region.target_source_ids(target_id)
    routes = {
        mode: _empty_route(mode, "invalid_input", request, source_ids)
        for mode in ("shortest", "slope_penalized")
    }
    for route_result in routes.values():
        route_result["datasetVersion"] = region.dataset_version
        route_result["modelVersion"] = region.model_version
        for leg_name in ("outbound", "return"):
            route_result[leg_name]["datasetVersion"] = region.dataset_version
            route_result[leg_name]["modelVersion"] = region.model_version
    return {
        "requestId": str(request.get("requestId", "")),
        "planId": compute_plan_id(request, region),
        "schemaVersion": SCHEMA_VERSION,
        "datasetVersion": region.dataset_version,
        "modelVersion": region.model_version,
        "status": "invalid_input",
        "routes": routes,
        "warnings": list(region.warnings),
        "errors": errors,
        "generatedAt": _now(),
    }


# ---------------------------------------------------------------------------
# Plan evaluation
# ---------------------------------------------------------------------------

def evaluate_plan(region: Region, request: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate both route modes and return the plan response object."""

    if not isinstance(request, Mapping):
        raise TypeError("request must be a mapping")
    errors = _validate_plan(region, request)
    if errors:
        return _invalid_plan_response(region, request, errors)

    base = _xy(request["baseXY"])
    target = region.stop(str(request["targetId"]))
    assert base is not None and target is not None  # validated above
    target_xy = _xy(target.get("xy"))
    if target_xy is None:
        return _invalid_plan_response(
            region,
            request,
            [_warn("invalid_target_geometry", "Target science stop has no finite xy.", "error")],
        )

    max_slope = float(_num(request["maxSlopeDeg"]))  # type: ignore[arg-type]
    speed = float(_num(request["speedMPerMin"]))  # type: ignore[arg-type]
    budget = float(_num(request["totalBudgetMin"]))  # type: ignore[arg-type]
    reserve = float(_num(request["reserveMin"]))  # type: ignore[arg-type]
    dwell = float(_num(request["dwellMin"]))  # type: ignore[arg-type]
    polygons = request.get("blockedPolygonsXY") or []
    source_ids = region.target_source_ids(str(request["targetId"]))
    dataset_version = region.dataset_version
    model_version = region.model_version

    base_px = region.grid.xy_to_pixel(*base)
    if base_px is None:
        return _invalid_plan_response(
            region,
            request,
            [_warn("base_out_of_bounds", f"baseXY {list(base)} lies outside the regional grid.", "error")],
        )
    target_px = region.grid.xy_to_pixel(*target_xy)
    if target_px is None:
        return _invalid_plan_response(
            region,
            request,
            [
                _warn(
                    "target_out_of_bounds",
                    f"Target {request['targetId']!r} lies outside the regional grid.",
                    "error",
                )
            ],
        )

    try:
        blocked_mask = rasterize_blocked(region.grid, polygons)
    except ValueError as exc:
        return _invalid_plan_response(
            region,
            request,
            [_warn("invalid_blocked_polygons", str(exc), "error")],
        )

    if not region.grid.traversable(base_px[0], base_px[1], blocked=blocked_mask):
        return _invalid_plan_response(
            region,
            request,
            [
                _warn(
                    "base_unusable",
                    "baseXY is on no-data, inside a closure, or steeper than the slope ceiling.",
                    "error",
                )
            ],
        )

    routes: dict[str, dict[str, Any]] = {}
    for mode in ("shortest", "slope_penalized"):
        outbound_result = route(
            region.grid,
            base,
            target_xy,
            mode=mode,
            max_slope_deg=max_slope,
            blocked_polygons=polygons,
        )
        return_result = route(
            region.grid,
            target_xy,
            base,
            mode=mode,
            max_slope_deg=max_slope,
            blocked_polygons=polygons,
        )
        outbound = _leg_from_route(region.grid, outbound_result, speed, source_ids)
        return_leg = _leg_from_route(region.grid, return_result, speed, source_ids)
        for leg in (outbound, return_leg):
            leg["datasetVersion"] = dataset_version
            leg["modelVersion"] = model_version
        combined = _combine_legs(
            outbound,
            return_leg,
            speed,
            dwell,
            reserve,
            budget,
            source_ids,
            dataset_version,
            model_version,
        )
        combined["mode"] = mode
        routes[mode] = combined

    status = _aggregate_status([r["status"] for r in routes.values()])
    warnings = list(region.warnings)
    if status == "over_budget":
        warnings.append(
            _warn(
                "over_budget",
                "At least one route mode exceeds the total time budget.",
                "warning",
            )
        )
    if status == "no_path":
        warnings.append(
            _warn(
                "route_unavailable",
                "At least one route mode has no traversable path under the current constraints.",
                "warning",
            )
        )

    return {
        "requestId": str(request.get("requestId", "")),
        "planId": compute_plan_id(request, region),
        "schemaVersion": SCHEMA_VERSION,
        "datasetVersion": dataset_version,
        "modelVersion": model_version,
        "status": status,
        "routes": routes,
        "warnings": warnings,
        "generatedAt": _now(),
    }


# ---------------------------------------------------------------------------
# Rehearsal evaluation
# ---------------------------------------------------------------------------

def _empty_assessment(
    label: str,
    status: str,
    source_ids: list[str],
    dwell: float,
    reserve: float,
    dataset_version: str,
    model_version: str,
    warnings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "label": label,
        "status": status,
        "pathXY": None,
        "distanceM": None,
        "ascentM": None,
        "maxSlopeDeg": None,
        "meanSlopeDeg": None,
        "travelMin": None,
        "dwellMin": _r(dwell) or 0.0,
        "reserveMin": _r(reserve) or 0.0,
        "totalRequiredMin": None,
        "marginMin": None,
        "profile": [],
        "sourceIds": list(source_ids),
        "datasetVersion": dataset_version,
        "modelVersion": model_version,
        "warnings": list(warnings or []),
    }


def _assessment_from_legs(
    label: str,
    legs: Sequence[Mapping[str, Any]],
    speed: float,
    dwell: float,
    reserve: float,
    budget: float,
    source_ids: list[str],
    dataset_version: str,
    model_version: str,
) -> dict[str, Any]:
    if any(leg.get("status") != "ok" for leg in legs):
        warnings = [w for leg in legs for w in leg.get("warnings", [])]
        return _empty_assessment(
            label,
            "no_path",
            source_ids,
            dwell,
            reserve,
            dataset_version,
            model_version,
            warnings,
        )

    distance = sum(float(leg["distanceM"]) for leg in legs)
    ascent = sum(float(leg["ascentM"]) for leg in legs)
    max_slope = max(float(leg["maxSlopeDeg"]) for leg in legs)
    mean = (
        sum(float(leg["meanSlopeDeg"]) * float(leg["distanceM"]) for leg in legs) / distance
        if distance > 0
        else float(legs[0]["meanSlopeDeg"])
    )
    travel = distance / speed
    required = travel + dwell + reserve
    margin = budget - required

    path: list[list[float]] = []
    profile: list[dict[str, Any]] = []
    offset = 0.0
    for leg in legs:
        leg_path = list(leg.get("pathXY") or [])
        if leg_path:
            path += leg_path if not path else leg_path[1:]
        for sample in leg.get("profile", []):
            item = dict(sample)
            item["distanceM"] = _r(offset + float(sample.get("distanceM", 0.0)))
            profile.append(item)
        offset += float(leg.get("distanceM") or 0.0)

    warnings = [w for leg in legs for w in leg.get("warnings", [])]
    return {
        "label": label,
        "status": "ok" if margin >= -1e-9 else "over_budget",
        "pathXY": path or None,
        "distanceM": _r(distance),
        "ascentM": _r(ascent),
        "maxSlopeDeg": _r(max_slope),
        "meanSlopeDeg": _r(mean),
        "travelMin": _r(travel),
        "dwellMin": _r(dwell) or 0.0,
        "reserveMin": _r(reserve) or 0.0,
        "totalRequiredMin": _r(required),
        "marginMin": _r(margin),
        "profile": profile,
        "sourceIds": list(source_ids),
        "datasetVersion": dataset_version,
        "modelVersion": model_version,
        "warnings": warnings,
    }


def evaluate_rehearsal(region: Region, request: Mapping[str, Any]) -> dict[str, Any]:
    """Recompute return options from the current position.

    ``remainingBudgetMin`` is the time available *now*. ``elapsedMin`` is echoed
    for context but is never subtracted a second time.
    """

    if not isinstance(request, Mapping):
        raise TypeError("request must be a mapping")
    errors = _validate_rehearsal(region, request)
    if errors:
        return _invalid_rehearsal_response(region, request, errors)

    current = _xy(request["currentXY"])
    base = _xy(request["baseXY"])
    target = region.stop(str(request["targetId"]))
    assert current is not None and base is not None and target is not None
    target_xy = _xy(target.get("xy"))
    if target_xy is None:
        return _invalid_rehearsal_response(
            region,
            request,
            [_warn("invalid_target_geometry", "Target science stop has no finite xy.", "error")],
        )

    max_slope = float(_num(request["maxSlopeDeg"]))  # type: ignore[arg-type]
    speed = float(_num(request["speedMPerMin"]))  # type: ignore[arg-type]
    elapsed = float(_num(request["elapsedMin"]))  # type: ignore[arg-type]
    remaining = float(_num(request["remainingBudgetMin"]))  # type: ignore[arg-type]
    dwell = float(_num(request["dwellMin"]))  # type: ignore[arg-type]
    reserve = float(_num(request["reserveMin"]))  # type: ignore[arg-type]
    mode = str(request.get("routeMode", "shortest"))
    polygons = request.get("blockedPolygonsXY") or []
    source_ids = region.target_source_ids(str(request["targetId"]))
    dataset_version = region.dataset_version
    model_version = region.model_version

    current_px = region.grid.xy_to_pixel(*current)
    if current_px is None:
        return _invalid_rehearsal_response(
            region,
            request,
            [
                _warn(
                    "current_out_of_bounds",
                    f"currentXY {list(current)} lies outside the regional grid.",
                    "error",
                )
            ],
        )

    try:
        blocked_mask = rasterize_blocked(region.grid, polygons)
    except ValueError as exc:
        return _invalid_rehearsal_response(
            region,
            request,
            [_warn("invalid_blocked_polygons", str(exc), "error")],
        )

    if not region.grid.traversable(current_px[0], current_px[1], blocked=blocked_mask):
        message = (
            "currentXY is invalid under the injected closures, no-data mask, or slope "
            "ceiling; the position was not moved."
        )
        response = _invalid_rehearsal_response(
            region,
            request,
            [_warn("current_position_blocked", message, "error")],
        )
        response["currentPositionValid"] = False
        return response

    immediate_route = route(
        region.grid,
        current,
        base,
        mode=mode,
        max_slope_deg=max_slope,
        blocked_polygons=polygons,
    )
    immediate_leg = _leg_from_route(region.grid, immediate_route, speed, source_ids)
    immediate = _assessment_from_legs(
        "immediate_return",
        [immediate_leg],
        speed,
        0.0,
        reserve,
        remaining,
        source_ids,
        dataset_version,
        model_version,
    )

    to_target_route = route(
        region.grid,
        current,
        target_xy,
        mode=mode,
        max_slope_deg=max_slope,
        blocked_polygons=polygons,
    )
    return_route = route(
        region.grid,
        target_xy,
        base,
        mode=mode,
        max_slope_deg=max_slope,
        blocked_polygons=polygons,
    )
    to_target = _leg_from_route(region.grid, to_target_route, speed, source_ids)
    back_to_base = _leg_from_route(region.grid, return_route, speed, source_ids)
    for leg in (to_target, back_to_base):
        leg["datasetVersion"] = dataset_version
        leg["modelVersion"] = model_version
    continue_then_return = _assessment_from_legs(
        "continue_then_return",
        [to_target, back_to_base],
        speed,
        dwell,
        reserve,
        remaining,
        source_ids,
        dataset_version,
        model_version,
    )

    for assessment in (immediate, continue_then_return):
        assessment["datasetVersion"] = dataset_version
        assessment["modelVersion"] = model_version

    status = _aggregate_status([immediate["status"], continue_then_return["status"]])
    warnings = list(region.warnings)
    if continue_then_return["status"] == "over_budget" and immediate["status"] == "ok":
        warnings.append(
            _warn(
                "continue_exceeds_budget",
                "Immediate return fits the remaining budget but continuing to the target "
                "and returning does not.",
                "warning",
            )
        )

    return {
        "requestId": str(request.get("requestId", "")),
        "rehearsalId": compute_rehearsal_id(request, region),
        "schemaVersion": SCHEMA_VERSION,
        "datasetVersion": dataset_version,
        "modelVersion": model_version,
        "status": status,
        "currentPositionValid": True,
        "currentXY": [current[0], current[1]],
        "elapsedMin": _r(elapsed),
        "remainingBudgetMin": _r(remaining),
        "immediateReturn": immediate,
        "continueThenReturn": continue_then_return,
        "warnings": warnings,
        "generatedAt": _now(),
    }


def _invalid_rehearsal_response(
    region: Region,
    request: Mapping[str, Any],
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    source_ids: list[str] = []
    target_id = request.get("targetId")
    if isinstance(target_id, str):
        source_ids = region.target_source_ids(target_id)
    dwell = _num(request.get("dwellMin")) or 0.0
    reserve = _num(request.get("reserveMin")) or 0.0
    elapsed = _num(request.get("elapsedMin")) or 0.0
    remaining = _num(request.get("remainingBudgetMin")) or 0.0
    current = _xy(request.get("currentXY"))
    immediate = _empty_assessment(
        "immediate_return",
        "invalid_input",
        source_ids,
        0.0,
        reserve,
        region.dataset_version,
        region.model_version,
    )
    continue_then_return = _empty_assessment(
        "continue_then_return",
        "invalid_input",
        source_ids,
        dwell,
        reserve,
        region.dataset_version,
        region.model_version,
    )
    return {
        "requestId": str(request.get("requestId", "")),
        "rehearsalId": compute_rehearsal_id(request, region),
        "schemaVersion": SCHEMA_VERSION,
        "datasetVersion": region.dataset_version,
        "modelVersion": region.model_version,
        "status": "invalid_input",
        "currentPositionValid": current is not None,
        "currentXY": [current[0], current[1]] if current is not None else None,
        "elapsedMin": _r(elapsed) or 0.0,
        "remainingBudgetMin": _r(remaining) or 0.0,
        "immediateReturn": immediate,
        "continueThenReturn": continue_then_return,
        "warnings": list(region.warnings),
        "errors": errors,
        "generatedAt": _now(),
    }
