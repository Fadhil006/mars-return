# Round 1: planetary geologist / data scientist (`planetary-geologist`)

## 1. Three-minute judge look: what's weak

- **Science is a pin plus a table.** All five sites share one identical `scientificQuestion` ("What would a crew observe and collect here that the rover's cores and instruments could not?"). The text asks the question but never answers it. A geologist judge will see this as filler straight away.
- **"Multiple NASA missions" is thin.** The entry uses MRO/CTX (DEM and ortho), Mars 2020 waypoints and sample inventory, and MSL RAD, which was measured at *Gale*. That is two missions at Jezero. NeuroNexus claims 76 sources and Protikriti about 25.
- **Imagery looks soft.** On a 3 km × 3 km crop, 5 m CTX reads as orange noise at desktop zoom. On the map, Brac, Issole and Rochette crowd together and one pin has no label. Judges compare this with competitors showing 25 cm HiRISE.
- **Roubion is a destination, but it yielded an *atmospheric* sample** (the first coring attempt failed). Choosing it as a science stop for a crew has no geological reason behind it.
- **Nothing connects orbital science to route choice.** No layer changes which stop you pick or which way you walk. The challenge asks for "science along the way". This entry gives science only *at the end of* the way.

## 2. Competitor scan (2026, same challenge, found via GitHub search; READMEs grepped)

At least 25 public repos. The data-heavy ones:
- **Magurin/marswalk-planner** (live at marswalk-planner-one.vercel.app): 1 m HiRISE slope, **Edwards & Buz THEMIS thermal inertia as "loose ground"**, Santee metabolic model, MEDA, and an **auto planner that fits the most science targets into one EVA (exact search)**. "Science per EVA" orienteering is therefore **already taken**.
- **hananshehzad06-ctrl/jezero-traverse-map** and **vivi-codes-at12/marswalk**: the **SIM 3464 geologic units** and THEMIS IR from the same zip.
- **GitTanish/ares-walk**: CRISM D2300 and THEMIS hooks, though they are "modeled unless rasters supplied".
- **kmmohaimenulhaque-code/MartianMap-NeuroNexus**: 76 sources, SIM 3292, MGCM dust, and a "science" route objective.

**Conclusion:** THEMIS TI, the SIM 3464 geology and a "science route" are now **table stakes**. None of the READMEs I checked does either of these:
- (a) score how far the **orbital prediction agrees with the rover's ground truth** at each site;
- (b) tie science to a **return margin under a mid-route event**.

Those two are the openings.

## 3. Data I verified (fetched today, 15 Nov 2026)

The crop is lon 77.424–77.478°E, lat 18.419–18.470°N (computed from the manifest).

| Layer | Endpoint / file | Status | Size | Licence | Value in our 3 km box |
|---|---|---|---|---|---|
| **HiRISE 25 cm controlled Jezero ortho** (MRO) | `https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0/default/default028mm/{z}/{row}/{col}.png` (geographic, 20 levels; z12 tile 1628/5858 returned a 256² PNG) | **200** | ~55 KB/tile | NASA/JPL/UArizona, public | 25 cm imagery behind the routes |
| CTX 6 m controlled ortho | `.../JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0/...` | 200 | — | public | same as now |
| THEMIS Night/Day IR 100 m controlled (Odyssey) | `.../THEMIS_NightIR_ControlledMosaics_100m_v2_oct2018/...` (levels 0–9) | 200 | — | public | qualitative only |
| Perseverance traverse | `trek.nasa.gov/mars/trekarcgis/rest/services/Perseverance_Traverse_Path/MapServer/WMTS` | 200 | — | public | — |
| Trek HiRISE/CTX **DEM** WMTS, CRISM `frt_07_*` WMTS, `Hydrous_Mineral_Detections_CRISM_clon0` | — | **404** | — | — | DEMs must be downloaded, not tiled |
| Trek catalogue search | `trek.nasa.gov/mars/TrekServices/ws/index/eq/searchItems?...&q=*` | 200 | 2038 items | — | layer discovery |
| **CRISM dominant-mineral map** (Parente, Saranathan, Itoh, Tarnas, Seelos, Mustard 2021) | zenodo.org/records/5575824 → `jezeroFinal.tif` | 200 | **1.4 MB**, 36 m, RGB class codes | **CC-BY-4.0** | 68% of the box classified (olivine, high-Ca pyroxene, olivine+smectite) |
| **THEMIS thermal inertia, Jezero** (Edwards & Buz 2021) | zenodo.org/records/4931348 → `Jezero_Thermal_Inertia_v1.tiff` | 200 | **1.7 MB**, 100 m | **CC-BY-4.0** | box TI 5–95th percentile = 176–272 SI; sites 206–252 |
| **Geologic map SIM 3464** (Sun & Stack 2020, 1:75k) | `https://pubs.usgs.gov/sim/3464/sim3464_database.zip` | 200 | **~349 MB** (file geodatabase, MTM 77.5°E; ships HRSC, THEMIS and CTX rasters) | **public domain** | readme warns of a **100–200 m offset** from the controlled CTX mosaic |
| Stack et al. 2020 photogeologic map (1:5k, the right scale for 3 km) | doi:10.1007/s11214-020-00739-x, supplementary TIF | no shapefile found | — | Springer OA | better scale, raster only |
| **Sample Dossier Initial Reports** (per-core context and results) | `pds.nasa.gov/data/pds4/releases/geo/mars2020_sample_dossier-20260213/` (initial_reports volumes 1–5) | readme 200; PDF path not resolved | PDFs | PDS public | answers the "why here" question for each site |
| Rover PLACES localizations | pds.nasa.gov `mars2020_rover_places-20251204` (sols 0–1619) | listed | small CSV | PDS public | geodetic positions with provenance |
| MEDA derived | pds.nasa.gov `mars2020_meda-20260811` | listed | per-sol CSV | PDS public | wind dead after sol 315; historical only |

