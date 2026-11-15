# lunar-artemis: what the Moon already solved that MARS RETURN should take

Lens: Artemis south-pole EVA planning (AEGIS/JETT products, VIPER traverse planning, Apollo field lessons). The entry stays a Mars entry; these are ideas worth taking.

## 1. Three-minute look from a lunar EVA desk

- **It plans the wrong scarce resource.** An Artemis EVA is not limited by minutes alone. FOD's constraint list has seven items: *"maximum traverse distance, maximum distance from lander, traverse lighting requirements, maximum safe slope for walking, maximum time without line of sight to lander, consumables redlines"* (NASA ASCEND 2025, Kostak/Caswell/Young). MARS RETURN models two of them, slope and time. jpl-traverse already measured that slope almost never binds here. **I measured that line of sight does bind** (below).
- **The products don't match what a flight team hands a crew.** NASA's flight products are a **Map Book** (slope, lighting, comm coverage, horizon views, geologic map, traverse maps, POI descriptions), a **cuff checklist**, EVA procedures and **flight rules** (same source). MARS RETURN has a "Mission report" instead. A judge from JSC would notice that the vocabulary is missing.
- **The assistant answers chat; Artemis uses AI to propose and check plans.** VIPER's SHERPA proposes traverses, and humans edit them: *"Any changes made are then run back through SHERPA to determine if it's feasible"* (NASA Artemis blog, Dec 2023). The closest academic analogue, RASAGE (UC Davis, SpaceCHI 2025), puts Phi-4-mini over A*, a metabolic model and a cited knowledge base. It reports **no measured results**; only targets such as "near-100% compliance". MARS RETURN already does something RASAGE only promises: a model answer is discarded unless its numbers match the stored plan. Nobody can see that today.

### Measurement: line of sight binds where slope does not
I ran a viewshed on `data/region/elevation.json` (20 m CTX). Settings: base at `[510,1510]`, a hypothetical 2 m mast, crew eye height 1.7 m, nearest-cell ray sampling, no curvature (curvature drops terrain about 1.3 m at 3 km, so this is optimistic). Routes come from live `/api/plan` with default inputs. Script: `scratchpad/lunar_vs.py` and `scratchpad/lunar_route.py`.

| Route (outbound) | No-LOS share | Longest blind stretch |
|---|---|---|
| **Sid** (demo default), shortest | **73%** | **805 m ≈ 27 min** |
| Sid, lower slope | 70% | 788 m ≈ 26 min |
| Roubion, shortest | 43% | 622 m ≈ 21 min |
| Rochette, shortest | 18% | 193 m ≈ 6 min |

- The base sees only **25.6%** of the 3×3 km box at 2 m, and 44.5% even with a 10 m mast.
- 3 of the 5 sampling sites are out of sight of the base.
- On the headline demo route the crew is out of direct contact for most of the walk. The current UI shows that route as "+76 min margin, GO".

**Challenge to isro #4 and jpl C7:** the viewshed is **not novel**. Sightline (Jakarta, https://github.com/monek825/sightline) already ships per-landmark viewsheds and a route "blind fraction". Build it anyway, because it changes the verdict on the demo route. The novelty has to come from what MARS RETURN does with it (L2, L3).

## 2. What the Moon does better (cited)

- **Artemis EVA development (AEGIS, JETT3/JETT5).** The process runs: prioritized POIs, then a "constraint-driven operational range", then POIs grouped into EVAs, iterated with stakeholders. The outputs are Map Book, cuff checklist, procedures and flight rules (ASCEND 2025).
- **VIPER.** It needed simultaneous sun, Direct-to-Earth comm and traversable terrain. When Earth was down, the rover parked at pre-planned **"Safe Havens"**. Legs had to stay in view of Earth except for planned shadow operations under 8 h. Strategic planning was solved as a cost-constrained TSP (NASA 2022 VIPER mission-planning overview; SpaceOps 2022).
- **MoonPath** (Peña-Asensio et al., *Acta Astronautica* 214, 2024): Dijkstra plus Monte Carlo on 5 m LOLA. It enforces a 15° slope limit and scores **astronaut-to-lander direct view**, body illumination, surface temperature and bearing capacity together. Walking times are taken from **Apollo 12/14 EVA data**, and the traverses are published as an atlas. MARS RETURN is a single-objective cousin of this.
- **Apollo walkback doctrine.** The LRV walkback assumed a rover failure, a walk home at **3.3 km/h** at elevated metabolic rate, and a **20% pad**. Crews drove to the *farthest* station first and worked back toward the LM (NASA ALSJ planning doc; SP-4204 ch. 23). On Apollo 17 the limit was **recomputed during the EVA from actual consumption** (TTU "EVA Walk-Back Limit Calculation"). That recomputation is exactly what MARS RETURN's rehearsal does.
- **Apollo 14, Cone Crater.** In hummocky terrain Shepard and Mitchell mistook a flank crater for the rim: "Our positions are all in doubt now". Mission Control called them back by the clock. LROC NAC later showed their tracks ending about 30 m short of the rim (NASA SP-350; LRO via Universe Today; NASA SVS 4883). This is the most famous "can we still get back?" decision in history, and it was made on time, not on position.
- **Latency.** Artemis already moves decisions from MCC to the IV crewmember because of a 5-14 s delay (Elston et al., IEEE Aero 2026, NASA JSC/ARC review). On Mars the local link between EV crew and base IV is the operational one.

