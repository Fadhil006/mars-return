# Research: making MARS RETURN a winning entry

Research date: 14 November 2026, which is the first day of the event weekend (14–15 November 2026).
Scope: what judges reward, what competing teams have already built, which data to add, whether any model training is needed, and what storage and hosting the project needs.

> **Verification gap.** `spaceappschallenge.org` failed TLS verification again, both from this machine (curl error 60) and through the fetch tool, and nothing was bypassed. Everything below about the official rules comes from search-engine excerpts of the official pages or from older guides. **A team member must open the challenge page, the Judging & Awards Guide and the Project Submission Guide in a browser today and check the submission deadline and demo limits.**

---

## 1. TL;DR: the actions most likely to change the result

1. **Ship something judges can open.** Both strong competitors have live Vercel sites. Without a public link and a 30-second video, the Presentation score is close to zero. This matters more than any other item here.
2. **Do not pitch slope-limited A\* or "can we walk home" as new.** Team Protikriti already ships GO/NO-GO walk-home checks, walking-range rings and a Perseverance drive benchmark at Jezero.
3. **Pitch what nobody else has:**
   - the mid-route rehearsal: an event happens, then compare "return now" with "continue, then return"
   - the closure stress test
   - the return envelope tied to a hypothetical scenario
   - an assistant that cannot invent numbers
   - a validation record

   No competitor README describes any of these.
4. **Raise the resolution.** Upgrade the routing terrain from the 20 m CTX grid to the 1 m HiRISE DTM mosaic of Jezero. Every competitor routes on 20 m or coarser terrain and admits that boulders are invisible. At 1–5 m, MARS RETURN would be the only entry whose slope map is close to astronaut scale. This one change can be checked and helps the Validity score.
5. **Add one more mission dataset that changes a decision.** CRISM minerals for choosing the science stop is the best candidate (see §5). The official challenge asks for data from several missions combined; the entry currently uses two (MRO/CTX and Mars 2020).
6. **Give walking speed a source.** Protikriti's pace model is Tobler × 0.8 with no NASA citation. A cited, slope-dependent model (Marquez/SEXTANT, built from Apollo data, or the Pandolf equation) is an easy Validity win.
7. **No ML training is needed.** Storage is small: about 0.5 GB of raw data now, and about 3–5 GB if HiRISE is added. See §6 and §7.

---

## 2. What the challenge asks for

Challenge: *Interplanetary Survival Guide: Martian Map*. Category: Human Exploration / Mars. Difficulty: beginner to intermediate.

The official description, as seen through search excerpts, asks for a layered, integrated view of a location or route on Mars. It should combine data from several NASA science missions so that a future astronaut can plan a safe Marswalk with science along the way.

The unofficial starter guide (Space Data Atlas) suggests a "first hour" workflow:

1. Load the CTX mosaic and MOLA hillshade from Mars Trek.
2. Choose a route, then pull HiRISE images and DTMs along it.
3. Mark hazards (slopes, boulders) and science targets.
4. **Add at least one more data type, such as thermal or radiation.**

The resources it names are Mars Trek WMTS, HiRISE (PDS), CRISM MTRDR (through ODE), THEMIS thermal mosaics, NASA Ames Mars climate simulations (MCMC ref), Curiosity RAD, and the NASA Image and Video Library API.

**How MARS RETURN maps to the challenge:**

| Challenge element | MARS RETURN today | Gap |
|---|---|---|
| Real location or route | Jezero, real CTX DEM and orthoimage | Resolution: 20 m |
| Several NASA missions | MRO/CTX and Mars 2020 (traverse, sampling sites, rover-vs-orbit elevation check) | A third mission dataset that affects a decision |
| Hazards | Slope, missing-data mask | No rocks or boulders; HiRISE would help |
| Science along the way | Five real Perseverance sampling sites | Why each stop matters scientifically (CRISM) |
| A further data type | None | Thermal (THEMIS thermal inertia) or radiation (RAD) |
| Safe Marswalk | Round trip, rehearsal, return envelope, stress test | Already the strongest part |

---

## 3. How judging works

Sources: search excerpts of the current Judging & Awards Guide, plus the 2020–2025 guides.

- **Process:**
  1. Local and Universal Event judges pick **Global Nominees**, roughly 1 per 10 submitted projects.
  2. Expert judges from NASA and the Space Agency Partners pick the **Global Finalists**.
  3. A separate panel picks **10 Global Winners**.

  In 2025 there were about 1,290 nominees. Reported participation varies between sources (about 11,500 projects or 18,860 teams).
