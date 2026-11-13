# Data method

## 1. Coordinate contract

All API and fixture coordinates are **local metric** `[x_m, y_m]`.
`+x` points East and `+y` points North. Pixel indices address cell centres:
`row = 0` is the **North** edge and `col = 0` is the **West** edge.

### Region bounds, projection and coordinate transforms

The manifest stores a north-up affine transform:

```text
x = a * col + b * row + c
y = d * col + e * row + f
```

For the committed dataset: `a = 20`, `b = 0`, `c = 0`, `d = 0`, `e = -20`,
`f = 3000`. Thus the region spans 0..3000 m East and 0..3000 m North.

- `pixel_to_xy(row, col, manifest)` returns the centre of the cell.
- `xy_to_pixel(x_m, y_m, manifest)` returns `[row, col]` or `None` outside the
  grid. The northern and eastern outer edges are half-open and therefore
  outside.

The real-raster path reprojects the source data onto a local Mars
azimuthal-equidistant plane; see section 3.

## 2. Committed dataset (offline synthetic fallback)

### Source products and acquisition/checksums

The committed `data/region/` directory is a deterministic synthetic fallback
produced by `server/preprocess.py --synthetic-fallback`. It is a physically
plausible **analog** of the western Jezero Crater delta, not a measured USGS
DEM. Generation uses a fixed NumPy seed (`2026`) and the following construction:

| Component | Role |
| --- | --- |
| Regional west-to-east tilt | Delta-topography gradient toward the crater floor |
| Radial fan centered near the western edge | Delta lobe / gentle depositional rise |
| Sinuous ridge | Delta-front relief |
| Two sinuous incised channels | Distributary lows |
| Multi-scale correlated noise (18/7/2 smoothing passes) | Natural-looking roughness |
| Steep eastern logistic wall | Crater-wall analog with slopes above the default ceiling |
| Two irregular no-data holes + one-cell border ring | Unknown / unusable cells |
| Hillshade render | `imagery.webp` preview aligned to the grid |

The manifest records SHA-256 checksums for the generated artifacts and source
records for the science stops. Real USGS DEM and orthoimage GeoTIFFs can be
substituted through the pipeline in section 3.

Measured properties of the committed dataset:

| Property | Value |
| --- | --- |
| Grid | 150 x 150 cells |
| Cell size | 20 m |
| Extent | 3000 m x 3000 m (~3 km x 3 km) |
| Valid cells | 21,775 / 22,500 (96.8%) |
| Elevation range | -2603.29 m to -2459.54 m (143.75 m relief) |
| Slope p50 / p90 / p99 / max | 2.84 / 8.87 / 33.36 / 35.57 deg |
| Cells at or below 15 deg | 89.6% |

`elevation.json`, `slope.json` and `mask.json` are 2-D row-major arrays.
Unknown elevation/slope cells are `null`; unknown mask cells are `false`.
No-data is never represented as zero.

### Science stops

`data/region/science-stops.json` contains three real Perseverance sample
locations. Local `xy` values are synthetic grid positions; the latitude and
longitude in provenance are approximate contextual values, not surveyed rover
fixes.

| targetId | Sample | Site | Sol | Rock type | Local xy |
| --- | --- | --- | --- | --- | --- |
| `hazeltop` | Hazeltop (sample 12) | Wildcat Ridge, Delta Front | 509 | Sedimentary | [1300, 400] |
| `montdenier` | Montdenier (sample 2) | Artuby Ridge / Rochette | 194 | Igneous | [1100, 1200] |
| `mageik` | Mageik (sample 15) | Amalik, Delta Front | 619 | Sedimentary | [1800, 900] |

Sample metadata was taken from NASA Science, *Mars Rock Samples*
(https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/,
accessed 2026-11-13). The full citation and provenance are stored per stop and
in the manifest source records.

### Reproduction commands

Synthetic fallback (already committed; safe to regenerate):

```bash
.venv/bin/python server/preprocess.py --synthetic-fallback
```

Real USGS rasters:

```bash
.venv/bin/python server/preprocess.py \
  --dem /path/to/jezero_dem.tif \
  --ortho /path/to/jezero_ortho.tif \
  --crop-bounds MINX MINY MAXX MAXY \
  --cell-size 20 \
  --max-cells 512
```

The crop bounds are expressed in the source raster CRS. See
`server/README.md` for the full environment and test commands.

## 3. Real-raster pipeline

`prepare_region(source_paths, crop_bounds, output_dir)` supports USGS DEM and
orthoimage GeoTIFFs:

### Resolution, resampling, slope derivation and masks

1. Read the DEM and optional orthoimage with `rasterio`.
2. Clip to `crop_bounds` (source CRS), rejecting empty or inverted bounds.
3. Compute the crop centre in `EPSG:4326` and define a local Mars
   azimuthal-equidistant projection with `R = 3,389,500 m` (IAU 2015 sphere).
4. Transform the crop bounds into that local plane and choose a 10 m or 20 m
   resolution. If the resulting grid exceeds 512 x 512 cells, preprocessing
   fails with an explicit message rather than silently changing resolution.
5. Reproject the DEM with bilinear resampling onto a north-up metric grid,
   preserving source no-data as `NaN`.
6. Compute slope from **metric elevation gradients**:

   ```
   dz/dx, dz/dy = gradient(elevation, cell_size_m)
   slope_deg    = degrees(arctan(hypot(dz/dx, dz/dy)))
   ```

   Raw degree rasters are never interpreted as slope.
7. Reproject the orthoimage (or render a hillshade when no orthoimage is
   supplied), stretch to 8-bit, and save `imagery.webp`.
8. Write JSON layers, the science-stop file, SHA-256 checksums, and
   `manifest.json` last.

