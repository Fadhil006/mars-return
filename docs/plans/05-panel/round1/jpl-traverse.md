# jpl-traverse: JPL surface-ops review of MARS RETURN route planning

Reviewer persona: JPL strategic/tactical traverse planner (M2020/MSL). Scope: route planning, hazard model, uncertainty, rehearsal.

## 1. Three-minute judge look (brutal)

**What is genuinely good.** `return_field` (a cost-to-go map from the base) has the right structure. It is the same object JPL's landing-site traversability tool computes, a Dijkstra cost map that is queried from many start points (Ono et al.), and the same idea as MIT SEXTANT's "walk back from any point on the traverse". The rover-vs-CTX elevation check (125 localizations, σ 1.98 m) is real validation that competitors will not have. Keep both.

**What a domain judge sees as a toy (all checked in the repo or the live data):**
1. **The slope constraint almost never binds.** I measured the slope layer: median 2.26°, p99 7.9°, and **only 0.12% of cells exceed 15° (0.42% exceed 10°)**. The 15° ceiling and the "lower slope" objective are mostly decoration. The two routes to Sid differ by 33 m over 2.2 km (1.5%), and every site passes 8/8 closures. A stress test that always passes is a non-result in a demo.
2. **Slope is measured at the wrong scale.** `preprocess.py` uses 3×3 central differences, a 40 m baseline, on a CTX stereo DEM. Kirk et al. (2020/2021) found stereo DTM effective horizontal resolution is about 10–20 image pixels, so for CTX that is roughly 60–120 m. A 15° limit is a footstep-scale (1–5 m) limit. Applying it to 40–120 m slopes systematically understates hazards, and the UI does not show how large that gap is.
3. **Time ignores terrain.** `mission.py`: `travelMin = distanceM / speedMPerMin`. A 15° climb costs the same minutes as flat ground, and `ascentM` is computed but used for nothing. The routing cost `length*(1+4(s/smax)^2)` has no units, so "lower slope" is not "faster" or "cheaper" by any physical measure. Real planners minimize **time** (Ono et al.: pixel cost = 1/driving speed, with speed taken from terrain class, CFA rock abundance and slope).
4. **Edges are symmetric and slope has no sign.** Uphill and downhill cost the same, so the "return envelope" assumes the trip home equals the trip out. For walking that is false: Tobler-type and suited-locomotion models are asymmetric.
5. **No hazard layer other than slope.** There is no terrain class, no rock abundance and no sand. Brac and Issole are in **South Séítah**, the ripple- and sand-covered unit. The JPL mobility model treats ripple fields as untraversable at any slope and drops speed at CFA >7% (80→60 m/hr) and avoids >15%. This planner would cheerfully send a crew in by the shortest line.
6. **False precision.** "+76.34 min" margins are given to a hundredth of a minute from a constant-speed assumption. There is no distribution, no percentile, no path-inflation factor. Ono et al. report percentile distance and time from CDFs, and they inflate grid routes by +30% from Curiosity's real odometry versus planned routes (and take −5.4% for 8-connected grid overestimate).
7. **Staircase 8-connected paths** on a 20 m grid look amateur in 3D next to Protikriti's Cesium.

**Why a competitor scores higher on Validity/Presentation:** Protikriti shows ~25 datasets plus hazards plus a walk-home card. A judge cannot tell their A* is just as naive. Yours looks *less* layered because slope is the only hazard.

## 2. I ran one experiment for you (real Mars ground truth)

`data/region/rover-traverse.json` has odometry. I routed the planner (shortest, 15°) between consecutive Perseverance localizations: 27 drives of ≥60 m, ≤2 sols apart, staying inside the crop. Script: `scratchpad/jpl/odo.py`.

| | total |
|---|---:|
| Rover odometry | 4,716 m |
| Planner route | 4,659 m |
| Straight line | 4,432 m |

Odometry/planner per drive: **median 1.01, p10 0.88, p90 1.29, max 1.74.** Every drive was routable. This means:

- In aggregate the planner is unbiased on this floor, which is a real, citable validation.
- Per excursion the error is roughly −12% to +29% (p10–p90). That should be the uncertainty band on every distance and margin.
- Planner route over straight line is only 1.05, so the terrain model barely steers at all (see point 1).

