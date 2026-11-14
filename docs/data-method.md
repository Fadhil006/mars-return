# Data processing record — A1

## Source products and acquisition

The prepared 3 km crop uses two real, matched USGS/PDS CTX products. Both original GeoTIFFs were downloaded on 2026-11-12 from the URLs in [`data/sources/`](../data/sources/). Their SHA-256 hashes, product descriptions and attribution/terms notes are recorded there and embedded as source records in the generated manifest. Raw downloads are intentionally ignored by Git.

| Layer | Product | Native pixel spacing | Observed format / units |
|---|---|---:|---|
| Elevation | M20 Jezero Crater CTX DEM mosaic | 20 m | 1-band Float32 GeoTIFF; elevation meters; nodata `-3.4028234663852886e+38` |
| Imagery | M20 Jezero Crater CTX ortho mosaic | 5 m | 1-band UInt8 GeoTIFF; grayscale image |

The DEM is 4,456 × 5,067 pixels, with projected bounds 4,328,999.999…–4,418,119.999… m east and 1,042,080.000…–1,143,420.000… m north. Its CRS is the Jezero equirectangular projection on the Mars 2000 sphere (radius 3,396,190 m), standard parallel 18.4663°, central meridian 0°. The imagery is nominally 5 m and has a separately named but numerically matched equirectangular Mars CRS; Rasterio reprojects it onto the DEM analysis grid. It is grayscale, not color imagery.

## Region, projection and coordinate transforms

The crop is 4,353,000–4,356,000 m projected east and 1,091,800–1,094,800 m north (3,000 m square; 150 × 150 cells at 20 m). Its discovery reference is approximately 18.4446° N, 77.4509° E, transformed with the product's sphere and standard parallel. This is a geographic neighborhood, not an independently registered rover landing-position fix. The raster CRS radius (3,396,190 m) takes precedence over the catalogue's differing radius metadata; full source WKT is preserved.

Manifest `originXY` is the crop's southwest corner `[west, south]`, expressed as local `[0,0]` meters. Column increases east; row 0 is north. Each pixel coordinate refers to its cell center:

```text
x = west + (col + 0.5) * cellSizeM
y = south + (height - row - 0.5) * cellSizeM
```

`xy_to_pixel` accepts west and south edges, excludes east and north edges, and rejects all other out-of-bounds coordinates. It returns `[row, col]`; `pixel_to_xy` returns `[x, y]`. Projection uses the source Mars datum; there is no Earth CRS or Earth-distance conversion.

## Resolution, slope and masks

The analysis grid stays at the DEM's native 20 m spacing; requests finer or coarser than the DEM are rejected rather than presented as evidence. For shifted crop alignment, DEM values use bilinear reprojection but also require a fully valid bilinear support footprint; nodata contributors are kept unknown instead of renormalized into terrain values. Imagery is average-resampled, its valid-data coverage is recorded, and invalid pixels are transparent in the RGBA preview. The preview keeps the source's finer pixels (5 m for the CTX orthoimage, 600 × 600) for display only; the mask and every calculation stay on the 20 m grid. Elevation and derived slope are JSON row-major nested arrays. Non-finite or nodata values serialize as `null`. Slope is `atan(hypot(dz/dx, dz/dy))` in degrees from centered metric finite differences; a full valid 3 × 3 elevation neighborhood is required. The mask is nested JSON booleans only: `true` means elevation, slope and imagery are present; `false` means a required layer is missing. No obstacle exclusions are hand-authored. SHA-256 checksums for all four exported layers are in `manifest.json`.

The imagery preview is a contrast-stretched grayscale WebP with transparent invalid coverage. Elevation and imagery are from orbital CTX products, not independent sensors. DEM pixel spacing is not a statement of vertical accuracy. No source acquisition date or quantitative accuracy was established from the supplied product landing page/file metadata; neither is invented here. The manifest stores full source CRS WKT and affine transforms for both rasters, the Mars datum WKT derived from the DEM CRS, crop bounds and projected offset, and the analysis pixel-to-local transform. Datum metadata is derived from each DEM's actual CRS; source identifiers/records are populated only for the two known product filenames after checksum verification. The DEM catalogue publication date is 2021-10-14, not the acquisition date.

## Reproduction

The complete reproducible demo command, including verified acquisition and versioning of scientific context/waypoint metadata, is:

```sh
.venv/bin/python -m scripts.prepare_demo
```

For raster preparation alone, after obtaining the verified inputs, run from the repository root:

```sh
.venv/bin/python -m server.preprocess \
  --elevation data/raw/M20_JezeroCrater_CTXDEM_20m.tif \
  --imagery data/raw/M20_JezeroCrater_CTXortho_mosaic_5m.tif \
  --bounds 4353000 1091800 4356000 1094800 \
  --output-dir data/region --cell-size-m 20
```

Crop bounds are in the DEM's native projected meters and supplied in west, south, east, north order. The run produces 150 × 150 cells; 22,500 have elevation coverage and 21,904 have a complete slope neighborhood. Imagery validity and combined true-mask cell counts are recorded separately. The crop has elevations from −2,616.9055 m to −2,475.135 m (prepared-array mean −2,570.5251 m in the source units). Raster preparation alone versions layers and crop parameters; `scripts.prepare_demo` additionally versions the destination checksum, source records, and scenario metadata. Use the complete command before serving the documented scenario.

## Limitations and use

This is an orbital planning surface, not a certified hazard map. CTX-derived topography cannot resolve all small rocks, loose material, local slopes, rover/crew-scale hazards, or current conditions. The baseline mask means only that required raster values exist; it does not certify traversability. Slope estimation near gaps deliberately creates additional unknown cells. Product terms and attribution details available from the source pages are summarized, not legal advice; retain source citations with any redistribution.
