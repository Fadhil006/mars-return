import json
import hashlib

import numpy as np
import pytest
import rasterio
from PIL import Image
from rasterio.transform import from_origin

from server.preprocess import prepare_region


def test_prepare_region_plane_nodata_and_aligned_layers(tmp_path):
    crs = rasterio.crs.CRS.from_epsg(3857)
    transform = from_origin(0, 100, 10, 10)
    y, x = np.mgrid[95:-5:-10, 5:105:10]
    plane = (0.1 * x + 0.2 * y).astype("float32")
    plane[4, 4] = -9999
    dem_path, image_path = tmp_path / "dem.tif", tmp_path / "image.tif"
    with rasterio.open(dem_path, "w", driver="GTiff", width=10, height=10, count=1,
                       dtype="float32", crs=crs, transform=transform, nodata=-9999) as dst:
        dst.write(plane, 1)
    with rasterio.open(image_path, "w", driver="GTiff", width=20, height=20, count=1,
                       dtype="uint8", crs=crs, transform=from_origin(0, 100, 5, 5), nodata=0) as dst:
        image = np.full((20, 20), 100, dtype="uint8")
        image[:4, :4] = 0
        dst.write(image, 1)

    out = tmp_path / "region"
    manifest = prepare_region({"elevation": dem_path, "imagery": image_path},
                              [0, 0, 100, 100], out, cell_size_m=10)
    elevation = json.loads((out / "elevation.json").read_text())
    slope = json.loads((out / "slope.json").read_text())
    mask = json.loads((out / "mask.json").read_text())

    expected = np.degrees(np.arctan(np.hypot(0.1, 0.2)))
    assert manifest["width"] == manifest["height"] == 10
    assert abs(slope[2][2] - expected) < 1e-5
    assert elevation[4][4] is None
    assert slope[4][4] is None and mask[4][4] is False
    assert all(len(grid) == 10 and all(len(row) == 10 for row in grid)
               for grid in (elevation, slope, mask))
    assert mask[2][2] is True
    assert all(isinstance(value, bool) for row in mask for value in row)
    assert (out / "imagery.webp").is_file()
    assert manifest["sourceIds"] == []
    assert "Mars" not in manifest["sourceDatumWKT"]
    assert manifest["pixelToLocalTransform"] == [10.0, 0, 0, 0, -10.0, 100.0]
    for layer, filename in manifest["layers"].items():
        assert hashlib.sha256((out / filename).read_bytes()).hexdigest() == manifest["checksums"][filename]
    assert manifest["coverage"]["imageryValidCells"] < 100
    assert mask[0][0] is False
    assert Image.open(out / "imagery.webp").getpixel((0, 0))[3] == 0


def test_half_cell_shift_preserves_nodata_interpolation_support(tmp_path):
    crs = rasterio.crs.CRS.from_epsg(3857)
    transform = from_origin(0, 120, 10, 10)
    dem_path, image_path = tmp_path / "dem.tif", tmp_path / "image.tif"
    dem = np.ones((12, 12), dtype="float32")
    dem[6, 6] = -9999
    with rasterio.open(dem_path, "w", driver="GTiff", width=12, height=12, count=1,
                       dtype="float32", crs=crs, transform=transform, nodata=-9999) as dst:
        dst.write(dem, 1)
    with rasterio.open(image_path, "w", driver="GTiff", width=24, height=24, count=1,
                       dtype="uint8", crs=crs, transform=from_origin(0, 120, 5, 5)) as dst:
        dst.write(np.full((24, 24), 100, dtype="uint8"), 1)

    out = tmp_path / "shifted"
    prepare_region({"elevation": dem_path, "imagery": image_path}, [5, 5, 95, 95], out, 10)
    elevation = json.loads((out / "elevation.json").read_text())
    mask = json.loads((out / "mask.json").read_text())
    # This shifted cell interpolates from source pixels including the nodata sample.
    assert elevation[4][5] is None
    assert mask[4][5] is False


def test_rejects_upsampling_nonfinite_inputs_and_rotated_dem(tmp_path):
    crs = rasterio.crs.CRS.from_epsg(3857)
    dem_path, image_path = tmp_path / "dem.tif", tmp_path / "image.tif"
    with rasterio.open(dem_path, "w", driver="GTiff", width=10, height=10, count=1,
                       dtype="float32", crs=crs, transform=from_origin(0, 100, 10, 10)) as dst:
        dst.write(np.ones((10, 10), dtype="float32"), 1)
    with rasterio.open(image_path, "w", driver="GTiff", width=20, height=20, count=1,
                       dtype="uint8", crs=crs, transform=from_origin(0, 100, 5, 5)) as dst:
        dst.write(np.ones((20, 20), dtype="uint8"), 1)

    paths = {"elevation": dem_path, "imagery": image_path}
    with pytest.raises(ValueError, match="cell size"):
        prepare_region(paths, [0, 0, 100, 100], tmp_path / "fine", 5)
    with pytest.raises(ValueError, match="finite"):
        prepare_region(paths, [0, 0, float("nan"), 100], tmp_path / "nan", 10)
    rotated = tmp_path / "rotated.tif"
    with rasterio.open(rotated, "w", driver="GTiff", width=10, height=10, count=1,
                       dtype="float32", crs=crs, transform=rasterio.Affine(10, 1, 0, 0, -10, 100)) as dst:
        dst.write(np.ones((10, 10), dtype="float32"), 1)
    paths["elevation"] = rotated
    with pytest.raises(ValueError, match="rotated"):
        prepare_region(paths, [0, 0, 100, 100], tmp_path / "rot", 10)