- **Five criteria, equally weighted:**
  - **Impact:** the size of the problem and how many people it could help.
  - **Creativity:** novelty.
  - **Validity:** whether it is scientifically sound, achieves its stated goal and could work in the real world.
  - **Relevance:** whether it answers *this* challenge.
  - **Presentation:** whether the demo quickly makes the project's importance clear to someone with no background in the subject.

  The guide explicitly warns teams not to neglect Presentation.
- **Global award categories** (2025 names; each year may differ):
  - Best Use of Data: makes space data accessible or uses it for a distinctive application
  - Best Use of Science
  - Best Use of Technology
  - Best Use of Storytelling
  - Galactic Impact
  - Best Mission Concept: the most plausible concept and design
  - Most Inspirational
  - Local Impact
  - and others

  The best fits for MARS RETURN are **Best Mission Concept**, **Best Use of Science** and **Best Use of Data**. Tune the pitch for these.

### Submission requirements (current guide, from search excerpts; verify in a browser)

- **Demo:** a video of **30 seconds or less**, *or* a slide deck of **up to 7 slides** including the title slide. Videos and slides cannot be uploaded to the Space Apps site, so host them elsewhere (for example YouTube unlisted or Google Drive) and link them.
- **Public links must work without logging in.** One 2026 local event template says so explicitly.
- **English** on the project page and in linked material. No images of anyone under 18.
- **AI tools are allowed**, but you must **state where and how AI was used**. Some sources also mention watermarking AI-generated images or video; that is unconfirmed, so check the official text. This project used Claude Code during development, so declare that.
- List every NASA and partner dataset used. `docs/data-method.md` and `data/sources/` already hold this; copy it into the submission.
- "Create Your Own Challenge" entries cannot win global awards. This entry is on an official challenge, so that does not apply.

---

## 4. Competitors on the same challenge (public repositories, read 14 November 2026)

| Team | Live | Stack | Strengths | Admitted or visible weaknesses |
|---|---|---|---|---|
| **Protikriti** "Martian Map" (strongest) | atlas-mars.vercel.app / martian-map.vercel.app (the two links disagree) | TS + CesiumJS, Python pipeline, Vercel, 182 tests, CI | Whole-planet globe with 20 m Jezero terrain; Rover Street View from 2,087 Navcam stops; A* using Tobler × 0.8 with a 15° cutoff; **GO/NO-GO walk-home card; 1/2/4 h walking-range rings**; line of sight; hazard markers with detour cost; benchmark against Perseverance's real drive; MEDA/REMS weather; 30 sample cores; site report (ice, radiation, daylight); offline mode. About 25 datasets. | Pace model has no NASA citation and Mars gravity is not modelled. 20–32 m slope map, so boulders are invisible. Flat 20 min per science stop. **No LLM assistant.** Very wide scope. |
| **UnknownX** "MarsWay" | marsway-cyan.vercel.app | React 19, Leaflet, Three.js, Express | Globe, 2D map and first-person EVA HUD; **shortest / safest / science route comparison**; offline rule-based assistant (English, Bangla, Banglish) with voice; provenance tags (Observed / Derived / Modeled / Simulated); many layers | MOLA-scale terrain. Much of the content is simulated (suit vitals, dust devils). Messy repository. No visible tests. |
| pollob-kumar "Marswalk Planner" | none | React, Leaflet, three.js | Scaffold only | No real data yet |
| PrinceTimilsina | none | none | Research notes only | No code |

**Conclusions for positioning:**

- Breadth is a losing battle; Protikriti has more layers than this team can add in a weekend. Win on **depth and rigour about one question**: *"Can we still get back, and what if something changes?"*
- Features **only MARS RETURN has**:
  - the mid-route event rehearsal
  - the closure stress test (worst single closure on the way home)
  - a grounded LLM brief that may only quote the server's numbers
  - an elevation profile tied to the route
  - a published validation record
  - sampling sites located from rover localizations, not hand-placed
- Things to **copy cheaply**, because judges will expect them:
  - provenance tags on every number (the project already has the "hypothetical" labelling idea; make it visible in the UI)
  - a short benchmark: "our route compared with Perseverance's real path"
  - a shareable URL for each scenario

---

## 5. Data upgrades, ranked by benefit per hour

### 5.1 HiRISE DTM at Jezero (highest value)

- **Product:** USGS *Mars 2020 Terrain Relative Navigation HiRISE DTM Mosaic*. It is built from 7 HiRISE stereo pairs and co-registered to the CTX mosaic that the project already uses, with a median vertical offset from CTX of about 0.4 m. That alignment means the coordinate pipeline needs few changes.
  https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_hirise_dtm_mosaic
