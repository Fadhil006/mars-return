"""Coordinate transform tests: orientation, round trips, bounds, manifest errors."""

from __future__ import annotations

import pytest

from server.coordinates import (
    ManifestError,
    get_bounds,
    is_xy_in_bounds,
    pixel_to_xy,
    xy_to_pixel,
)
from server.tests.helpers import make_manifest


def test_pixel_centres_and_orientation():
    manifest = make_manifest(rows=4, cols=5, cell_size_m=20.0)  # 80 m tall, 100 m wide

    # row 0 is North, col 0 is West; values are cell centres.
    assert pixel_to_xy(0, 0, manifest) == [10.0, 70.0]
    assert pixel_to_xy(0, 4, manifest) == [90.0, 70.0]
    assert pixel_to_xy(3, 0, manifest) == [10.0, 10.0]
    assert pixel_to_xy(3, 4, manifest) == [90.0, 10.0]

    # East increases x, South decreases y.
    assert pixel_to_xy(0, 1, manifest)[0] > pixel_to_xy(0, 0, manifest)[0]
    assert pixel_to_xy(1, 0, manifest)[1] < pixel_to_xy(0, 0, manifest)[1]


def test_round_trip_all_cells():
    manifest = make_manifest(rows=7, cols=11, cell_size_m=10.0)
    for row in range(7):
        for col in range(11):
            x, y = pixel_to_xy(row, col, manifest)
            assert xy_to_pixel(x, y, manifest) == [row, col]


def test_out_of_bounds_returns_none():
    manifest = make_manifest(rows=4, cols=5, cell_size_m=20.0)
    assert xy_to_pixel(-1.0, 10.0, manifest) is None
    assert xy_to_pixel(10.0, -1.0, manifest) is None
    assert xy_to_pixel(100.0, 10.0, manifest) is None  # exactly the east edge
    assert xy_to_pixel(10.0, 80.0, manifest) is None  # exactly the north edge
    assert xy_to_pixel(100.0 + 0.01, 10.0, manifest) is None
    assert not is_xy_in_bounds(150.0, 40.0, manifest)
    assert is_xy_in_bounds(99.9, 79.9, manifest)


def test_pixel_out_of_range_raises():
    manifest = make_manifest(rows=4, cols=5, cell_size_m=20.0)
    with pytest.raises(IndexError):
        pixel_to_xy(4, 0, manifest)
    with pytest.raises(IndexError):
        pixel_to_xy(0, 5, manifest)
    with pytest.raises(IndexError):
        pixel_to_xy(-1, 0, manifest)


def test_bounds_are_outer_edges():
    manifest = make_manifest(rows=4, cols=5, cell_size_m=20.0)
    assert get_bounds(manifest) == {"minX": 0.0, "minY": 0.0, "maxX": 100.0, "maxY": 80.0}


def test_malformed_manifest_rejected():
    with pytest.raises(ManifestError):
        pixel_to_xy(0, 0, {})
    bad = make_manifest(rows=4, cols=5, cell_size_m=20.0)
    bad["grid"]["transform"]["b"] = 3.0
    with pytest.raises(ManifestError):
        pixel_to_xy(0, 0, bad)
    nan_manifest = make_manifest(rows=4, cols=5, cell_size_m=20.0)
    nan_manifest["grid"]["transform"]["c"] = float("nan")
    with pytest.raises(ManifestError):
        pixel_to_xy(0, 0, nan_manifest)