**Result I computed: CRISM class at each stop, 3×3 pixels at 36 m**

| Stop | CRISM class (pixel count) |
|---|---|
| Brac (Séítah) | **olivine high-confidence 6/9, medium 3/9** |
| Issole (Séítah) | olivine and olivine+smectite 5/9, none 4/9 |
| Rochette (Máaz) | mostly none, plus olivine and high-Ca pyroxene traces |
| Sid | none |
| Roubion | none |

The rover's in-situ result agrees with Brac: Liu et al. 2022, *Science* 377:1513, describes the Brac/Bastide outcrop as an **olivine cumulate**. That gives a real, citable **orbit → ground check**, and it is the headline of proposal A.

## 4. Proposals (ranked)

**A. "Orbit said / Rover found" card for each site. NOVEL.**
- **What:** Each stop shows three rows:
  - CRISM class and confidence, sampled server-side from the Parente map;
  - the SIM 3464 unit;
  - what Perseverance actually cored: rock type from the inventory, plus a one-line citation from the Initial Reports or Liu 2022 / Farley 2022.
- **Verdict per site:** *confirmed* (Brac: olivine cumulate), *orbit silent* (Sid, Roubion: dust cover or below detection) or *partial*. This tells a crew where orbital maps can be trusted and where a human visit adds information. It is the real answer to the site's question, which stays empty today.
- **Wins:** Validity (ground-truthed), Relevance (science along the way), Creativity.
- **Data:** zenodo 5575824 (CC-BY), SIM 3464, PDS sample dossier.
- **Effort:** S–M. One preprocess script; values go into `science-stops.json` with `sourceIds`.

**B. Science triage inside the rehearsal. NOVEL. This is the unique differentiator.**
- **What:** When the event fires mid-route, the server ranks the remaining stops by **science retained per minute of return margin consumed**, so the crew sees "drop Issole, keep Brac: −6% science, +22 min margin". The comparison is shown as a two-line Pareto (margin against science value) for "return now / continue / continue minus one stop".
- **Why it's unique:** Magurin already maximises science per EVA, but only in a static plan. Nobody else does it **under a contingency**.
- **Wins:** Impact and Creativity.
- **Rules kept:** `mission.py` computes it; the assistant narrates through `trusted_context`.
- **Effort:** M. It reuses the rehearsal and stress arithmetic.

**C. Transparent science-value score along the corridor, not only at the end.**
- **What:** Score each route with three terms:
  - distinct CRISM classes within 50 m of the path;
  - SIM 3464 unit contacts crossed (contacts are where geologists stop);
  - a bonus for stops whose orbital class the rover has *not* sampled.
- **Display:** "science per minute" for both objectives. Every term is clickable down to the pixel and its citation.
- **Labelling:** a hypothetical weighting, with the weights visible. It must never be called "science value" without the word "model".
- **Wins:** Relevance and Validity.
- **Effort:** M.