- **Alternatives:**
  - *Mars Human Exploration Zone DEM Archive 2023*: HiRISE DEMs at 1 m post spacing.
  - The 25 cm HiRISE orthomosaic, about 3.2 GB.
  - The PDS HiRISE DTM archive (`MRO-M-HIRISE-5-DTM-V1.0`), indexed on USGS STAC.
- **Approach:**
  1. Crop to the existing 3 × 3 km box.
  2. Resample to **2–5 m**. At 5 m the grid is 600 × 600 = 360k cells; at 2 m it is 1500 × 1500 = 2.25M cells. The 1 m native grid is 9M cells, which is probably too slow for the request-time routing in `server/routing.py`, so measure before choosing.
  3. Keep CTX as the fallback context layer and say which product each number came from.
- **Cost:** this changes `modelVersion` and every validated number. Re-run `scripts.validate_demo` and regenerate `docs/validation-results.json`.
- **Pitch line:** "Every other entry plans on 20 m terrain. We plan on HiRISE stereo terrain at X m, the same product NASA used to land Perseverance."

### 5.2 A third mission that changes a decision

| Candidate | What it adds to the decision | Access | Effort |
|---|---|---|---|
| **MRO/CRISM mineral map** | Ranks science stops by mineralogy (carbonates and clays on the delta). "Is this stop worth the extra 40 minutes?" | ODE REST: `https://oderest.rsl.wustl.edu/live2/?query=product&results=fp&output=JSON&target=mars&ihid=MRO&iid=CRISM&pt=MTRDR` with a box around 77–78°E, 18–19°N | Medium |
| **Odyssey/THEMIS thermal inertia** | Sand compared with bedrock: a traversability cost (loose sand is slower). MEDA measured thermal inertia from about 180 (dunes) to 605 (bedrock) SI on the ground, which can serve as a cross-check. | Mars Trek WMTS | Low–medium |
| **MSL RAD surface dose** | A radiation budget for the EVA: dose per hour × route time. Gale data used as a stand-in for Mars. | PDS PPI `MSL-M-RAD-3-RDR-V1.0` | Low (one constant, cited) |
| **MGS/MOLA** | Regional context and hillshade | Mars Trek WMTS `Mars_MGS_MOLA_ClrShade_merge_global_463m` | Low (display only) |
| **Mars 2020 MEDA** | Conditions on the sols of each sample | PDS Atmospheres, DOI 10.17189/1522849 | Medium |

**Recommendation:**

- Use **THEMIS thermal inertia as a route-cost term**. This is a terrain-type hazard the challenge explicitly asks for.
- Use a **RAD dose constant** for the EVA dose line in the brief. It is cheap and adds a further data type.
- If time allows, use **CRISM to justify the science stops**.

Each one must change a number or a decision on screen, not only appear as a layer.

### 5.3 Walking-speed model with a source

- **NASA SEXTANT / BASALT** uses Marquez's metabolic model, extrapolated from Apollo data, with one speed per slope.
- The **Pandolf equation** (body mass, load, speed, grade, terrain factor) is used in NASA's 2024 EMBC paper on traverse metabolic cost.
- **Mars-gravity data point:** walking at 1.2 m/s costs about 0.060 kcal/kg-min at Mars gravity, against 0.069 on Earth.
- **Walk-back:** Apollo walk-back limits used constant speed and consumables. Artemis planning uses about 16 km round trip per EVA, and the JSC 10 km walk-back study is in lunar gravity. NASA presentations note that the Mars-gravity offload condition reached VO2max at 3.5 mph.

**Action (A2):** replace the constant speed with a cited slope → speed table (Marquez/SEXTANT form). Optionally add a Pandolf-based "metabolic cost of this route" line, labelled as a model. Do this once, before re-validating.

### 5.4 Hazards beyond slope

- Searches found no Jezero rock-abundance raster ready to download.
- Published work: about 63 boulder-fall tracks in Jezero mapped from HiRISE (GRL 2020), and automated boulder detection down to about 50 cm on the delta (JARS 2020).
- **Cheapest honest option:** derive a surface-roughness layer from the HiRISE DTM (local standard deviation of elevation after detrending) and label it "roughness proxy, not a boulder count".

---

## 6. Is any training required?

**No.** Nothing in the challenge or the judging needs a trained model, and the project's core is deterministic arithmetic, which suits the Validity criterion better.

