import hashlib
import json

import pytest

from server.region import load_region


def bundle(tmp_path):
    manifest = {"width": 2, "height": 2, "cellSizeM": 20,
                "originXY": [0, 0], "datasetVersion": "synthetic"}
    for name, data in {"elevation": [[0, 1], [None, 1]], "slope": [[0, 0], [None, 0]],
                       "mask": [[True, True], [False, True]],
                       "science-stops": [{"id": "s", "positionXY": [10, 30], "sourceIds": ["source"]}]}.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(data))
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return manifest


def test_valid_bundle_preserves_missing_data(tmp_path):
    bundle(tmp_path)
    region = load_region(tmp_path)
    assert region["elevation"][1][0] is None
    assert region["mask"][1][0] is False


@pytest.mark.parametrize("change", ["dimensions", "checksum", "sourceIds", "mask"])
def test_invalid_bundle(tmp_path, change):
    manifest = bundle(tmp_path)
    if change == "dimensions":
        manifest["height"] = 513
    elif change == "checksum":
        manifest["checksums"] = {"elevation.json": hashlib.sha256(b"wrong").hexdigest()}
    elif change == "sourceIds":
        manifest["sourceIds"] = [["unhashable"]]
    elif change == "mask":
        (tmp_path / "mask.json").write_text("[[1,1],[0,1]]")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_region(tmp_path)
