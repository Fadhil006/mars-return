"""Validate and package a region: python -m scripts.package_region --region-dir data/region --output region.tar.gz."""

import argparse
import hashlib
import os
import tarfile
import tempfile
from pathlib import Path

from server.region import load_region

FILES = ("manifest.json", "science-stops.json", "imagery.webp", "elevation.json", "slope.json", "mask.json")


def package_region(region_dir, output):
    region_dir, output = Path(region_dir), Path(output)
    for path in region_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in region bundle: {path}")
    for name in FILES:
        if not (region_dir / name).is_file():
            raise FileNotFoundError(region_dir / name)
    load_region(region_dir)
    if output.exists():
        raise FileExistsError(output)

    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".tar.gz", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with tarfile.open(temporary_path, "w:gz") as archive:
            for name in FILES + ("rover-traverse.json",):
                if (region_dir / name).is_file():  # the traverse layer is optional
                    archive.add(region_dir / name, arcname=name, recursive=False)
        digest = hashlib.sha256(temporary_path.read_bytes()).hexdigest()
        # Hard-link publication is atomic and fails rather than replacing a concurrent output.
        os.link(temporary_path, output)
        return digest
    finally:
        temporary_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(package_region(args.region_dir, args.output))


if __name__ == "__main__":
    main()
