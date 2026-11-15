# isro-scientist — Round 1

Perspective: Chandrayaan-3 (Pragyan traverse, Vikram hop), MOM, Chandrayaan-4 sample-return planning. Frugal, so the bias is toward decisions over features.

## 1. A judge's 3-minute look (brutal)

- **The budget is a number, not a clock.** "Total time budget 3 h 00 m" is an accountant's constraint. Every surface mission I have flown ran to the Sun's clock: Pragyan was parked with a full battery and its panel "oriented to receive the light at the next sunrise" because sunset ended the mission ([spacepolicyonline](https://spacepolicyonline.com/news/india-says-good-night-to-chandrayaan-3/)). There is no sol, no local solar time and no sunset anywhere in the product (I grepped `server/` and `web/src`; the only "sun" is a display light in `TerrainView.tsx`). A judge from any agency will notice this.
- **The event is generic.** "Hypothetical corridor blocked" is a checkbox. The defining moment of Pragyan's 100 m drive was concrete: on 27 Aug 2023 NavCam saw a 4 m crater 3 m ahead, and ground commanded a retrace and a new path ([Business Today](https://businesstoday.in/latest/story/chandrayaan-3-pragyan-rover-heads-to-new-path-after-locating-4-metre-diameter-crater-ahead-of-it-says-isro-395957-2023-08-28), [Deccan Herald](https://www.deccanherald.com/amp/story/science%2Fspace%2Fchandrayaan-3-rover-comes-across-crater-on-lunar-surface-reverts-to-safer-path-2663720)). Your rehearsal is the right idea, but the trigger is anonymous.
- **No communications at all.** Pragyan could only talk through Vikram. Perseverance's data goes out through relay passes by MRO, TGO (ESA) and Mars Express ([NASA Mars Relay Network](https://science.nasa.gov/mars/mars-relay-network/)). An excursion tool with no idea of "can base hear us here?" reads as a hiking app.
- **3 km × 3 km at 20 m means 150×150 cells.** That is honest, but it looks tiny next to Protikriti's Cesium globe. Make the smallness the point ("this is the scale of a walk") or a judge will read it as a limitation.
- **No headline verdict on screen.** The header says "No result yet". The first frame of the video should be one sentence a non-specialist remembers: *"Turn back by 15:40 or you walk home in the dark."*
- **The Evidence tab is a wall of text.** It is good provenance, but a juror will not read it. Lead with one card per mission that says what changed because of that data.
- **Mobile was still on "Loading the region" after 15 s** (in the existing screenshot; I did not re-test). Some judges open links on phones, so check it.

Why a competitor might outscore you: Protikriti already has a "can the crew still walk home" card, range rings, weather and about 25 datasets. On Presentation and Relevance they look bigger. Your edge (mid-route rehearsal, validated arithmetic) is invisible unless the demo puts it on a clock and a real event.

## 2. What the real world does better (and you can borrow cheaply)

- **Apollo walkback limit.** This is the original "can we still get back?" rule: the farthest point from the LM a crew could reach and still walk home on the PLSS consumables left if the LRV failed. Crews therefore drove to the farthest point first and worked back toward the LM ([Apollo 15 traverse planning, NASA ALSJ](https://www.nasa.gov/wp-content/uploads/static/history/alsj/19790073512_1979073512.pdf); [TTU walk-back paper](https://ttu-ir.tdl.org/handle/2346/74208)). Your `reach` envelope is the same idea; name it that way.
- **Mars24 (NASA GISS, Allison & McEwen 2000)** gives local true solar time and solar elevation and azimuth for any Mars longitude and date, with a stated error in Ls of 0.008° ([GISS credits](https://www.giss.nasa.gov/tools/mars24/help/credits.html), [technical notes](https://oregonl5.nss.org/mist/docs/Mars24J/help/notes.html)). It is a closed-form algorithm with no external data, so the server can compute it.
- **Perseverance ENav** plans from orbital maps on the ground, then re-plans on board from stereo when it meets terrain the orbital map could not resolve ([JPL Robotics](https://robotics.jpl.nasa.gov/what-we-do/flight-projects/mars-2020-rover/m2020mobility/)). Your 20 m DEM against the 5 m image is the same split between "map" and "eyes".
- **The sample-return rule: never risk the only copy.** Perseverance left duplicate tubes at the Three Forks depot as a backup to the samples it still carries ([NASA](https://www.nasa.gov/feature/jpl/nasa-s-perseverance-rover-completes-mars-sample-depot)). Chandrayaan-4's whole architecture hangs on go/no-go gates (ascender and transfer-module docking, rehearsed first by SpaDeX) ([Space.com](https://space.com/the-universe/moon/india-targets-2028-for-chandrayaan-4-sample-return-mission-to-moons-south-pole)).
- **ESA Mars Express HRSC Jezero DTM.** DLR called it the most accurate topographic model of Jezero when it was released ([DLR 2020](https://www.dlr.de/en/latest/news/2020/03/20200929_topography-of-jezero-crater)). It is distributed via ESA PSA, NASA PDS and ODE ([ODE HRSC DTMRDR](https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/MEX/HRSC/DTMRDR.htm)), and a USGS study compared HRSC, CTX and HiRISE DTM quality at Jezero directly ([USGS](https://www.usgs.gov/publications/evaluating-stereo-dtm-quality-jezero-crater-mars-hrsc-ctx-and-hirise-images)).

## 3. Highest-leverage changes

**1. The deadline is sunset: a Mars24 clock at Jezero.** NOVEL — nobody else will have this.
- What: add a sol/date and an EVA start time in LTST. The server computes solar elevation over the excursion with the Mars24 equations (about 60 lines of arithmetic, unit-tested against GISS worked examples). The time budget becomes "back before solar elevation drops below X°", with X a labelled hypothetical. Show the sun-elevation curve under the route profile, and add "start later" or "start earlier" as a rehearsal event.
- Why: Validity (real ephemeris, not an arbitrary 180 min), Impact (it is how real surface operations are planned), Presentation (a clock is legible to anyone).
- Data: Mars24 algorithm (NASA GISS). No downloads.
- Effort: M (A2 math, B1 UI).

**2. Shrinking walkback ring.** Combines #1 with the existing `reach`.
- What: animate the return envelope as the solar clock advances, so the ring visibly contracts toward base, and mark the **point of no return** on the outbound leg. Call it a "walkback limit (Apollo 15 rule)" and cite it.
- Why: this is the one image a jury will remember. Protikriti's rings are static; yours shrink with time and with events. Scores Creativity and Presentation.
- Data: existing `/api/reach`, sampled at N clock times (server-side loop).
- Effort: S–M.

**3. Make the rehearsal event the "Pragyan moment".**
- What: replace the anonymous closure in the demo with a real feature visible in the 5 m CTX image but smoothed out of the 20 m DEM. The narrative: the map could not see it, the crew sees it 30 m ahead, re-plan. Label it "feature below DEM resolution, hypothetical obstruction". Cite Pragyan, 27 Aug 2023, in the demo voice-over, not in the product.
- Why: Validity (shows honestly where resolution runs out), Presentation (a real story with a date).
- Data: existing ortho and DEM. Pick the feature by eye and record its coordinates in `data/sources`.
- Effort: S.

**4. Comms shadow: line-of-sight to base.** NOVEL — nobody else will have this.
- What: compute a viewshed from the base antenna (hypothetical mast height, labelled) over the DEM: 150×150 cells, one ray per cell, which is trivial. Colour route segments where the crew loses direct line of sight to base, add a "time out of contact" metric to each route and to "return now" against "continue", and allow an optional rule: "prefer returns that regain contact soonest". Pragyan lived and died by its relay through Vikram, and Mars EVA crews will too.
- Why: Impact and Creativity; it changes a decision on real terrain.
- Data: CTX DEM only.
- Effort: S (A2), plus S UI.

**5. Second agency, second DEM: HRSC as an independent cross-check.**
- What: resample the HRSC DTM (50 m nominal) to the bundle grid. Show "CTX and HRSC agree within N m (RMS) along this route" and flag cells where they disagree beyond a threshold as lower-confidence terrain. Keep CTX as the routing surface. You already do a rover-versus-orbital check, so this reuses that pattern.
- Why: Validity, plus Relevance with partner-agency judges. Space Apps winners are chosen by NASA and Space Agency Partner experts, and ESA and ISRO are partners ([Space Apps 2025 awards](https://www.spaceappschallenge.org/2025/awards/), [partners](https://www.spaceappschallenge.org/2025/space-agency-partners/)).
- Data: ESA PSA / PDS HRSC DTMRDR for Jezero. Acknowledge the HRSC PI as requested.
- Effort: M (A1).

**6. Flight rules in plain language.** NOVEL. AI used the honest way.
- What: the crew types rules such as "turn back if margin falls under 20 min", "never be out of contact with base for more than 10 min" or "back before sun elevation 10°". The model *only* translates each rule into a schema-validated constraint JSON, which is shown back for confirmation ("I understood: …"). The server then evaluates every route and rehearsal against those rules and returns PASS/FAIL per rule, and the assistant cites that table. The model never produces a number; unparseable rules are rejected with a visible message. Without a key, a small regex grammar covers the five rule types.
- Why: "Whoever uses AI best" means AI that turns intent into checkable constraints, not a chatbot that narrates. It also fits the `trusted_context` rule.
- Data: existing plan and rehearsal outputs, plus #1 and #4 metrics.
- Effort: M (B3 with A3 for the schema).

**7. Sample-return doctrine: "cache and return" as a third rehearsal option.**
- What: alongside "return now" and "continue then return", add "cache the sample at the nearest safe point and return". The light return saves dwell time. It is labelled hypothetical; time saved is the only effect modelled (no mass or speed physics).
- Why: it draws on how MSR actually hedges risk (Three Forks), and it is a clever, low-cost Impact point.
- Effort: S–M. Drop it if time is short.

Ordering if days are short: 3 → 1 → 2 → 4 → 5. Items 6 and 7 only after those.

## 4. Multi-agency data: does it score?

- **Yes, if it changes or checks a decision; no, if it is decoration.** The challenge text says "multiple NASA science missions", so NASA layers stay primary. Partner data adds Validity (an independent DTM) and lands with partner-agency judges. The comms story is naturally multi-agency, because NASA's own relay network depends on ESA's TGO and Mars Express ([NASA MRN](https://science.nasa.gov/mars/mars-relay-network/)). Say that in one sentence.
- **HRSC: take it** (see #5).
- **CaSSIS colour: optional backdrop.** I found no confirmed public Jezero tile in my search, so verify it before promising anything.
- **Tianwen-1 HiRIC: trap.** It famously imaged Perseverance near its landing site ([Xinhua](https://www.news.cn/english/20220324/849308ae69e44232a0df435191450db3/c.html)), but I found no public archive path, and Zhurong is in Utopia Planitia, which is irrelevant to Jezero. At most, mention it in the pitch.
- **MOM MCC: regional context only.** Its resolution is far too coarse for a 3 km box, and I could not verify archive access this round. Using it as a 1-km-scale locator image would be a friendly gesture to ISRO judges, but only if it can be downloaded legally from PRADAN. Do not force it.

## 5. The trap I expect another panellist to push

**A learned or reinforcement-learning path planner ("AI finds the safest route").** It is slower than A* on a 150×150 grid, unverifiable in days, and it destroys your strongest asset: reproducible, tested numbers that the assistant can cite. A juror asking "why this route?" gets "the network decided". ISRO did not let Pragyan pick its own path; ground planned it in short commanded segments.

A close second is SPICE-propagated relay-orbiter pass windows: a week of work for a number the demo cannot verify. The line-of-sight viewshed (#4) gives 80% of the story for 5% of the effort.

---
Not done: I did not re-test the mobile load or run any API flows beyond reading models. The GitHub search for more 2026 entries failed (gh is not authenticated). CaSSIS, MOM MCC and HiRIC archive availability are unverified. The Apollo 15 3.3 km/h walk-home figure comes from OCR, so check the PDF before quoting it.
