import json
import tarfile

import pytest

from scripts.package_region import FILES, package_region
from server.region import load_region


def region_bundle(directory):
    directory.mkdir()
    (directory / "manifest.json").write_text(json.dumps({
        "width": 1, "height": 1, "cellSizeM": 20, "originXY": [0, 0], "datasetVersion": "synthetic"
    }))
    (directory / "science-stops.json").write_text("[]")
    (directory / "elevation.json").write_text("[[1]]")
    (directory / "slope.json").write_text("[[0]]")
    (directory / "mask.json").write_text("[[true]]")
    (directory / "imagery.webp").write_bytes(b"synthetic imagery")


def test_packages_validated_region_and_extracts_loadable_bundle(tmp_path):
    source, output = tmp_path / "region", tmp_path / "region.tar.gz"
    region_bundle(source)
    digest = package_region(source, output)
    assert len(digest) == 64
    extract = tmp_path / "extract"
    extract.mkdir()
    with tarfile.open(output) as archive:
        assert set(archive.getnames()) == set(FILES)
        archive.extractall(extract)
    assert load_region(extract)["manifest"]["datasetVersion"] == "synthetic"


def test_rejects_missing_file(tmp_path):
    source = tmp_path / "region"
    region_bundle(source)
    (source / "imagery.webp").unlink()
    with pytest.raises(FileNotFoundError):
        package_region(source, tmp_path / "out.tar.gz")


def test_rejects_symlink(tmp_path):
    source = tmp_path / "region"
    region_bundle(source)
    (source / "extra").symlink_to(source / "manifest.json")
    with pytest.raises(ValueError, match="Symlinks"):
        package_region(source, tmp_path / "out.tar.gz")
