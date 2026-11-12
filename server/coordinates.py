"""Conversions between grid pixels and the region's local metric frame."""


def pixel_to_xy(row, col, manifest):
    """Return the center [x, y] of a grid cell; row 0 is north."""
    width, height = manifest["width"], manifest["height"]
    if not (0 <= row < height and 0 <= col < width):
        raise ValueError("pixel is outside region")
    cell = manifest["cellSizeM"]
    west, south = manifest["originXY"]
    return [west + (col + 0.5) * cell, south + (height - row - 0.5) * cell]


def xy_to_pixel(x, y, manifest):
    """Return [row, col]; west/south included, east/north excluded."""
    width, height = manifest["width"], manifest["height"]
    cell = manifest["cellSizeM"]
    west, south = manifest["originXY"]
    col, northward_row = (x - west) / cell, (y - south) / cell
    if not (0 <= col < width and 0 <= northward_row < height):
        raise ValueError("coordinate is outside region")
    return [height - 1 - int(northward_row), int(col)]
