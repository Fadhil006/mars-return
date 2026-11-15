# Round 1 — eva-human-factors (EVA flight director / human-factors view)

## 1. Three-minute look: what an EVA officer would say

**"It plans in minutes. We plan in consumables."** The whole safety argument is `distanceM / speedMPerMin` (server/mission.py:15, :32, :111; web/src/mission/state.ts:184). That means:

- **Uphill and downhill cost the same.** The route already returns `ascentM` and a per-cell elevation `profile` (server/routing.py:175-189), and then the time model throws them away. Most excursions out of a base on a crater floor or delta are downhill out and uphill back. The return leg, the one the product exists to protect, is the leg it underestimates most. A judge with field experience will catch this in about ten seconds.
- **30 m/min (1.8 km/h) is a lone number with no source.** It is labelled "Assumption", which is honest, but nothing says where it came from or how wrong it could be. Apollo walkback planning used 3.3 km/h at 1440 BTU/h (~420 W), with a 30-minute consumables reserve on top (Apollo 15 traverse memo, ALSJ). Apollo crews also used consumables faster than predicted (NASA NTRS 20210024317).
- **The time "budget" isn't tied to anything physical.** No real suit has a 3-hour budget. A suit has O2, CO2 scrubbing capacity, cooling water and battery, and each one drains in proportion to **metabolic rate**, and metabolic rate depends on slope, load and gravity. A 20-minute reserve is padding, not a contingency case. Apollo defined *two* cases: walkback (rover failure) and rideback (PLSS failure on the backup O2 supply, 0.95 h). Whichever was tighter at that point set the limit.
- **No crew, no failure case.** There's no "one crew member injured, half speed" and no "suit anomaly, switch to backup". "Can we still get back?" is answered for healthy walkers only, and that's the question nobody in MCC asks.
- **No Mars communication delay.** On Mars, the ground's answer to "can we get back" arrives 8–48 min round-trip later. The rehearsal pauses the world. The real decision is "by the time Houston's GO reaches you, will it still be true?" That's the single most Mars-specific thing about this challenge, and it's missing.
- **The output isn't how crews consume plans.** Crews fly from a cuff checklist and a timeline with *must-leave-by* times (JETT3 products: cuff checklist + Map Book; Playbook in NEEMO/BASALT). The product gives a margin in minutes on a dashboard. Nobody on EVA reads a dashboard.

Credit where it's due: the mid-route rehearsal (return now vs continue then return), the return envelope and the closure stress test are the right *questions*. Protikriti's "walk-home card" and MarsWay's "safer route" answer an easier version of them. The engine is sound. The physics underneath it is the weak point.

## 2. What real tools and research do better (2023–2026)

- **NASA JSC Crew State and Risk Model, traverse module.** It estimates the metabolic cost of a planned traverse with a field-calibrated Pandolf/Santee load-carriage-on-slope equation: inputs are body mass, load, speed, *grade %* and a terrain coefficient η, plus a metabolic delay term. The field model fit measured K5 data better than the lab model (regression slope 0.95 vs 0.50). Kim et al., IEEE EMBC 2024: https://ntrs.nasa.gov/api/citations/20240001423/downloads/IEEE%20EMBC%202024.pdf
- **Apollo walkback/rideback envelope.** Return distance is limited by consumables at a fixed walking metabolic rate after a 30-minute reserve, and the governing failure case switches partway through the EVA. https://www.nasa.gov/history/alsj/a15/a15.trv1prep.html
- **MIT SEXTANT.** Computes the energy-optimal path and the walkback from *every point on the traverse*, and links thermal load and power to consumables. https://dspace.mit.edu/entities/publication/242ddd93-f93d-4ca4-944f-281cdf25ace6 ; walk-back limits from slope with the Virtual Spacesuit: https://ttu-ir.tdl.org/handle/2346/74208
- **Artemis EVA development process.** Roles (EVA FCR, Ground IV, Science MPSR) and final products. It moves from directive EVAs to discovery-driven ones, so plans must stay flexible. Caswell, Kostak, Young, ASCEND 2025: https://ntrs.nasa.gov/api/citations/20250006063/downloads/Caswell%20Kostak%20Young%20ASCEND%202025%20Rev%206-11-25.pdf ; JETT5 (2024) science ops: https://ntrs.nasa.gov/citations/20250000177
- **Comm-latency research.** BASALT's timeline drew "now", "now minus one-way light time" and "now plus round trip" lines. NEEMO found text and data beat voice under delay. NASA HRP's 2025 review covers 15 latency studies. https://ntrs.nasa.gov/api/citations/20250000703/downloads/2025%20HRP%20IWS%20Comm%20Delay.pdf ; https://ntrs.nasa.gov/api/citations/20170002363/downloads/20170002363.pdf
- **Heart rate to metabolic rate during EVA.** Individual crew regressions reach R² > 0.82; it's used to track consumables live. https://ntrs.nasa.gov/citations/20210024317
- **Slope energetics.** Minetti 2002 gives a cost-of-walking polynomial in grade. Its minimum is at about −10%, and it's strongly asymmetric. https://iris.unibs.it/retrieve/ddc633e4-3c03-4e2e-e053-3705fe0a4c80/Minetti%20JAP%202002.pdf. Simulated 0.38 g walking measured VO2 at ~0.68 L/min vs 1.00 L/min at 1 g (Brown et al. 2018): https://kclpure.kcl.ac.uk/portal/en/publications/the-metabolic-cost-of-walking-in-simulated-martian-gravity-and-it/
- **Another entry found:** "MarswalkAI" (DEV post; MOLA, HiRISE, CRISM, THEMIS thermal inertia for trafficability, MCS dust). https://dev.to/walsal201/astromind-4ji4. More data breadth than we have, but there's no sign of a physiology or walkback model.

