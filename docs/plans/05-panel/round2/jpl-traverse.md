# jpl-traverse: round 2

## 1. ATTACK: the three weakest proposals

**A1. isro #1, "the deadline is sunset" (Mars24 clock).** It is a non-event, and I side with lunar-artemis using numbers. Jezero is at 18.4°N and Mars' solar declination ranges over ±25.2°. From cos H0 = −tanφ·tanδ, daylight runs from about 10.8 h to 13.2 h, so sunset falls between roughly 17:25 and 18:35 LTST. A 3 h EVA from 10:30 to 13:30 LTST ends at least 3.9 h before sunset in every season. The constraint only binds if a user deliberately starts after about 14:30, which makes it a scheduling footnote, not a route constraint. The isro proposal costs M effort (60 lines of ephemeris plus tests plus UI) for a curve that stays flat in every demo.

**A2. eva-human-factors #2 and #3: O2-percentage walkback and the Earth-latency envelope.** Both are false precision on top of a missing calibration. The eva panelist concedes that 0.38 g suited slope walking has **no** published calibration. Then "O2 at return: 34%" is an integer derived from a made-up loadout times an uncalibrated cost. It also cannot differ from minutes here: with a median slope of 2.3°, metabolic cost ≈ constant × distance, so the O2 bar is the time bar in a costume. The latency envelope models the wrong link, as lunar-artemis said. At Mars one-way light time (about 4–22 min), Earth is not in the go/no-go loop at all, so the "GO arrives stale" shading answers a question no flight rule asks. Both cost M effort and are invisible in 30 s.

**A3. ai-strategist E (Claude vision "second look" at the 5 m CTX corridor) and viz-ux #2 (HiRISE 1 m for 3D display while routing stays on CTX 20 m).**
- **E has no ground truth.** Meter-scale ripples are at or below CTX pixel scale, and the proposer already promises never to feed the output into routing. That makes it a decorative, unverifiable overlay.
- **viz #2 is self-sabotage.** A 1 m mesh under a 20 m route shows judges the route walking straight over ridges the planner cannot see. Either route on HiRISE (my C2, M effort) or don't show it in 3D. Use the 25 cm HiRISE *basemap* (planetary D, S effort) instead. It looks professional without exposing the planner's resolution.

## 2. DEFEND or concede

- **C5 "Perseverance test-pilot replay": concede it is NOT novel.** Protikriti already benchmarks against Perseverance drives, so I drop the NOVEL tag. The *number* is still the defence: per-drive ratio p10–p90 0.88–1.29 on 27 drives.
- **C1 calibrated P90 margin: keep, retitled.** Land & Stand already has a "round-trip probability field", but it comes from crew deconditioning. Ours would be the only error band **measured against real Mars drives**. It also kills the "+76.34 min" false precision. Effort S: 500 seeded draws on a 150×150 grid run in under a second.
- **C3 Tobler, asymmetric: keep as table stakes, not as a differentiator** (Protikriti has Tobler). It is S effort, and a NASA judge's first objection is "climbing is free".
- **C2 HiRISE DTM routing: demote to "if time".** Tension now comes from the viewshed (73% of the Sid outbound leg is blind), not from slope. Routing on 1 m data is M–L effort, and nothing about it shows in a 30 s video.
- **C4 Séítah terrain-class layer: drop.** The Stack et al. 2020 map is raster-only, and SIM 3464 carries a 100–200 m offset, which is fatal in a 3 km box. CRISM mineralogy is not trafficability.
- **C7 viewshed: vindicated.** The measured 25.6% coverage and the 805 m (about 27 min) blind stretch on a "GO +76" route are the tension the scenario was missing. Sightline already shows blind *zones*. Our edge is blind *minutes* in the go/no-go decision and in the return logic.
- **C6 "AI proposes, physics disposes": keep, merged** into ai-strategist A+C and isro #6.

## 3. STEAL: the two best

**S1. lunar-artemis L3, the "Safe Haven" field: minutes to regain contact.** Sharpen it in three ways:
- Make it a multi-source run of the existing `return_field` (seeded from every visible cell), so it costs about 20 lines.
- Add it as the third rehearsal option, "move to contact (N min), then decide", next to return now and continue.
- Feed the stress test so a closure can fail on *"survivable but silent > X min"*. This is what finally makes stress fail on gentle terrain: tension from terrain occlusion that a slope map can never produce.

**S2. planetary-geologist A, "Orbit said / Rover found".** Brac is CRISM olivine (6/9 high-confidence pixels), confirmed in situ by Perseverance as an olivine cumulate (Liu 2022). Nobody else does an orbit-versus-ground comparison. Sharpen it by making it *decision* data, not a card. In the rehearsal triage, rank "drop Issole, keep Brac" using a visible rule: a stop where orbit and ground disagree, or where orbit is silent, is where a human adds the most. The server ranks the stops; the AI only explains the ranking.

## 4. VOTE: ranked top 7

1. **Blind-minutes flight rule plus the Safe Haven contact field** (lunar L2/L3, isro #4, my C7). It turns the default GO into AMBER on real terrain; the only tension we have that is measured on the DEM. **S–M**
2. **Point-of-no-return ribbon with trigger gates** (viz #4, earth E2, eva #5 cuff card). The thesis as one glanceable image, and it recolours live on an event. **S–M**
3. **AI flight director: tool trace, proof strip, one live rejection** (ai A+C, isro #6, my C6). It follows JPL's December 2025 pattern: the model picks the inputs and the planner computes the answer. **M**
4. **Orbit said / Rover found** (planetary A, plus B triage if time allows). A unique ground-truthed science reason to walk. **S–M**
5. **Margins with a P90 band calibrated on 27 Perseverance drives** (my C1, eva #6). It ends the false precision with a measured error. **S**
6. **Tobler, grade-signed, asymmetric return** (eva #1, my C3). It closes the first NASA objection. **S**
7. **HiRISE 25 cm Trek basemap, cached locally** (planetary D). Every frame of the video looks professional. **S**

## 5. THE 30-SECOND FILM

| # | Time | Shot |
|---|---|---|
| 1 | 0–4 s | LROC image of Apollo 14's tracks stopping short of Cone's rim. Caption: *"1971: turned back 30 m from the rim. By the clock."* |
| 2 | 4–9 s | HiRISE-based Jezero oblique. Sid selected, the route draws on, card reads **GO +76 min**. |
| 3 | 9–15 s | The viewshed lights up and 73% of the outbound leg greys out. The card flips to **AMBER: 27 min out of contact**, and the Safe Haven arrow appears. |
| 4 | 15–21 s | The walker pauses at T+47 and an event lands: "corridor blocked". The ribbon recolours, the point-of-no-return marker drops, and the "Return now" vs "Continue" cards show their P90 bands. |
| 5 | 21–26 s | Typed: *"Push on to Brac or turn back?"* Tool-trace cards (rehearse → reach → contact) stream in. The answer shows chips: **"7/7 numbers traced to the planner"**. |
| 6 | 26–30 s | Brac card: **Orbit: olivine (CRISM) · Rover: olivine cumulate (Perseverance)**. End title with the positioning line. |

Hypothetical labels (base, corridor) stay visible in frame.

## 6. Positioning line

**"MARS RETURN tells a crew the minute they must turn back, how sure that minute is (measured against Perseverance's own drives), and whether base will hear them on the way — and its AI cannot say a number the planner did not compute."**