`datasetVersion` for the real path is derived from a digest of the processed
elevation and mask (`jezero-preprocessed-<12 hex>`). `datasetVersion` for the
synthetic path is the stable `jezero-synthetic-2026.11-v1` so fixtures remain
reproducible.

## 4. Routing method

`server/routing.py` implements 8-neighbour A* on cell centres.

- **Traversable cell:** `mask == true`, finite elevation, finite slope, outside
  every conservatively rasterised closure.
- **Edge slope** (conservative): `max(slope(cell_a), slope(cell_b))`.
- **Slope ceiling:** edges above `maxSlopeDeg` are excluded in both modes.
  Supported range is 5..30 deg; default is 15 deg.
- **Blocked polygons:** rasterised with `all_touched=True`, so any cell touched
  by a polygon edge or corner is closed.
- **No corner cutting:** a diagonal step is allowed only when both adjacent
  orthogonal cells are traversable.
- **Costs:**

  ```
  shortest:          stepDistance
  slope_penalized:   stepDistance * (1 + 4 * (edgeSlope / slopeLimit)^2)
  ```

  where `stepDistance` is `cellSizeM` for cardinal moves and
  `cellSizeM * sqrt(2)` for diagonal moves.
- **Heuristic:** Euclidean distance to the goal; admissible for both modes.
- **Output:** the unsmoothed grid path, start and goal cell centres, and total
  horizontal distance. Disconnected regions return `no_path` with `None` path
  and distance.

## 5. Mission arithmetic

For a plan, both route modes are evaluated independently. Each mode has
distinct `outbound` (base -> target) and `return` (target -> base) legs.

```
legDistance      = sum of horizontal step distances
ascentM          = sum of positive elevation changes along the path
maxSlopeDeg      = max sampled cell slope along the path
meanSlopeDeg     = distance-weighted mean of cell slopes
travelMin        = distanceM / speedMPerMin
totalRequiredMin = outboundTravel + returnTravel + dwellMin + reserveMin
marginMin        = totalBudgetMin - totalRequiredMin
```

Defaults: `speedMPerMin = 30`, `totalBudgetMin = 180`, `dwellMin = 10`,
`reserveMin = 20`, `maxSlopeDeg = 15`. A negative margin sets `over_budget`;
a disconnected leg sets `no_path` and null metrics.

Validation rejects nonpositive speed, non-finite coordinates, unsupported
schema/dataset versions, negative budgets, reserve larger than the plan budget,
invalid targets, out-of-bounds endpoints, and malformed polygons.

### Rehearsal

`remainingBudgetMin` is the time available **now**. `elapsedMin` is echoed for
context but is never subtracted again.

```
immediateReturn:     current -> base
  required = distance / speed + reserveMin

continueThenReturn:  current -> target -> base
  required = (toTarget + return) / speed + dwellMin + reserveMin
```

Both are compared against `remainingBudgetMin`. If an injected closure covers
`currentXY`, the response sets `currentPositionValid = false`, returns
`invalid_input` with `current_position_blocked`, and echoes the unchanged
`currentXY`; the rover is never teleported to a nearby free cell.

## 6. Brief method

`POST /api/brief` never reads metrics from the question text. It:

1. Looks up the stored plan by `planId`.
2. Rejects missing, expired, or stale (model/dataset mismatch) records with an
   explicit recalculation error.
3. Re-verifies the stored request input hash.
4. Builds a deterministic template answer from the stored route metrics and
   the target science-stop record.
5. Returns `mode: "template"`, `metricRefs`, and `sourceIds` citations.

The in-memory store is bounded (default 256 entries) and plans expire after
30 minutes by default. Both limits are configurable with
`MARS_RETURN_PLAN_STORE_MAX` and `MARS_RETURN_PLAN_TTL_SECONDS`.

## 7. Artifacts, uncertainty and use/attribution terms

- **Artifacts:** `data/region/` contains `elevation.json`, `slope.json`,
  `mask.json`, `imagery.webp`, `science-stops.json`, and `manifest.json`. The
  manifest records bounds, transform, projection, Mars datum, sources,
  `datasetVersion`, parameter bounds, and SHA-256 checksums.
- **Uncertainty:** the committed terrain is a synthetic analog. All measured
  distances and slopes describe that analog, not actual Jezero topography. The
  real-raster path is implemented but has not been exercised against downloaded
  USGS data in this environment.
- **Attribution:** science-stop metadata comes from NASA Science, *Mars Rock
  Samples* (https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/,
  accessed 2026-11-13). The full citation and provenance are stored per stop
  and in the manifest source records.
- **Use:** derived routes are planning estimates, not certified astronaut
  navigation or safety guidance.

## 8. Limitations

- The committed terrain is synthetic. Real USGS rasters can be substituted,
  but the committed measured numbers do not describe actual Jezero topography.
- Traversal is geometric only: no energy, thermal, solar, communication,
  rover-kinematics, or time-of-day model is applied.
- Slope is a local cell-gradient estimate; steep features smaller than a cell
  may be under-represented. No-data creates a conservative one-cell halo
  because gradients touching `null` are also `null`.
- Paths are unsmoothed grid paths. Ascent and distance therefore include
  grid-scale zig-zag and should be treated as planning estimates.
- The local Mars tangent plane is appropriate for a few-kilometre region, not
  for global navigation.
- Briefs are deterministic template explanations, not an LLM. The `model` mode
  is reserved by the contract but not implemented.
- Plan state is process-local and is lost on restart. There is no database,
  authentication, or rate limiting.
- No frontend application code is implemented; `web/` contains only placeholder
  READMEs inherited from `origin/main`.