Caveats: odometry includes slip and turn-in-place, and rover paths are ENav/AutoNav choices, not walking paths. Present the result as "path-length uncertainty calibrated against real Mars drives", not as astronaut truth.

## 3. Highest-leverage changes

**C1. Calibrated margins: "P90 margin", not "+76.34 min".** NOVEL: nobody else will have this.
What: Monte Carlo (about 500 draws, under 1 s on 150×150) over (a) the empirical path-inflation ratios above, (b) a speed band, and (c) DEM vertical σ 1.98 m from their own rover check, which perturbs slope and therefore the blocked cells. Report P50/P90 margin and P(return fits budget) like Ono's CDFs, and draw the return envelope as a P90 contour. Why: Validity plus Impact. "Can we still get back?" becomes "with 90% confidence, yes, by 41 min", backed by a calibration from 27 real Perseverance drives. Effort S–M (A2). Data: rover-traverse.json (already tracked), validation σ. The assistant cites these numbers through trusted_context and does not recompute them.

**C2. HiRISE 1 m DTM: show "what 20 m hides" and use it to coarsen conservatively.**
What: read only the crop window from the USGS Mars 2020 TRN HiRISE DTM mosaic. It has a direct GeoTIFF, can be read with GDAL `/vsicurl/` plus a window so the whole file is never downloaded, and covers the Octavia E. Butler landing area where the crop sits. Compute slope at a 2–5 m baseline. For each 20 m cell store **max and P95 HiRISE slope**, which is exactly the "conservative coarsening" validation.md says is missing. Add a toggle layer, "slope hidden at 20 m", and route on the conservative layer. Why: Validity, and it shows the team understands scale. Effort M (A1). Source: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_hirise_dtm_mosaic; quality reference: Kirk et al. 2021, https://mdpi.com/2072-4292/13/17/3511. Bulk data stays out of Git; track the checksum only.

**C3. Physical cost: time-optimal, grade-signed, asymmetric.**
What: edge time = length / v(signed grade). Use a Tobler-shape hiking function scaled so flat ground equals the scenario speed (Apollo 12/14 walking rates, as Peña-Asensio et al. 2024 did; SEXTANT used a Marquez slope-velocity model). The "lower slope" objective becomes "fastest". Compute the return field on **reversed edges** so the cost to get *home* is exact. Count ascent in the time. Keep the label: a hypothetical walking model, not suit physiology. Why: Validity. A climb now costs time, and the return can take longer than the outbound. Effort S–M (A2; touches the reach and stress code and the tests).

**C4. Terrain-class hazard layer: Séítah sand and ripple fields.**
What: take the mapped units from the Stack et al. 2020 Mars 2020 Science Team photogeologic map. Its supplementary ZIP (MOESM3) probably holds the GIS; verify that first. Rasterize it to the grid and apply an Ono-style per-class speed table (sand/ripples: slow or no-go, labelled hypothetical). Optional: a rock-abundance class from the HiRISE ortho if time allows (CFA thresholds 7%/15%). Why: Relevance ("layered view from multiple missions") and Validity. It also makes the two objectives produce *visibly different* routes. Effort M. Sources: https://link.springer.com/article/10.1007/s11214-020-00739-x; Ono et al., https://www-robotics.jpl.nasa.gov/media/documents/Data-driven%20surface%20traversability%20analysis%20for%20Mars%202020%20landing%20site%20selection.pdf

**C5. "Perseverance as test pilot" replay view.** NOVEL.
What: in the 3D view, play a real rover drive (sol N to N+1). Draw the planner's prediction for the same endpoints over it, with the odometry/prediction ratio, and finish with the calibration histogram from §2. Why: Creativity plus Validity in one 15-second demo beat. Real Mars ground truth beats any competitor's synthetic hazard markers. Effort S (data and script exist; B2 renders two polylines).

**C6. AI proposes, physics disposes. This mirrors JPL's real Dec 2025 AI-planned drives.**
What: in December 2025 JPL had Claude propose Perseverance waypoints from HiRISE plus slope, then humans reviewed them before upload (~456 m over two drives). Copy that loop for a multi-stop Marswalk. The model reads stop evidence and the image tile, then proposes an ordered stop sequence with a science rationale. The server evaluates each proposal deterministically, using a sequential Dijkstra for ordering as in Ono et al., and accepts or rejects it with reasons. The human approves. The model never produces a number; every metric shown is server-computed (the rule is preserved). Why: it is the team's "best use of AI" thesis, with a real NASA precedent to cite. Effort M (B3 + A3). Sources: https://www.anthropic.com/news/claude-on-mars; https://www.space.com/space-exploration/mars-rovers/nasas-perseverance-mars-rover-completes-its-1st-drive-planned-by-ai

