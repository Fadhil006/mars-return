"""Derive real Perseverance sample-site stops and the rover traverse layer for the Jezero crop.

Reads NASA's public Mars 2020 waypoint/traverse GeoJSON (downloaded to data/raw/m20/ when absent)
and the transcribed sample inventory, then writes the two small tracked region files. The NASA
files are live and grow with every drive, so the SHA-256 of the copy actually used is recorded
in the output instead of being pinned.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CROP = [4353000, 1091800, 4356000, 1094800]  # projected west, south, east, north; same as prepare_demo
RADIUS_M, STANDARD_PARALLEL_DEG = 3396190, 18.4663  # the DEM's equirectangular Mars sphere projection
BASE_URL = "https://mars.nasa.gov/mmgis-maps/M20/Layers/json/"
SOURCE_IDS = {"M20_waypoints.json": "nasa-m20-waypoints", "M20_traverse.json": "nasa-m20-traverse"}


def project(lon, lat):
    return (RADIUS_M * math.radians(lon) * math.cos(math.radians(STANDARD_PARALLEL_DEG)),
            RADIUS_M * math.radians(lat))


def local(easting, northing):
    """Projected metres to the crop's local frame, or None when outside it."""
    x, y = easting - CROP[0], northing - CROP[1]
    return [round(x, 1), round(y, 1)] if 0 <= x < CROP[2] - CROP[0] and 0 <= y < CROP[3] - CROP[1] else None


def build_science(waypoints, traverse, sample_sites):
    """Return (science stops, traverse layer) from parsed GeoJSON and the sample inventory."""
    points = []
    for feature in waypoints["features"]:
        p = feature["properties"]
        # NASA supplies both forms; refuse to continue if our projection disagrees with theirs.
        x, y = project(p["lon"], p["lat"])
        if math.hypot(x - p["easting"], y - p["northing"]) > 1:
            raise ValueError(f"Projection disagrees with NASA easting/northing at sol {p['sol']}")
        points.append(p)
    points.sort(key=lambda p: (p["sol"], p["dist_total_m"]))
    inside = [(p, local(p["easting"], p["northing"])) for p in points]
    inside = [(p, xy) for p, xy in inside if xy]
    last_sol = max(p["sol"] for p, _ in inside)

    stops = []
    for site in sample_sites:
        first_sol = min(s["sol"] for s in site["samples"])
        earlier = [p for p in points if p["sol"] <= first_sol]
        if not earlier or local(earlier[-1]["easting"], earlier[-1]["northing"]) is None:
            raise ValueError(f"No in-crop rover localization on or before sol {first_sol} for {site['id']}")
        rover = earlier[-1]
        names = ", ".join(f"{s['name']} (sol {s['sol']})" for s in site["samples"])
        stops.append({
            "id": site["id"], "name": f"{site['feature']} — {site['samplingLocation']}",
            "positionXY": local(rover["easting"], rover["northing"]), "kind": "rover_sample_site",
            "locationUncertaintyM": None, "gridSpacingM": 20,
            "sourceIds": ["nasa-m20-waypoints", "nasa-perseverance-mars-rock-samples", "usgs-m20-ctx-dem-20m"],
            "samples": site["samples"], "roverSol": rover["sol"], "roverRMC": rover["RMC"],
            "roverElevationM": rover["elev_geoid"],
            "description": f"Perseverance sampling site. NASA's inventory lists {names} at {site['feature']}, {site['samplingLocation']}.",
            "scientificQuestion": "What would a crew observe and collect here that the rover's cores and instruments could not?",
            "locationProvenance": f"Rover end-of-drive localization on sol {rover['sol']} (RMC {rover['RMC']}), the last "
                                  f"localization on or before the first sample was sealed on sol {first_sol}. This is the "
                                  "rover's position, not the drill target within arm's reach; no geodetic uncertainty is published.",
        })

    path = []
    for feature in sorted(traverse["features"], key=lambda f: f["properties"]["sol"]):
        if feature["properties"]["sol"] > last_sol:
            continue
        geometry = feature["geometry"]
        lines = [geometry["coordinates"]] if geometry["type"] == "LineString" else geometry["coordinates"]
        for line in lines:
            for lon, lat, *_ in line:
                xy = local(*project(lon, lat))
                if xy and (not path or xy != path[-1]):
                    path.append(xy)
    layer = {"sourceIds": sorted(SOURCE_IDS.values()), "solRange": [inside[0][0]["sol"], last_sol],
             "note": "Real Perseverance localizations inside the crop, in the region's local metric frame. "
                     "Positions are rover localizations, not surveyed ground control.",
             "waypoints": [{"sol": p["sol"], "rmc": p["RMC"], "xy": xy, "elevationM": p["elev_geoid"],
                            "odometerM": p["dist_total_m"]} for p, xy in inside],
             "pathXY": path}
    return stops, layer


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    raw, hashes, parsed = ROOT / "data/raw/m20", {}, {}
    raw.mkdir(parents=True, exist_ok=True)
    for name in SOURCE_IDS:
        path = raw / name
        if not path.exists():
            with urlopen(BASE_URL + name, timeout=120) as source:
                path.write_bytes(source.read())
        hashes[SOURCE_IDS[name]] = hashlib.sha256(path.read_bytes()).hexdigest()
        parsed[name] = json.loads(path.read_text())
    samples = json.loads((ROOT / "data/sources/m20-samples.json").read_text())
    stops, layer = build_science(parsed["M20_waypoints.json"], parsed["M20_traverse.json"], samples["sites"])
    layer["sourceSha256"] = hashes
    region = ROOT / "data/region"
    (region / "science-stops.json").write_text(json.dumps(stops, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    (region / "rover-traverse.json").write_text(json.dumps(layer, ensure_ascii=False, allow_nan=False) + "\n")
    print(f"{len(stops)} sample sites, {len(layer['waypoints'])} rover localizations, {len(layer['pathXY'])} path points")
    print("Now run: python -m scripts.prepare_demo")


if __name__ == "__main__":
    main()
