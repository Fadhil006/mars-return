# earth-crossdomain — round 1 (Earth "can we still get back?" decision support)

## 1. Three-minute look, through an Earth safety lens

The core object is right. A cost-to-go field from base (`return_field`), "return now vs continue then return", and a turnaround sentence (`web/src/mission/format.ts:31`) are the same skeleton as an aviation point-of-safe-return or a ski-tour turnaround. But every serious Earth tool I know adds three things this one lacks.

1. **Nothing fights the human.** Accidents are not caused by missing arithmetic. They are caused by people who *had* the arithmetic and pressed on: plan continuation bias in aviation, summit fever in mountaineering. In MARS RETURN the server answers first and the human just reads it, so there is no decision to get wrong. The product shows a margin and never tests judgement. Earth decision aids are built around the moment someone wants to keep going.
2. **The answer is not committed before departure.** Wildfire trigger points, ski-tour turnaround times and ETOPS limits are all set *before* the trip, when the person is calm, and then obeyed. Here the "turn around" call only exists after an event is injected and a button is pressed.
3. **There is no risk class a layperson can carry.** Skitourenguru colours each route segment and gives one 0–3 number. ATES gives a 0–4 class. Here the judge gets "+76.34 min" and two near-identical routes (jpl-traverse measured a 1.5% difference). A judge cannot remember a decimal margin. They can remember "this route is Class 3".

Already covered by others, so I don't repeat them: P90 margins, asymmetric/Tobler time, consumables, latency, sunset clock, viewshed, an LLM driving the planner, adversarial red-teaming, the 30 s video cut.

## 2. What Earth does better (cited, mostly 2023–2025)

- **Wildfire trigger boundaries.** Kalogeropoulos et al. (Fire Safety Journal 2023, k-PERIL) and Kalogeropoulos & Rein (Safety Science 2023) define a trigger boundary as the landscape perimeter where *hazard arrival time = evacuation time + a safety factor*. They criticise triggers "arbitrarily defined via landmarks" with no safety factor. That is literally `return_field` contoured against the remaining time. https://portal.research.lu.se/en/publications/integrating-wildfire-spread-and-evacuation-times-to-design-safe-t/ ; NIST ESCAPE/WUI-NITY: https://phys.org/news/2023-08-nist-issues-guidance-emergency-response.pdf
- **Plan continuation bias is still a live cause of accidents.** NTSB link to an Envoy E170 wrong-runway landing at O'Hare (Sept 2024): https://www.flightglobal.com/safety/continuation-bias-highlighted-after-e170s-wrong-runway-landing-at-chicago/166468.article . ATSB VFR-into-weather report, where the "pull" grew as the destination got closer: https://atsb.gov.au/node/10682 . Xu et al. 2023, on the mechanisms behind it: https://jps.ecnu.edu.cn/EN/10.16719/j.cnki.1671-6981.20230409
- **Death on the way back.** Firth et al. (BMJ 2008, Himalayan Database): 56% of deaths above 8000 m happened *on descent*, and late summit time predicted death. https://pmc.ncbi.nlm.nih.gov/articles/PMC2602730 . Follow-up with data to 2024, where descent mortality fell from 3.0% to 0.8%: https://www.eurekalert.org/news-releases/1125559 . **This is the opening line of the video.**
- **Skitourenguru.** Rates every route segment from terrain (slope, size, shape, cover) combined with conditions, gives a 0–3 risk indicator in three colours, and runs on about 10k Alpine routes daily. ISSW 2024: https://arc.lib.montana.edu/snow-science/objects/ISSW2024_O11.9.pdf ; BFU coverage: https://www.bluewin.ch/en/news/skitourenguru-tool-helps-to-choose-safe-ski-touring-routes-li.3069477
- **ATES v2 / AutoATES v2.0** (Statham & Campbell ISSW 2023; Toft et al. NHESS 2024): a 0–4 terrain-exposure class computed automatically from a DEM and published *with its validation F1 score*. https://nhess.copernicus.org/articles/24/1779/2024/
- **Garmin Smart Glide / ForeFlight Emergency Glide Mode.** A cyan reach ring that accounts for terrain and wind. In an emergency it turns amber, re-measures actual performance and auto-selects the best reachable airport by suitability, not just distance. https://www8.garmin.com/manuals/webhelp/GUID-1FA95EDE-BA0A-4000-B109-7E73945389F7/EN-US/GUID-4DA7E6BB-CD32-42AA-B5D7-9485CD40F271.html ; https://avweb.com/aviation-news/foreflight-emergency-glide-mode/
- **SAR lost-person science.** Koester's ISRID ring model (distance from last known point, from about 50k incidents) and Bayesian probability-of-area. Agent-based probability-density maps (arXiv 2412.13317, Dec 2024). https://ica-adv.copernicus.org/articles/5/10/2025/ica-adv-5-10-2025.pdf ; https://arxiv.org/html/2412.13317v1
- **Cognitive forcing.** Buçinca, Malaya & Gajos (CSCW 2021): explanations alone do *not* reduce over-reliance on AI, and in some studies increase it. Making the person commit before seeing the AI answer does reduce it. https://www.eecs.harvard.edu/~kgajos/papers/2021/bucinca2021trust.shtml

## 3. Highest-leverage changes