| Possible ML use | Verdict |
|---|---|
| LLM assistant (`/api/brief`) | **No training.** It uses an API model only when `MODEL_API_KEY` is set and otherwise falls back to deterministic templates. A model answer is kept only if its numbers and citations match the stored plan. This rule is a selling point; say it in the pitch. |
| Terrain classification (AI4Mars) | Optional and **not recommended this weekend**. AI4Mars has about 50k rover images with 425k labels on Zenodo; a DeepLabv3 baseline reached about 96% accuracy; a Perseverance-adapted MobileNetV2 (SPOC) reached about 84%. No ready Perseverance checkpoint was found, and the labels are rover-view, not orbital, so they would not plug into the route grid. Licence: "not specified" on data.gov. |
| Boulder detection on HiRISE | Research-grade work, not weekend work. Use the roughness proxy (§5.4). |

If the team uses a hosted LLM for the brief, budget a few cents per demo run. The deterministic fallback must work with no key, because judges may run it without one.

---

## 7. Storage, compute and hosting

**Measured on this machine:**

| Item | Size |
|---|---|
| `data/raw` (CTX DEM and ortho, downloaded by `prepare_demo`) | 432 MB |
| `data/region` (prepared bundle, 150 × 150 grid at 20 m) | 1.1 MB |
| `data/packages` | 296 KB |
| `.venv` | 261 MB |
| `web/node_modules` | 125 MB |

**With HiRISE added (estimated):**

- Raw DTM mosaic plus orthoimage: about 1–4 GB. The 25 cm orthomosaic alone is about 3.2 GB; crop it right after download.
- Prepared bundle at 5 m: about 360k cells per layer, so a few MB as JSON. Consider binary `Float32Array` or WebP for elevation if it grows past about 10 MB.
- **Total disk needed: under 10 GB. No GPU and no database.** Plans stay in process memory, as the project rules require.

**Hosting** (a live link is required in practice):

- **Frontend (static Vite build):**
  - Cloudflare Pages (free, unlimited static bandwidth, **25 MiB per-file cap**, 20,000 files)
  - Vercel Hobby (non-commercial)
  - GitHub Pages (1 GB site soft limit)

  The prepared region bundle is small enough for any of these.
- **Backend (FastAPI, one worker):** needs a small always-on container, such as Render or Fly.io free/hobby tiers, a Hugging Face Space (Docker), or a cheap VPS.
  - Ship the *prepared* bundle in the image, not `data/raw`.
  - Do not expose `MODEL_API_KEY` to the browser.
  - Free tiers that sleep add a cold start of 30 s or more. Warm the server up before judging, or record the demo video locally.
- **Cheapest alternative with nothing to keep running:** pre-compute the demo scenarios and serve them as static JSON next to the frontend, with the live API as an option. The rule against synthetic data is not broken, because the JSON comes from real terrain computed by the real server. Label it "precomputed from server v X".
- All free-tier limits above come from secondary blogs. Check the provider's own docs before relying on them.
- Never commit bulk rasters; the existing `.gitignore` rules already cover this.

---

## 8. Plan for the remaining weekend

Suggested order, using the owner roles from `CONTRIBUTING.md`:

| Priority | Task | Owner | Criterion |
|---|---|---|---|
| P0 | Check the deadline and demo rules in a browser and record them in `docs/submission-checklist.md` | B1 | none |
| P0 | Finish and merge the frontend (`group-b-frontend` has uncommitted map, rehearsal, route and profile work) | B1/B2 | Presentation |
| P0 | Deploy the frontend and backend (or precomputed JSON) to a public URL that works without login | B2 | Presentation |
| P0 | 30-second video following `docs/demo-script.md`: question → route → event → "return now or continue" → stress test → brief with citations | B3 | Presentation |
| P1 | HiRISE DTM at 2–5 m and re-validation | A1/A2 | Validity, Creativity |
| P1 | Cited slope → speed model | A2 | Validity |
| P1 | THEMIS thermal inertia as a route cost, or a RAD dose line | A1/A3 | Relevance |
| P2 | "Our route vs Perseverance's real traverse" comparison (the traverse is already in the bundle) | A2/B1 | Validity |
| P2 | Provenance tag on every number in the UI (Observed / Derived / Hypothetical) | B3 | Validity |
| P2 | CRISM-justified science stops | A3 | Relevance |
| P3 | Shareable scenario URL | B1 | Impact |

**Pitch structure for 7 slides, or the 30-second video:**

1. The problem: astronauts walk from a base; things change mid-walk.
2. The question: "Can we still get back?"
3. Real Jezero terrain (HiRISE/CTX) and real Perseverance sampling sites.
4. Rehearsal: an event at a point, then return now against continuing.
5. Stress test and return envelope.
6. Validation, with every number traceable to its source.
7. Data used (missions) and an AI-use disclosure.

