# viz-ux: round 2

The 30 s cap changes everything. A frame that cannot be read in 5 seconds does not exist. Each idea below is judged by one test: **does it make a frame?**

## 1. Attack

**A1. Earth light-delay framing: eva-human-factors #3 ("latency-shifted envelope") and ai-strategist G ("Ask Earth").**
The scenario is wrong on its own terms. In this scenario the crew talks to a **base on Mars**, not to Earth. A walking crew's go/no-go comes from the local base and the crew itself. That is exactly why lunar-artemis's line of sight to base is the real constraint.
A 4–22 minute light-delay ring answers a question nobody on this EVA asks. It also adds a third hypothetical (comms architecture) on top of the base and the corridor. In a 30 s film a countdown timer is dead air.
Drop both.

**A2. Consumables, metabolic physics and histograms: eva-human-factors #2, #4 and #6.**
These are scientifically sincere and visually invisible. "O2 at return 34%" stacks Minetti energy cost, an unvalidated 0.38 g suit factor, a hypothetical loadout and Monte Carlo spread. The author concedes that the 0.38 g suited-slope combination has **no published calibration**.
That makes a number built on four assumptions, labelled "assumption" four times, on terrain where the median slope is 2.3°. A judge sees a percentage and a tiny histogram, and neither survives a 30 s cut.
If any uncertainty ships, it should be jpl-traverse C1's single P90 band, built from the 27 **real** drives, not from physiology guesses.

**A3. Vision "second look" on 5 m CTX: ai-strategist E.**
At 5 m pixels, ripples and rocks are below resolution. The original JPL story is that Claude *missed* the ripples even on HiRISE. Re-running that failure on imagery 20x coarser invites the judge's first question: "how often is it wrong?" We have no labels to answer it, which is the same trap jpl-traverse names for ML classifiers.
"Closed vocabulary plus DEM cross-check" does not rescue it, because the DEM is 20 m and is the thing that cannot see the features either.

