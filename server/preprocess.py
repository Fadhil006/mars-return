"""Prepare a bounded local metric region from georeferenced rasters."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import from_bounds


def prepare_region(source_paths, crop_bounds, output_dir, cell_size_m=20):
    """Write aligned JSON grids and imagery for [west,south,east,north] bounds.

    Bounds are in the elevation raster's native projected metric CRS. The
    returned local frame has its southwest corner at [0, 0].
    """
    if not math.isfinite(cell_size_m) or cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive")
    west, south, east, north = map(float, crop_bounds)
    if not all(map(math.isfinite, (west, south, east, north))) or not west < east or not south < north:
        raise ValueError("crop_bounds must be finite west,south,east,north")
    width, height = round((east - west) / cell_size_m), round((north - south) / cell_size_m)
    if width < 3 or height < 3 or width > 512 or height > 512:
        raise ValueError("crop must produce a 3..512 cell grid in each dimension")
    east, north = west + width * cell_size_m, south + height * cell_size_m
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with rasterio.open(source_paths["elevation"]) as dem:
        if not dem.crs or not dem.crs.is_projected:
            raise ValueError("elevation source must use a projected metric CRS")
        if dem.crs.linear_units not in ("metre", "meter"):
            raise ValueError("elevation source CRS units must be meters")
        if not all(math.isfinite(value) for value in dem.transform):
            raise ValueError("elevation source transform must be finite")
        if dem.transform.a <= 0 or dem.transform.e >= 0 or dem.transform.b or dem.transform.d or not math.isclose(
                abs(dem.transform.a), abs(dem.transform.e), rel_tol=1e-5):
            raise ValueError("rotated or non-square elevation pixels are unsupported")
        source_resolution = [abs(dem.transform.a), abs(dem.transform.e)]
        if not math.isclose(cell_size_m, max(source_resolution), rel_tol=1e-6):
            raise ValueError("analysis cell size must match DEM pixel spacing; up/downsampling is unsupported")
        if west < dem.bounds.left or east > dem.bounds.right or south < dem.bounds.bottom or north > dem.bounds.top:
            raise ValueError("crop_bounds must be covered by the elevation raster")
        requested = from_bounds(west, south, east, north, dem.transform)
        col0 = max(0, math.floor(requested.col_off))
        row0 = max(0, math.floor(requested.row_off))
        col1 = min(dem.width, math.ceil(requested.col_off + requested.width))
        row1 = min(dem.height, math.ceil(requested.row_off + requested.height))
        window = rasterio.windows.Window(col0, row0, col1 - col0, row1 - row0)
        data = dem.read(1, window=window, masked=True).astype("float64")
        transform = dem.window_transform(window)
        target_transform = from_origin(west, north, cell_size_m, cell_size_m)
        elevation = np.full((height, width), np.nan, dtype="float64")
        reproject(data.filled(np.nan), elevation, src_transform=transform, src_crs=dem.crs,
                  dst_transform=target_transform, dst_crs=dem.crs, src_nodata=np.nan,
                  dst_nodata=np.nan, resampling=Resampling.bilinear)
        # Require full valid interpolation support; a nodata neighbor may not
        # be silently renormalized into a plausible-looking elevation.
        support = np.zeros((height, width), dtype="float32")
        reproject((~np.ma.getmaskarray(data)).astype("float32"), support,
                  src_transform=transform, src_crs=dem.crs,
                  dst_transform=target_transform, dst_crs=dem.crs,
                  resampling=Resampling.bilinear)
        elevation[support < 1 - 1e-6] = np.nan
        crs_wkt = dem.crs.to_wkt()
        source_nodata = dem.nodata
        dem_crs_wkt = crs_wkt
        dem_transform = list(dem.transform)[:6]
        dem_bounds = list(dem.bounds)
        dem_datum_wkt = dem.crs.geodetic_crs.to_wkt()

    elevation_valid = np.isfinite(elevation)
    # A centered 3x3 neighborhood is required, avoiding derivative estimates
    # across gaps or the padded border.
    neighborhood = elevation_valid.copy()
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            shifted = np.zeros_like(elevation_valid)
            shifted[max(0, dr):height + min(0, dr), max(0, dc):width + min(0, dc)] = \
                elevation_valid[max(0, -dr):height - max(0, dr), max(0, -dc):width - max(0, dc)]
            neighborhood &= shifted
    safe = np.where(elevation_valid, elevation, 0.0)
    dz_dy, dz_dx = np.gradient(safe, cell_size_m, cell_size_m)
    slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
    valid = elevation_valid & neighborhood
    elevation[~np.isfinite(elevation)] = np.nan
    slope[~valid] = np.nan

    with rasterio.open(source_paths["imagery"]) as image:
        if not image.crs or not image.crs.is_projected:
            raise ValueError("imagery must use a projected CRS")
        if not all(math.isfinite(value) for value in image.transform):
            raise ValueError("imagery source transform must be finite")
        channels = min(image.count, 3)
        imagery_resolution = [abs(image.transform.a), abs(image.transform.e)]
        imagery_crs_wkt = image.crs.to_wkt()
        imagery_transform = list(image.transform)[:6]
        image_bounds = transform_bounds(rasterio.crs.CRS.from_wkt(crs_wkt), image.crs,
                                        west, south, east, north)
        requested = from_bounds(*image_bounds, transform=image.transform)
        col0, row0 = max(0, math.floor(requested.col_off)), max(0, math.floor(requested.row_off))
        col1 = min(image.width, math.ceil(requested.col_off + requested.width))
        row1 = min(image.height, math.ceil(requested.row_off + requested.height))
        if col1 <= col0 or row1 <= row0:
            image_valid = np.zeros((height, width), dtype=bool)
            image_transform = image.transform
            image_mask = np.zeros((1, 1), dtype="uint8")
        else:
            image_window = rasterio.windows.Window(col0, row0, col1 - col0, row1 - row0)
            image_transform = image.window_transform(image_window)
            image_mask = image.dataset_mask(window=image_window)
            image_coverage = np.zeros((height, width), dtype="float32")
            reproject(image_mask.astype("float32"), image_coverage,
                      src_transform=image_transform, src_crs=image.crs,
                      dst_transform=target_transform, dst_crs=rasterio.crs.CRS.from_wkt(crs_wkt),
                      resampling=Resampling.average)
            image_valid = image_coverage >= 254.999
        rgb = np.zeros((height, width, 3), dtype="uint8")
        for band in range(channels):
            band_data = np.zeros((height, width), dtype="float32")
            reproject(rasterio.band(image, band + 1), band_data,
                      src_transform=image.transform, src_crs=image.crs,
                      dst_transform=target_transform, dst_crs=rasterio.crs.CRS.from_wkt(crs_wkt),
                      dst_nodata=0, resampling=Resampling.average)
            low, high = np.percentile(band_data[band_data > 0], [1, 99]) if np.any(band_data > 0) else (0, 1)
            rgb[..., band] = np.clip((band_data - low) * 255 / max(high - low, 1), 0, 255)
        if channels == 1:
            rgb[..., 1:] = rgb[..., :1]
    Image.fromarray(np.dstack((rgb, image_valid.astype("uint8") * 255))).save(
        out / "imagery.webp", quality=85
    )

    def write_grid(name, values):
        rows = [[None if v is None or (not isinstance(v, (bool, np.bool_)) and not math.isfinite(float(v)))
                 else bool(v) if isinstance(v, (bool, np.bool_)) else float(v) for v in row]
                for row in values]
        (out / f"{name}.json").write_text(json.dumps(rows, separators=(",", ":")) + "\n")

    write_grid("elevation", elevation)
    write_grid("slope", slope)
    mask = valid & image_valid
    write_grid("mask", mask)
    version_hash = hashlib.sha256()
    version_hash.update(elevation.tobytes())
    version_hash.update(slope.tobytes())
    version_hash.update(rgb.tobytes())
    version_hash.update(image_valid.tobytes())
    version_hash.update(valid.tobytes())
    version_hash.update(f"{crop_bounds}:{cell_size_m}".encode())
    version_hash.update(crs_wkt.encode())
    version_hash.update(imagery_crs_wkt.encode())
    version_hash.update(json.dumps([dem_transform, imagery_transform]).encode())
    dataset_version = version_hash.hexdigest()[:16]
    basename_ids = {
        "M20_JezeroCrater_CTXDEM_20m.tif": "ctx-dem.json",
        "M20_JezeroCrater_CTXortho_mosaic_5m.tif": "ctx-ortho.json",
    }
    source_records = []
    source_dir = Path(__file__).resolve().parents[1] / "data" / "sources"
    for source_path in source_paths.values():
        record_name = basename_ids.get(Path(source_path).name)
        record_path = source_dir / record_name if record_name else None
        if record_path and record_path.is_file():
            record = json.loads(record_path.read_text())
            with Path(source_path).open("rb") as source:
                if hashlib.file_digest(source, "sha256").hexdigest() != record["sha256"]:
                    raise ValueError("Known source filename does not match its registered checksum")
            source_records.append(record)
    layer_checksums = {
        filename: hashlib.sha256((out / filename).read_bytes()).hexdigest()
        for filename in ("elevation.json", "slope.json", "mask.json", "imagery.webp")
    }
    manifest = {
        "datasetVersion": dataset_version, "width": width, "height": height,
        "cellSizeM": cell_size_m, "originXY": [0, 0],
        "sourceBoundsXY": [west, south, east, north], "projectedOffsetXY": [west, south],
        "pixelToLocalTransform": [cell_size_m, 0, 0, 0, -cell_size_m, height * cell_size_m],
        "analysisCRS": crs_wkt, "sourceDatumWKT": dem_datum_wkt,
        "sourceElevationCRS": dem_crs_wkt, "sourceElevationTransform": dem_transform,
        "sourceElevationBoundsXY": dem_bounds, "sourceElevationResolutionM": source_resolution,
        "sourceImageryCRS": imagery_crs_wkt, "sourceImageryTransform": imagery_transform,
        "sourceImageryResolutionM": imagery_resolution,
        "sourceNoData": source_nodata if source_nodata is None or math.isfinite(source_nodata) else None,
        "sourceIds": [record["sourceId"] for record in source_records], "sources": source_records,
        "layers": {"elevation": "elevation.json", "slope": "slope.json",
                   "mask": "mask.json", "imagery": "imagery.webp"},
        "coverage": {"elevationValidCells": int(elevation_valid.sum()), "slopeValidCells": int(valid.sum()),
                     "imageryValidCells": int(image_valid.sum()), "traversableCells": int(mask.sum()),
                     "totalCells": width * height},
        "layerInfo": {
            "elevation": {"resolutionM": cell_size_m, "sourcePixelSpacingM": source_resolution,
                          "validCells": int(elevation_valid.sum()), "units": "m"},
            "slope": {"resolutionM": cell_size_m, "validCells": int(valid.sum()), "units": "degrees"},
            "mask": {"resolutionM": cell_size_m, "validCells": int(mask.sum()), "units": "boolean"},
            "imagery": {"resolutionM": cell_size_m, "sourcePixelSpacingM": imagery_resolution,
                        "channels": channels, "validCells": int(image_valid.sum()),
                        "format": "grayscale preview" if channels == 1 else "RGB preview"},
        },
        "checksums": layer_checksums,
        "slopeMethod": "Centered finite differences; degrees; null unless full 3x3 elevation neighborhood exists.",
        "maskMeaning": "true means elevation, slope, and imagery are valid; false means at least one is missing.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elevation", required=True, help="Projected DEM GeoTIFF")
    parser.add_argument("--imagery", required=True, help="Matched imagery GeoTIFF")
    parser.add_argument("--bounds", required=True, nargs=4, type=float,
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
                        help="Crop bounds in DEM projected CRS meters")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cell-size-m", type=float, default=20)
    args = parser.parse_args()
    print(json.dumps(prepare_region({"elevation": args.elevation, "imagery": args.imagery},
                                    args.bounds, args.output_dir, args.cell_size_m), indent=2))


if __name__ == "__main__":
    main()