**D. HiRISE 25 cm basemap from Trek WMTS.**
- **What:** At the 3 km scale, HiRISE makes the product look professional rather than amateur. It also lets judges see why the lower-slope route bends: around the Séítah ridges.
- **How:** Cache the tiles covering the box during `prepare_demo`. Keep them out of Git and serve them locally, so the demo never depends on Trek being up and still meets the "no fallback" rule.
- **Wins:** Presentation. Adds a second MRO instrument.
- **Effort:** S. Geographic tiling; the tile math is trivial and verified above.

**E. THEMIS thermal inertia as a speed modifier with a visible label.**
- **What:** Low TI (<200, loose fines) reduces the walking speed, and the route explains "slowed here: TI 180, likely loose sand" (Edwards & Buz 2021, CC-BY, 1.7 MB).
- **Why:** Table stakes, but it adds Mars Odyssey as a mission.
- **Wins:** Relevance and Validity.
- **Effort:** S.
- **Caveat:** at 100 m the box is only 30×30 pixels. Say so.

**F. Replace Roubion and fix the site text.**
- **What:** Drop Roubion (an atmospheric sample) as a geological destination, or label it honestly. Write per-site questions from the Initial Reports.
- **AI use (honest and visible):** an LLM drafts each question and two-sentence context *offline* from the report PDF text. A human approves it, and it is stored with the PDF citation and a page number. A test asserts every claim carries a `sourceId`.
- **Wins:** Validity and Presentation.
- **Effort:** S.

**G. Mission-count line in the header and report.**
- **What:** Show "MGS · Odyssey · MRO (CTX, HiRISE, CRISM) · Mars 2020 · MSL". Each badge opens its evidence card.
- **Wins:** Relevance, and an easy point.
- **Effort:** S, once D and E land.

## 5. Trap I expect the panel to push

**"Use AI vision to detect hazards, rocks or minerals from imagery."** Avoid it, for four reasons:
- 25 cm HiRISE cannot resolve the rocks that matter to a walker (under about 0.75 m). A 5 m CTX tile cannot show minerals.
- There is no labelled Jezero ground truth to validate against within days.
- Whatever it produced would be an unvalidated derived map presented next to real ones. That is exactly the "synthetic shown as real" failure, and a geologist judge will ask "what's your precision/recall?"

The honest AI win is the opposite: **the AI reads and cites real mission documents (B and F), and the server verifies the numbers.**

A smaller trap: **"live MEDA weather"**. The MEDA wind sensor died around sol 315 (2022), and the data are historical point measurements from one rover. Present them as context only.

## Sources

- Trek WMTS and catalogue: endpoints listed above (HTTP status verified with curl).
- CRISM map: https://zenodo.org/records/5575824
- THEMIS thermal inertia: https://zenodo.org/records/4931348
- SIM 3464: https://pubs.usgs.gov/publication/sim3464 and https://pubs.usgs.gov/sim/3464/sim3464_readme.txt
- Stack et al. 2020: https://dspace.mit.edu/handle/1721.1/131851
- Liu et al. 2022 (olivine cumulate): https://carnegiescience.edu/olivine-cumulate-outcrop-floor-jezero-crater-mars
- Sample dossier: https://pds.nasa.gov/data/pds4/releases/geo/mars2020_sample_dossier-20260213/readme.txt
- Rover PLACES: https://pds-geosciences.wustl.edu/missions/mars2020/places.htm
- MEDA: https://pds.nasa.gov/data/pds4/releases/atmos/mars2020_meda-20260811/readme.txt and https://arxiv.org/pdf/2410.19132 (wind sensor ends at sol 315)
- CRISM retirement, April 2023: https://www.jpl.nasa.gov/news/nasa-retires-mineral-mapping-instrument-on-mars-orbiter/
- Science-aware multi-objective traverse planning: https://arxiv.org/html/2406.16376v1 and https://digitalcommons.mtu.edu/michigantech-p2/2763
- Competitors:
  - https://github.com/Magurin/marswalk-planner
  - https://github.com/hananshehzad06-ctrl/jezero-traverse-map
  - https://github.com/vivi-codes-at12/marswalk
  - https://github.com/GitTanish/ares-walk
  - https://github.com/kmmohaimenulhaque-code/MartianMap-NeuroNexus