**Words to avoid:** "safe route", "certified", "real-time hazard". **Say instead:** "model result on real terrain, with hypothetical scenario inputs".

---

## 9. Sources

**Official and challenge:**
- Challenge page (read through search excerpts; direct fetch failed TLS): https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/
- Judging & Awards Guide: https://www.spaceappschallenge.org/resources/judging-awards-guide
- Project Submission Guide: https://www.spaceappschallenge.org/resources/project-submission-guide/
- 2025 awards: https://spaceappschallenge.org/2025/awards and NASA's announcement https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-announces-2025-international-space-apps-challenge-global-winners/
- AI-disclosure discussion: https://github.com/nasa/spaceapps/discussions/1273
- 2026 local template ("links must work without login"): https://github.com/2026-NASA-Space-Apps-Besanzon/template
- Older guides: https://spaceapps-prod.s3.amazonaws.com/media/documents/Space_Apps_2022_Judging_and_Awards_Guide.pdf, https://spaceapps-prod.s3.amazonaws.com/media/documents/Space_Apps_2022_Project_Submission_Guide.pdf

**Starter guide and competitors:**
- Space Data Atlas starter guide (unofficial): https://spacedata.swapniltamse.com/challenges/martian-map/
- Protikriti: https://github.com/AhsanulHoque22/Nasa-Space-Apps-Challenge-2026-Team-Protikriti
- MarsWay (UnknownX): https://github.com/ahsanur-official/Interplanetary-Survival-Guide-Martian-Map
- pollob-kumar: https://github.com/pollob-kumar/nasa-space-apps-martian-map
- PrinceTimilsina: https://github.com/PrinceTimilsina/spaceapp_research

**Data:**
- Mars 2020 TRN HiRISE DTM mosaic: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_hirise_dtm_mosaic
- Mars 2020 TRN CTX DTM mosaic: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_ctx_dtm_mosaic
- HiRISE DTMs on STAC: https://stac.astrogeology.usgs.gov/docs/data/mars/hirise_dtms/
- Human Exploration Zone DEM archive: https://astrogeology.usgs.gov/search/map/mars_human_exploration_zone_dem_archive_2023
- Mars Trek WMTS API: https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars
- ODE REST (CRISM, HiRISE search): https://ode.rsl.wustl.edu/mars/
- CRISM documentation: https://pds-geosciences.wustl.edu/missions/mro/crism.htm
- MSL RAD RDR: https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/
- MEDA surface energy budget at Jezero (Martínez et al. 2023): https://digital.inta.es:8443/jspui/bitstream/20.500.12666/867/1/
- Mars climate reference: https://data.nas.nasa.gov/mcmcref/
- Photogeologic map of the Perseverance field site: https://dspace.mit.edu/entities/publication/6f01f5fc-b4b2-4d09-bc5a-6a0746dc0f4e
- Boulder-fall tracks in Jezero: https://ui.adsabs.harvard.edu/abs/2020GeoRL..4790362S
- Boulder detection on the Jezero delta: https://ui.adsabs.harvard.edu/abs/2020JARS...14a4522N/abstract
- AI4Mars: https://data.nasa.gov/dataset/ai4mars-a-dataset-for-terrain-aware-autonomous-driving-on-mars and https://openaccess.thecvf.com/content/CVPR2021W/AI4Space/papers/Swan_AI4MARS_A_Dataset_for_Terrain-Aware_Autonomous_Driving_on_Mars_CVPRW_2021_paper.pdf

**EVA and walking models:**
- EVA performance methodology (SEXTANT / Marquez model): https://bhp.engr.tamu.edu/wp-content/uploads/sites/212/2022/02/Kluis-et-al.-2022-A-METHODOLOGY-FOR-ANALYZING-AND-IMPROVING-EVA-PERFORMANCE.pdf
- Pandolf-based traverse cost (NASA, EMBC 2024): https://ntrs.nasa.gov/api/citations/20240001423/downloads/IEEE%20EMBC%202024.pdf
- Lunar analog EVA metabolic rates: https://ntrs.nasa.gov/citations/20230014953
- Walk-back limit, Virtual Spacesuit: https://ttu-ir.tdl.org/handle/2346/74208
- Reduced-gravity energy cost: https://apu.edu/files/cris_reduced_gravities.pdf
- Mars mass / walk-back (ICES 2026): https://ntrs.nasa.gov/api/citations/20260005410/downloads/Mars_Mass_ICES2026_Presentation_Final.pdf