**C7. Line-of-sight-to-base constraint (viewshed).**
What: a viewshed from the base (mast height as an input) on the DEM, and a "minutes out of sight" metric per route. Artemis EVA planning lists "max time without line of sight to lander" alongside slope limits and consumables redlines (NASA ASCEND 2025). Why: Relevance to real EVA ops at very little cost. Effort S. Sources: https://ntrs.nasa.gov/api/citations/20250006988/downloads/ASCEND%20presentation%20-%20Planning%20Lunar%20EVAs.pdf; Peña-Asensio et al. 2024, https://boris.unibe.ch/194784

**C8. Fix false precision and staircase geometry (polish).** Round margins to whole minutes with a band from C1. Apply line-of-sight path smoothing (string-pulling over cells that are not blocked) before display and distance. Effort S.

Priority with days left: **C1 + C5** (cheapest, most novel, same data), then C3, then C2 or C4 (one of them, not both).

## 4. The trap: training our own ML terrain classifier "to use AI"

The ML/AI panelist will likely push "run a SPOC/AI4Mars-style deep-learning terrain classifier on HiRISE". Don't. AI4Mars labels are *rover* images, not orbital ones. NOAH-H was applied to Jezero (Wright et al. 2022), but it is a research system and you cannot reproduce it in days. Without labels there is no confusion matrix. A domain judge will ask "what is its accuracy on Séítah?", and an unvalidated colour layer breaks the "synthetic is never real" spirit of this project. Use the **human-mapped** Stack et al. units (C4) as the class layer. Put AI where it can be checked: proposals verified by the planner (C6) and uncertainty calibrated against rover truth (C1/C5).

## Sources
- Ono et al., Data-driven surface traversability analysis for Mars 2020 landing site selection (JPL): mobility model, CFA thresholds, sequential Dijkstra, +30% odometry inflation, −5.4% 8-connected correction, CDF metrics. https://www-robotics.jpl.nasa.gov/media/documents/Data-driven%20surface%20traversability%20analysis%20for%20Mars%202020%20landing%20site%20selection.pdf
- JPL rapid traverse 2023 (ripple-field route rejected for drive-fault risk): https://robotics.jpl.nasa.gov/media/documents/2023-rapid-traverse.pdf
- Sun & Sholes 2024, Mars 2020 strategic planning process: https://sfsholes.github.io/papers/SunSholes2024_Mars2020StrategicPlanningProcess.pdf
- Kirk et al., stereo DTM quality at Jezero (HRSC/CTX/HiRISE): https://pubs.usgs.gov/publication/70212659 , https://mdpi.com/2072-4292/13/17/3511
- USGS M2020 TRN HiRISE DTM (1 m) / ortho (25 cm): https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_hirise_dtm_mosaic ; newer MSR release https://doi.org/10.5066/P13CPYYU
- Stack et al. 2020 photogeologic map: https://link.springer.com/article/10.1007/s11214-020-00739-x
- Wright et al. 2022, NOAH-H at Jezero: https://oro.open.ac.uk/84535
- ENav ML heuristics (Abcouwer et al.): https://arxiv.org/abs/2011.06022
- Peña-Asensio et al. 2024, minimum-metabolic lunar traverses: https://boris.unibe.ch/194784
- NASA ASCEND 2025, Planning Lunar EVAs: https://ntrs.nasa.gov/api/citations/20250006988/downloads/ASCEND%20presentation%20-%20Planning%20Lunar%20EVAs.pdf
- SEXTANT / suited energetics (MIT): https://dspace.mit.edu/handle/1721.1/33088 ; Kluis et al. 2022: https://bhp.engr.tamu.edu/wp-content/uploads/sites/212/2022/02/Kluis-et-al.-2022-A-METHODOLOGY-FOR-ANALYZING-AND-IMPROVING-EVA-PERFORMANCE.pdf
- AI-planned Perseverance drives, Dec 2025: https://www.anthropic.com/news/claude-on-mars