**Concede to lunar-artemis on the sunset clock (isro #1).** At 18°N, a 3 h EVA started mid-sol ends hours before sunset. A sun curve that never binds is another green bar. That repeats the exact disease the facts sheet diagnoses: **the current scenario has no tension**.

## 2. Defend or drop my own

- **HiRISE display terrain (my #2): keep it, but cut the scope.** Planetary-geologist verified that Trek serves the **25 cm HiRISE Jezero ortho as tiles (HTTP 200)**. Draping that imagery is S. The 1 m DTM is M and should only happen if A1 has a spare day. I concede it adds **beauty, not tension**: on terrain this gentle, HiRISE will not change a route. It earns its place in exactly one shot.
- **Context descent (my #1): shrink it.** It gets 3 s in the film, and it falls back to the existing OrbitControls with `autoRotate` if the context tile is not ready.
- **Point-of-no-return ribbon (my #4): keep it, and fix it.** As specified it would be **all green**, because the margin is +76 min. The fix is to colour the ribbon by **two** server facts: whether the crew can still return with reserve, and whether base has line of sight. On the default Sid route that turns 73% of the outbound leg dark. That is the tension.
- **Rover ground-truth images (my #6): merge** into planetary-geologist A ("Orbit said / Rover found").
- **AI camera director (my #7): merge** into ai-strategist A. Each tool call becomes a camera beat.
- **Drop:** the sky, fog and SSAO pass as a headline item. Keep it as a half-day polish task for B2 only. The first-person view stays a trap; eva-human-factors independently agrees.

## 3. Steal

1. **Line-of-sight blind time plus "Safe Haven" (lunar-artemis L2/L3, isro #4, jpl-traverse C7).** This is the best single fact the panel found: "GO +76 min, but 27 min out of contact".
   - **Sharpen:** draw the server's viewshed raster in the 3D view as a **shadow cast by the base mast**. Cells the base cannot see sink into a cool grey-blue wash, so the blind valley reads instantly as the base's "light" failing to reach.
   - It must be the server raster used as a texture, never a client recomputation.
   - The longest blind stretch gets a bracket and a clock: "805 m · 27 min · no contact".
2. **Flight Director agent plus proof strip (ai-strategist A + C, isro #6 flight rules).**
   - **Sharpen:** every tool call shows as a chip ("rehearse ✓", "reach ✓", "viewshed ✓") *and* moves the map, so the agent's reasoning is visible as camera motion.
   - End on the counter "5/5 numbers traced to the planner".
   - Rehearse one live rejection for the live link, not for the film.

## 4. Vote: ranked top 7

1. **Contact-aware return: viewshed blind minutes, longest blind stretch, Safe Haven option** (lunar L2/L3, isro 4, jpl C7). It creates the tension the scenario lacks and nobody has it with return logic. **S–M**
2. **Flight Director agent with visible tool calls and proof strip** (ai A + C, isro 6). It is "AI used best" as the JPL pattern, where the AI proposes and the simulator decides. **M**
3. **Two-fact route ribbon plus point-of-no-return marker and trigger gates** (my #4, earth E2/E3, isro 2). The core question becomes one image. **M**
4. **Orbit said / Rover found per site, with the real rover image and CRISM vs core** (planetary-geologist A, my #6). Multi-mission layering with a confirmed olivine result at Brac. **S–M**
5. **P90 margin calibrated on 27 real drives, plus the "Perseverance as test pilot" replay** (jpl C1 + C5). Validity no rival can copy. **M**
6. **HiRISE 25 cm drape, Jezero context descent, and a one-row header with the map at 65% or more of the width** (mine). It wins the first frame and the live-link first impression. **S–M**
7. **Slope- and direction-aware time (Tobler)** (eva 1, jpl C3). This is parity with Protikriti, but its absence is the first thing a NASA judge attacks. **S–M**

## 5. The 30-second film

Every shot is captured from the real app at 1440p60, with scripted camera poses, burned-in English subtitles, one music bed, and every "Hypothetical" label in frame. All of it is buildable in days if items 1–3 and 6 land.

| # | Time | Picture (real app) | On-screen text |
|---|---|---|---|
| 1 | 0–3 s | Jezero context view eases down into the 3 km box. The HiRISE drape resolves and the low sun rakes across it. Fallback: slow auto-rotate of the 3D terrain. | "Jezero Crater, Mars. Real NASA orbital terrain." |
| 2 | 3–8 s | 3D oblique. The route draws on from Base to Sid. The heads-up display shows **GO · margin +76 min**, with the "Hypothetical base" tag visible. | "The plan says GO." |
| 3 | 8–14 s | The viewshed wash falls across the terrain from the base mast. The ribbon turns dark over 73% of the outbound leg. A bracket marks the blind stretch: **805 m · 27 min · no contact**. | "But for 27 minutes, base can't see you." |
| 4 | 14–20 s | The rehearsal walker pauses mid-blind-stretch. Tap the "Corridor blocked" event. The ribbon recolours, the point-of-no-return marker drops, and the cards "Return now" and "Move to contact, then decide" slide in with server margins. | "Something changes. Can we still get back?" |
| 5 | 20–26 s | Typed question to the agent. Tool chips fire (rehearse ✓ reach ✓ viewshed ✓) while the camera flies to the Safe Haven cell. The proof strip reads "5/5 numbers traced to the planner". | "The AI asks the planner. It can't invent a number." |
| 6 | 26–30 s | End card over the HiRISE terrain: name, positioning line, and the source strip "MRO CTX · HiRISE · MSL RAD · 27 Perseverance drives". | — |

Rule: **open on terrain, never on the form**. The red-team point holds. The control panel does not appear in the film at all.

## 6. Positioning line

**"Before you walk on Mars: can we still get back, and will base hear us on the way? A planner checked against 27 real Perseverance drives answers, and an AI that is not allowed to invent a number explains."**