## 3. Highest-leverage changes

**1. Slope-aware, direction-aware time (fixes the core validity hole). S–M.**
Swap constant speed for a published grade-to-speed relation, applied per profile segment and per direction. Tobler's hiking function is v = 6·exp(−3.5·|tan θ + 0.05|) km/h, scaled by a labelled "suited, 0.38 g" factor. The return leg then gets a different time from the outbound leg. The data is already there: the existing `profile` and the DEM slope. Make the change in `_assessment` and in `return_field` edge weights. In the reach field, the weight must be the cost of moving *toward* the base, so reverse the edge direction. Then show "outbound 41 min / return 58 min, same path" on screen. That one line kills the obvious objection. *Validity, Impact.*

**2. Consumables walkback, not a minute budget (Apollo method, Mars numbers). M.**
Integrate metabolic power along the path. Use Minetti C(i) J/kg/m, or the Santee/Pandolf form the JSC traverse model uses, times system mass and g-scaling. Turn that into O2 used (≈ 20.1 kJ per L O2), CO2 produced and cooling water. Compare against a *hypothetical, labelled* suit loadout, for example O2 for 8 h at 420 W (the Apollo walkback rate, sourced). The headline becomes "**O2 at return: 34% (reserve floor 30 min at walkback rate)**" instead of "margin 22 min". Keep minutes as a secondary readout. Every constant goes in the Evidence tab with its citation. Nothing new is needed in `trusted_context`: the server computes, and the assistant cites. *Validity, Relevance.*

**3. NOVEL — Latency-shifted return envelope: "Will the GO still be true when it arrives?" M.**
Add a one-way light time input. The default is the real Earth–Mars distance on the demo date, computed from JPL Horizons, or a fixed table if offline. Shade three envelopes: where the crew can return *now*; where it can still return *if it keeps walking until Earth's answer arrives* (now + RTT along the planned path); and the cells it has already left behind. The rehearsal card adds a row: "Earth's reply lands at T+1:47. By then you are here, and return margin is X." This is the BASALT latency-line idea moved onto the map. No competitor has it, and no other challenge theme is as Mars-specific. *Creativity, Relevance.*

**4. NOVEL — Two-case envelope: walkback (healthy) vs. degraded crew (assisted pace / backup O2). M.**
Run the reach field twice with two labelled contingency cases. Case A: one crew member injured, at 50% speed and ×1.5 metabolic rate. Case B: suit anomaly on the backup supply with a fixed duration. On the map, show the *tighter* of the two envelopes, plus the point along the route where the governing case flips, exactly like Apollo's rideback-to-walkback crossover. Then add the line "the stop you chose is outside the degraded-crew envelope", which reads like real ops. *Validity, Impact.*

**5. "Turn-around time" and the cuff card (the product crews would actually carry). S.**
From the existing rehearsal arithmetic, compute per station: latest departure time, the point of no return on the outbound leg, and the time when the return leg must start. Export a printable cuff checklist in a wrist-card format with station, arrive-by, leave-by, the governing constraint and the walkback heading. The mission report already exists, so this is formatting plus a few derived fields from `/api/rehearse` and `/api/reach`. In the demo, hold it up. Every NASA judge has seen a cuff checklist. *Presentation, Impact.*

**6. Uncertainty instead of a single margin: P(return with reserve). M.**
Run Monte Carlo over speed factor, metabolic rate and suit loadout (Apollo flew over-predicted consumption, so the spread is justified and sourceable). Report "returns with full reserve in 94% of 2,000 draws" plus the 5th-percentile margin. Draw it as a small histogram on the route card. It's server-side, deterministic with a seeded RNG, and tested. It's also the honest answer to "nothing here is certified". *Validity.*

**7. AI as a latency-aware Ground IV, not a chatbot. S–M.**
The assistant drafts the *uplink message* in flight-control form: a time-tagged message with GO/NO-GO, the governing constraint, leave-by time and a cited source chip. It's written to be valid at **arrival time**, not send time. The text-over-voice finding from NEEMO justifies the format. Every number comes from `trusted_context`, including the new latency, consumables and contingency fields, so the existing number and citation check still enforces honesty. The visible-AI moment is a well-formed ops message under delay that a reviewer can check line by line. *Creativity, "AI used best".*

**8. (Optional) Least-energy objective. S.**
Make it a third route mode using the Minetti cost as the edge weight, next to shortest and lower-slope. It's visibly different on the delta scarp, and it's what SEXTANT optimizes. Skip it if time is short. Items 1–2 matter more.

Order if days are short: **1 → 5 → 3 → 2 → 4**. Item 1 is a few dozen lines and removes the one objection a NASA judge will raise first.

Guardrails: label every physiological constant "hypothetical crew/suit assumption" and cite it. Say that 0.38 g suited slope walking has **no** published calibration. Lab data covers 0.38 g on the flat and 1 g on slopes only, so the combined factor is an assumption, shown as a band, not a number.

## 4. Trap from another discipline

**First-person / VR "walk the route" immersion (from the graphics or UX side).** MarsWay already has a first-person EVA view, and Protikriti has rover street view, so it isn't novel. A 20 m DEM looks like mush at eye height, so it *undercuts* the Validity story. And it eats the days needed for items 1–5. A judge remembers "it told me where I can't get back to under a 22-minute light delay", not a blurry walk-through. A close second: treating the **radiation estimate as a go/no-go driver**. A few hours of surface dose (~0.6–0.7 mSv/day from MSL RAD) is negligible for one EVA unless there's an SPE. Present it as context, and don't let it crowd out consumables, which do decide the walkback.
