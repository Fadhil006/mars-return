import pytest

from server.coordinates import pixel_to_xy, xy_to_pixel


MANIFEST = {"width": 3, "height": 2, "cellSizeM": 10, "originXY": [100, 200]}


def test_cell_centers_round_trip_and_row_direction():
    assert pixel_to_xy(0, 0, MANIFEST) == [105, 215]
    assert pixel_to_xy(1, 2, MANIFEST) == [125, 205]
    for row in range(2):
        for col in range(3):
            assert xy_to_pixel(*pixel_to_xy(row, col, MANIFEST), MANIFEST) == [row, col]


def test_outer_boundaries_include_west_south_not_east_north():
    assert xy_to_pixel(100, 200, MANIFEST) == [1, 0]
    for point in ((130, 205), (105, 220), (99.99, 205), (105, 199.99)):
        with pytest.raises(ValueError):
            xy_to_pixel(*point, MANIFEST)


@pytest.mark.parametrize("pixel", [(-1, 0), (0, -1), (2, 0), (0, 3)])
def test_pixel_out_of_bounds(pixel):
    with pytest.raises(ValueError):
        pixel_to_xy(*pixel, MANIFEST)
