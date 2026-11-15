# red-team-competitor — round 2

On 15 Nov I grepped 18 rival READMEs (saved in scratchpad/rival-readmes/). Half of this panel's "NOVEL" labels don't survive that check.

## 1. ATTACK (three weakest)

**a. isro #1 "Sunset is the deadline, Mars24 clock": NOT novel and not binding.** Three rivals already ship it:
- Protikriti: "daylight", Mars24.
- Red Route (github.com/curry06240624-dev/red-route): "sun height (NASA GISS Mars24)" next to light time and GO/CAUTION/NO-GO.
- RedStep (redstep.vercel.app): the same.

Lunar-artemis is right that a 3 h mid-sol EVA at 18°N never meets sunset, so the clock never binds. M effort for a curve that never changes the answer. Drop it.

**b. planetary-geologist B "science triage under contingency, nobody else does it": false.** LIFELINE's README step 3: "Press **Running late**. The gate at stop A… switches to plan B (skip B)… then plan C (go home)". It has "skip the lowest-science stop" decision gates, live, with slides. Build triage now and you look like LIFELINE's copy, with less polish. It only survives if the science value is *ground-truthed* (see steal #1). A gate on a made-up score is what they already have.

**c. eva-human-factors #2 / #6 "O2 consumables walkback + Monte Carlo P(return)": table stakes, and it inflates false precision.**
- Oxygen or consumables appear in 10 of 18 READMEs (OlympusTrail, MarsWeave "suit physiology", LIFELINE "suit time", Red Route "suit air with turn-back point", AresNav…).
- Land & Stand and MarsWeave already show probabilities.
- Swapping "+76 min" for "O2 34%" built on a *hypothetical* suit loadout adds another hypothetical layer to a screen that already drowns in them.

Keep jpl C1's P90 band, because it rests on the 27 real drives (p10–p90 0.88–1.29). Drop consumables.

**Also dead:**
- **ai-strategist A ("Flight Director" agent driving the planner) is no longer NOVEL.** Magurin's marswalk-planner already has an "AI assistant [that] edits the plan through the same actions as the UI" (OpenAI). What nobody has is the **number check**. Magurin's README has no verification of any kind. Pitch the gate, not the agent.
- **eva #3 latency:** AresNav simulates the "~14m 18s one-way light-time delay" and RedStep shows "Earth light time". Only the latency-*shifted envelope* would be new, and it is a 2 s visual nobody understands in a 30 s film.
- **viz-ux #6 rover raw images and eva #5 cuff card:** Red Route has "16 Perseverance photos per stop" *and* "a one-page printable cuff card". Both are taken.

## 2. DEFEND / CONCEDE (my round 1)

- **Concede the mobile stall.** The moderator verified it was a headless artefact (<4 s real load). Struck.
- **Concede the solar-storm replay as the headline event.** RAD data is from Gale, not Jezero, and Sightline owns the May 2024 storm story. Using it would look derivative and stretch Validity. Downgrade it to a labelled "what if" at most.
- **Defend "rehearsal is the opening shot".** The moderator's own fact makes my case: the terrain is so gentle that the routes differ by 1.5% and all 8/8 closures pass, so **the default demo has no tension at all**. The fix is not to fake tension. It is to find the real constraint that binds. Lunar-artemis found it: the default Sid route is **out of sight of base for 73% of the outbound leg, with an 805 m (~27 min) blind stretch, yet shows GO +76 min.** That is the honest drama.
- **Defend "trap = breadth race".** Even stronger now: THEMIS TI, SIM 3464 and CRISM summary layers are in Protikriti, ARES and MarsWeave. Breadth gets no credit.

## 3. STEAL (and sharpen)

1. **planetary-geologist A "Orbit said / Rover found"** (CRISM Parente olivine at Brac → Perseverance olivine cumulate, Liu 2022). This is the only verified idea no rival has. A grep for olivine/ground-truth hits Protikriti only, as a plain CRISM layer. *Sharpen:* make it decide something. Each stop gets a "Why send a human?" verdict: *orbit confirmed* → the rover did it, so lower the human priority; *orbit silent* → a human adds information. That turns the science table into a reason to walk, and a reason to *skip* a stop under contingency. That is triage LIFELINE can't copy, because their score isn't grounded.
2. **lunar-artemis L2 + L3: line of sight and "move to contact, then decide".** Sightline has blind *fractions*. Nobody has blind *minutes on the return leg* or a "minutes to regain contact" field. *Sharpen:* this is the GO that turns amber in front of the judge. Same route, "GO +76 min" → "AMBER: 27 min out of contact, limit 10 (hypothetical)", then a third card: "move to contact (N min), then decide". Pair it with ai-strategist C, the proof strip: the AI's call shows "7/7 numbers traced to planner output".

## 4. VOTE: ranked top 7

| # | Proposal | Why | Effort | Rival already has? |
|---|---|---|---|---|
| 1 | **Line-of-sight flight rule + "minutes to regain contact" option in rehearsal** (lunar L2/L3, jpl C7, isro #4) | The only real constraint that binds on this gentle terrain; flips the default GO | S–M | Sightline: blind share only. No clock, no return option |
| 2 | **Visible number-check: AI flight-director call with proof strip** (ai C + D, eva #7, lunar L4 prose) | The "AI used best" thesis as something a judge can see; Magurin's agent has no gate | S | No |
| 3 | **"Orbit said / Rover found" + human-value verdict per stop** (geologist A) | The one verified orbit-vs-ground result in the field; Validity + Relevance | S–M | No |
| 4 | **Point-of-no-return ribbon on the route, recolours on an event** (viz #4, isro #2, earth E2 gates) | The thesis as one image for the film | M | LIFELINE has a shrinking zone, not a per-metre route ribbon |
| 5 | **P90 margin from the 27-drive calibration, whole minutes** (jpl C1 + C8) | Kills false precision with *measured* Mars data | S–M | No (Land & Stand's probabilities are physiology, not rover-calibrated) |
| 6 | **Context descent + one-row header, map ≥65%** (viz #1, #5 slim, #8) | Kills "3 km box" and "first screen is a form" | M | Land & Stand / Protikriti have globe descents: parity, not novelty |
| 7 | **"Decide first" 10 s summit-fever test before the reveal** (earth E1) | Makes the judge *play*; cheap; nobody has it | S | No |

Dropped: Mars24 sunset, O2 consumables, latency envelope, rover photo billboards, cuff card (all taken or non-binding), HiRISE DTM swap (M–L, changes no decision), adversarial red-team agent (nice, but after #2).

## 5. THE 30-SECOND FILM (≤6 shots, all buildable in days)

1. **0–4 s.** Context descent into Jezero, box outline. Text: "Jezero Crater. Real orbital terrain. Real Perseverance sites."
2. **4–9 s.** Pick Brac; card flips: "Orbit said: olivine. Rover found: olivine cumulate." Text: "Where orbit and rover agree."
3. **9–14 s.** Route draws; 3D walker moves; header shows "GO +76 min".
4. **14–21 s.** Ribbon turns amber along the blind stretch; viewshed shading appears. "27 min out of contact with base." 10 s "Return or continue?" prompt flashes (E1).
5. **21–27 s.** Three cards: Return now / Continue / Move to contact, then decide. The AI call types out with a "6/6 numbers verified against the planner" strip.
6. **27–30 s.** End card: positioning line + "Model results. Hypothetical scenario. Not certified." + URL.

Subtitled, no voice dependency. It fits the ≤30 s rule.

## 6. Positioning line

**"Every team draws the way home; MARS RETURN shows where you lose contact with home, and an AI whose numbers are checked tells you what to do about it."**