### E1. "Decide first": a summit-fever test inside the rehearsal. **NOVEL.** Effort S (frontend only).
**What.** At the paused rehearsal moment, after the event lands, *hide* the server's two option cards. Ask the user "Return now or continue?" with a 10 s countdown. Lock the answer in, then reveal the server's `immediateReturn` / `continueThenReturn` numbers. If the user chose "continue" while it was over budget or below reserve, show a one-line verdict: *"Plan-continuation: you pressed on past a no-go. 56% of Everest deaths above 8000 m happened on the descent (Firth 2008)."* The assistant then gives a two-line debrief that cites `trusted_context`. It makes no new calculation, so the rules hold.
**Why it wins.** Creativity and Impact: a judge watching the video gets *tested*, and they remember being caught out. It turns "AI used well" into "AI used to make humans think" (Buçinca 2021), which is the scientifically honest stance. No rival has it: Protikriti and MarsWay both answer for you.
**Data.** The existing `/api/rehearse` response. Nothing new on the server.

### E2. Trigger gates: wildfire trigger boundaries on Mars. Effort S–M.
**What.** At plan time, compute for each outbound route cell the *latest clock time you may pass it*: `T_gate = budget − cost_to_base(cell) − reserve`. Draw 3–4 gates on the route ("Gate B: pass by 01:12 or turn"). Also draw one map contour: the trigger boundary where remaining time equals time-to-base plus the safety factor, which is k-PERIL's construction. During rehearsal, a missed gate turns red and the call becomes "pre-committed turn", with no event needed. This differs from eva-human-factors' cuff card because it is *spatial and drawn on the terrain*, and it is the decision the crew made in advance. That is the antidote to continuation bias.
**Why it wins.** Validity, because it uses a published method with a named safety factor. Presentation, because gates read in 2 s on a 30 s video.
**Data.** The existing cost-to-go field and route polyline. The arithmetic belongs in `mission.py` (owner A2) so the assistant can cite it. It needs one new response field, which means a schema change agreed by A3 and B1.

### E3. Mars Return Exposure Scale (MRES 0–4): the ATES/Skitourenguru pattern. **NOVEL.** Effort M.
**What.** A deterministic, published rule table, *not ML*. Colour every route segment by return state: green = can reach base with reserve; amber = can reach base only by spending the reserve; red = beyond the point of safe return for this budget. Then roll up one route class:
- 0 = all green and passes every closure.
- 1 = all green, with at most one closure failing.
- 2 = some amber segments.
- 3 = more than X% amber, or a single closure strands the crew.
- 4 = any red segment.

Print the rule table in the Evidence tab and label it "hypothetical scale, team-defined, uncalibrated". Have the assistant say "Class 2 because segments 4–6 are amber (trusted_context)".
**Why it wins.** It gives judges one number to remember and compare across sites ("Sid is Class 1, Brac is Class 3"). Because classes vary with budget, it also fixes jpl-traverse's "the stress test always passes" problem. Skitourenguru shows the public trusts segment colouring.
**Data.** The existing margins, `reach` and `stress` results. Thresholds live server-side next to `evaluate_stress`.

### E4. Lost-comms search ring: ISRID on Mars. **NOVEL.** Effort M.
**What.** A rehearsal event "Comms lost at T+47". Mark the last known point and draw where the crew *can be* N minutes later. That is the forward reach from the last known point, bounded by the remaining budget. Shade it with a simple behaviour prior: most likely on the planned return line, then on the lowest-cost path to base, then anywhere in reach. This is Koester's ring and probability-of-area logic, with the "lost person category" replaced by "crew following doctrine". Output a search priority for a rescue rover (Area A/B/C).
**Why it wins.** Impact, because it answers the *second* life-or-death question ("if they don't come back, where do we look?"). Every rival stops at the walk-home.
**Data.** `/api/reach` run from an arbitrary origin (check that `evaluate_reach` accepts one; otherwise this is a small A2 change). The priors are labelled hypothetical. Do not quote ISRID numbers as if they applied to Mars.

### E5. Smart-Glide refuges and an ETOPS rule. Effort M.
**What.** Add one or two *hypothetical refuges* (a cached pressurized rover or a supply depot, labelled) and compute a multi-source cost-to-go: one Dijkstra seeded from every refuge. Then offer an ETOPS-style planning rule: *"never more than 60 min from a refuge"* as a constraint that is shown and can be toggled. In rehearsal, the ring turns cyan→amber like Smart Glide, and "Return" auto-picks the best refuge by margin, not distance. Mark the **equal-time point** between base and refuge on the route.
**Why it wins.** It is a recognisable, proven aviation pattern, and the ETP marker is a single visual beat. Relevance: Mars surface architectures do plan pressurized rovers as refuges.
**Cost.** Touches routing (owner A2) and the schema. Skip it if days are short. E1–E3 come first.

### E6. A 30 s hook taken from Earth's death statistics. Effort S.
Open the video on a black frame: "56% of Everest deaths happen on the way down." Cut to Jezero: "On Mars, plan the way back first." Then E1's countdown and the judge's own answer being checked. This is Earth evidence used as framing, not as Mars data, so Validity is intact.

### Priority
E1 → E2 → E6 (days 1–2, mostly frontend) → E3 → E4. E5 only if A2 has slack.

## 4. The trap I expect the panel to push

**"Train an AI risk model like Skitourenguru / AutoATES."** It sounds like the perfect AI story, and it is a trap. Skitourenguru's model is fitted to thousands of Alpine *accidents* plus daily avalanche bulletins, and AutoATES reports an F1 score against field-mapped classes. Mars has **zero** human traverse accidents and no ground-truth labels. Any learned "risk %" would be invented numbers presented as findings, which breaks the "synthetic never real" spirit and the assistant-must-not-compute rule. Steal the *pattern* (segment colours, one class, a published rule table, honest validation status) and keep the scale deterministic and labelled (E3). The same applies to agent-based Monte Carlo lost-person simulation: with no Mars behaviour data it is decoration, so keep E4's priors as three labelled tiers.