## 3. Proposals

**L1. Open the video with Apollo 14. S. Presentation, Relevance.**
- 0-5 s: the LROC image of Apollo 14's tracks ending short of Cone's rim, with the line "1971: 30 m from the rim, lost, called back by the clock." Then cut to Jezero: "MARS RETURN computes that clock before you walk."
- Add one line of provenance in the UI and report: "the rehearsal is Apollo 17's in-EVA walkback recomputation."
- This fits the 30 s limit and gives judges a real human precedent no rival uses. LIFELINE uses the generic walk-back rule, not this event.
- Data: NASA/GSFC/ASU public-domain imagery.

**L2. Make "minutes without line of sight" a flight-rule input, inside the plan and the rehearsal. S-M. Validity, Relevance.**
- *What:* a viewshed from the base mast, with mast height as a labelled hypothetical input. Report three numbers per route: total blind minutes, longest blind stretch, and blind minutes on the *return* leg after a rehearsal event.
- Add a user limit ("max 10 min out of sight", hypothetical) that turns a GO amber. Optionally add a third objective, "stay in contact": cost multiplied by a factor in cells the base cannot see.
- *Why:* it is the Artemis FOD constraint verbatim. It flips the default demo route (Sid: 27 min blind). Sightline only gives a distance share, with no clock and no return logic.
- *Data:* CTX DEM only. A2 adds about 30 lines of numpy to `routing.py`, with new fields in the schema, `api-contract.md` and `trusted_context`.

**L3. NOVEL: the "Safe Haven" field, or minutes to regain contact. M. Creativity, Impact.**
- *What:* a multi-source Dijkstra seeded from every visible cell. `return_field` already exists; `_search` needs to accept a start set. The result is a second cost-to-go map: *minutes to the nearest point where base can hear you*.
- In the rehearsal, add a third option next to "return now / continue": **"move to contact (N min), then decide"**.
- In stress: flag closures that push the return path into a blind valley ("survivable but silent").
- *Why:* VIPER planned Safe Havens for Earth-down periods, and this is the same idea on foot on Mars. No rival computes "how far to regain comm" from an arbitrary point. It is visibly clever and pure arithmetic, and the assistant can cite it.

**L4. NOVEL: the report becomes an Artemis-format Map Book and cuff checklist, drafted by the AI and checked by the server. M. Validity, Presentation, the "AI used best" thesis.**
- *What:* restructure the report into NASA's product set: traverse map, slope, comm coverage (L2), POI page per stop, cuff card (turn-around clock, blind-stretch warnings, walkback minutes), and a flight-rules page listing every hypothetical limit.
- The LLM drafts *only prose*: POI descriptions and the plain-language flight-rule wording. Every number is a placeholder that the server fills from `trusted_context`. Every line carries a source chip.
- *Why:* it places the AI where NASA's EVA Task flight controllers spend days, producing flight products, not chat. It answers RASAGE: "they propose cited, traceable EVA guidance; we enforce it with a numeric gate." This is the honest-AI demo beat.
- *Data:* existing evidence and plan state, plus CRISM/geology text if planetary-geologist's item A lands.
- Overlaps eva-human-factors #5 (cuff card). Merge them: their card, in NASA's Map Book frame.

**L5. Far-first ordering for a two-stop EVA. M. Validity.**
- Brac and Issole are both in South Séítah, about 120 m apart. Offer a two-stop plan and order the stops with the Apollo LRV rule: farthest first, then work back toward base. Show both orderings' minimum return margin.
- It is a VIPER-style ordering problem (cost-constrained TSP), trivially small here.
- Skip it if days are short. L2 and L3 first.

