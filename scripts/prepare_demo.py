"""Acquire checksum-verified CTX inputs and reproduce the documented Jezero demo."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen

from server.preprocess import prepare_region
from server.region import load_region

ROOT = Path(__file__).resolve().parents[1]


def fetch_verified(url, destination, expected_sha256):
    """Keep a partial or mismatching download out of the source path."""
    destination = Path(destination)
    if destination.exists():
        with destination.open("rb") as existing:
            digest = hashlib.file_digest(existing, "sha256").hexdigest()
        if digest != expected_sha256:
            raise ValueError(f"Checksum mismatch for existing source: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            digest = hashlib.sha256()
            with urlopen(url, timeout=120) as source:
                while chunk := source.read(1024*1024):
                    digest.update(chunk)
                    output.write(chunk)
        if digest.hexdigest() != expected_sha256:
            raise ValueError(f"Downloaded checksum mismatch: {url}")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def prepare_demo():
    records = [json.loads((ROOT / f"data/sources/{name}.json").read_text()) for name in ("ctx-dem", "ctx-ortho")]
    paths = {}
    for layer, record in zip(("elevation", "imagery"), records):
        path = ROOT / "data/raw" / record["productId"]
        fetch_verified(record["url"], path, record["sha256"])
        paths[layer] = path
    directory = ROOT / "data/region"
    manifest = prepare_region(paths, [4353000, 1091800, 4356000, 1094800], directory, 20)
    science = json.loads((ROOT / "data/sources/science.json").read_text())["sources"]
    manifest["sources"] = records + science
    manifest["checksums"]["science-stops.json"] = hashlib.sha256((directory / "science-stops.json").read_bytes()).hexdigest()
    manifest["scenario"] = {"baseXY": [510, 1510], "defaultTargetId": "terrain-observation-a",
                            "label": "Hypothetical base and observation points on real CTX terrain"}
    manifest["warnings"] = ["Base and observation points are hypothetical, not registered rover sample sites.",
                            "Three-landmark 2D/3D alignment review remains outstanding."]
    # Version the source metadata and destinations too, not only the raster bytes.
    manifest.pop("datasetVersion", None)
    manifest["datasetVersion"] = hashlib.sha256(json.dumps(manifest, sort_keys=True, allow_nan=False).encode()).hexdigest()[:16]
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False)+"\n")
    load_region(directory)
    print(f"Prepared Jezero dataset {manifest['datasetVersion']} ({manifest['width']}×{manifest['height']})")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    prepare_demo()
