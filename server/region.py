"""Load a prepared, versioned region; never replace absent terrain with fixtures."""

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from server.models import RegionManifest, ScienceStop, SourceRecord
from server.coordinates import xy_to_pixel


def load_region(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    RegionManifest.model_validate(manifest)
    width, height = manifest["width"], manifest["height"]
    if type(width) is not int or type(height) is not int or not 1 <= width <= 512 or not 1 <= height <= 512:
        raise ValueError("Region dimensions must be integers between 1 and 512")
    spacing = manifest["cellSizeM"]
    if not math.isfinite(spacing) or spacing <= 0:
        raise ValueError("Invalid cell spacing")
    if len(manifest["originXY"]) != 2 or not all(math.isfinite(v) for v in manifest["originXY"]):
        raise ValueError("Invalid region origin")
    if not isinstance(manifest["datasetVersion"], str) or not manifest["datasetVersion"]:
        raise ValueError("Missing dataset version")
    def source_ids(value):
        if not isinstance(value, list) or any(not isinstance(s, str) or not s for s in value):
            raise ValueError("sourceIds must be a list of nonempty strings")
    source_ids(manifest.get("sourceIds", []))
    # Check only declared assets, and never allow a manifest to escape its directory.
    for name, expected in manifest.get("checksums", {}).items():
        path = directory / name
        if path.resolve().parent != directory.resolve():
            raise ValueError("Checksum asset must be inside the region directory")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {name}")
    region = {"manifest": manifest}
    for name in ("elevation", "slope", "mask"):
        region[name] = json.loads((directory / f"{name}.json").read_text(encoding="utf-8"))
        if np.asarray(region[name], dtype=object).shape != (height, width):
            raise ValueError(f"{name} dimensions differ from manifest")
    elevation = np.asarray(region["elevation"], dtype=float)
    slope = np.asarray(region["slope"], dtype=float)
    mask = np.asarray(region["mask"], dtype=object)
    if any(type(v) is not bool for v in mask.flat):
        raise ValueError("Mask cells must be booleans")
    valid = mask.astype(bool)
    if not np.all(np.isfinite(elevation[valid])) or not np.all(np.isfinite(slope[valid])):
        raise ValueError("Traversable cells require finite elevation and slope")
    if np.any((slope[valid] < 0) | (slope[valid] > 90)):
        raise ValueError("Slope outside 0–90 degrees")
    region["scienceStops"] = json.loads((directory / "science-stops.json").read_text(encoding="utf-8"))
    if not isinstance(region["scienceStops"], list):
        raise ValueError("science-stops.json must contain a list")
    ids = set()
    for stop in region["scienceStops"]:
        ScienceStop.model_validate(stop)
        if not isinstance(stop.get("id"), str) or not stop["id"]:
            raise ValueError("Science stop requires a nonempty string ID")
        if stop["id"] in ids:
            raise ValueError("Duplicate science-stop ID")
        ids.add(stop["id"])
        xy = stop["positionXY"]
        if len(xy) != 2 or not all(math.isfinite(v) for v in xy):
            raise ValueError("Science stop requires finite positionXY")
        row, col = xy_to_pixel(*xy, manifest)
        if not region["mask"][row][col]:
            raise ValueError("Science stop must be inside valid terrain coverage")
        source_ids(stop.get("sourceIds", []))
    region["sources"] = manifest.get("sources", [])
    if not isinstance(region["sources"], list):
        raise ValueError("sources must be a list of source records")
    for source in region["sources"]:
        SourceRecord.model_validate(source)
    known_sources = {source["sourceId"] for source in region["sources"]}
    referenced = set(manifest.get("sourceIds", [])) | {s for stop in region["scienceStops"] for s in stop.get("sourceIds", [])}
    if region["sources"] and not referenced <= known_sources:
        raise ValueError("Source reference missing from source records")
    traverse = directory / "rover-traverse.json"
    if traverse.is_file():  # optional layer; listed in checksums when the bundle was prepared with it
        region["roverTraverse"] = json.loads(traverse.read_text(encoding="utf-8"))
        if not isinstance(region["roverTraverse"].get("waypoints"), list) or not isinstance(region["roverTraverse"].get("pathXY"), list):
            raise ValueError("rover-traverse.json requires waypoints and pathXY lists")
    region["directory"] = directory
    return region