**L6. Horizon views at each station, far-field only. M. Presentation. Optional.**
- The Map Book's "horizon views" are a navigation aid. Render one static 360° skyline per station from the **full source DEM** (manifest `sourceElevationBoundsXY` covers about 89×101 km), so the delta front and crater rim kilometres away appear.
- Mark the bearing to base on it. Use far features only, because the 20 m DEM cannot honestly draw the near field.

**Priority:** L2, then L1 (both S, done in a day), then L3, then L4. L5 and L6 only if time remains.

## 4. Challenges to the panel, where the Moon says otherwise

- **isro #1, sunset clock.** Illumination routing is the defining lunar *polar* problem because the sun sits about 1.5° above the horizon and shadows sweep the route (VIPER's shadow modelling). At 18°N, a 3 h EVA started at mid-sol never meets sunset; start time is a scheduling choice, not a route constraint. Show it as a label, not a feature.
- **eva-human-factors #3 and ai-strategist G, Earth light-time.** Artemis is already moving authority to the IV crewmember at 5-14 s of delay. At Mars light-times Earth is out of the loop entirely. The link that matters is EV crew to base IV, which is L2 and L3. A countdown to Earth makes good theatre but models the wrong link.
- **jpl C3 and eva #1, Tobler time.** Agree. MoonPath used empirical Apollo walking rates; using a measured rate beats inventing one.

## 5. Trap: copying "Horizon Match" or AI skyline localization

Sightline's pitch is to find yourself by matching the helmet-camera skyline to the DTM. The panel (red-team, viz) may want to match it. Don't:
- **Apollo 14 is the counter-example.** In hummocky terrain the crew could not tell a flank crater from Cone's rim while standing on the slope. Near-field skylines are ambiguous exactly where you are lost.
- A 20 m DEM cannot render the 1-100 m relief that forms a walker's near horizon.
- There is no real helmet camera, so any demo input would be synthetic and presented as a capability, which breaks a project rule.
- Sightline already owns it.

MARS RETURN wins by answering the question Apollo 14's controllers actually had to answer: not "where am I?" but "how long until you must turn, and will we hear you if it goes wrong?"

## Sources
- NASA ASCEND 2025, "EVA Development in Exploration-Driven Human Spaceflight": https://ntrs.nasa.gov/api/citations/20250006988/downloads/ASCEND%20presentation%20-%20Planning%20Lunar%20EVAs.pdf
- Elston et al., IEEE Aero 2026, review of NASA EVA informatics (AEGIS, xGDS, PATH, SEXTANT, Maestro): https://ntrs.nasa.gov/api/citations/20260001895/downloads/IEEEAeroConfPresentation_LeAP%20-%20STRIVES.pdf
- VIPER mission-planning overview: https://www.nasa.gov/wp-content/uploads/2022/05/overview_of_mission_planning_for_the_viper_rover.pdf ; SpaceOps 2022: https://ntrs.nasa.gov/api/citations/20220008301/downloads/2022-06-02-spaceops-viper-planning.pdf ; VIPER 2026 update: https://ntrs.nasa.gov/api/citations/20260002876/downloads/viper-2026-04-29_v2.pdf
- SHERPA and AI on VIPER: https://www.nasa.gov/blogs/artemis/2023/12/01/part-1-artificial-intelligence-and-nasas-first-robotic-lunar-rover/
- RASAGE (SpaceCHI 2025): https://drops.dagstuhl.de/storage/01oasics/oasics-vol130-spacechi2025/html/OASIcs.SpaceCHI.2025.6/OASIcs.SpaceCHI.2025.6.html
- MoonPath (Peña-Asensio et al. 2024): https://boris.unibe.ch/194784 ; https://phys.org/news/2023-10-lunar-astronauts-easy-trails-moon.html
- Apollo walkback: https://www.nasa.gov/wp-content/uploads/static/history/alsj/19790073512_1979073512.pdf ; https://www.american-spacecraft.org/documents/sp-4204/chapter-23.html ; https://ttu-ir.tdl.org/handle/2346/74208
- Apollo 14 Cone Crater: https://www.nasa.gov/wp-content/uploads/static/history/SP-350/ch-12-6.html ; https://universetoday.com/37870/latest-lro-image-solves-apollo-14-mystery ; https://svs.gsfc.nasa.gov/4883
- Mars relay (no DTE about 12 h/sol): https://science.nasa.gov/mars/mars-relay-network-update/
- LUMINA (OSU, DPS 2026), lunar VLM for decision support: https://www.eurekalert.org/news-releases/1149651
- Sightline: https://github.com/monek825/sightline
