# Round 2 — eva-human-factors

The moderator's facts kill the current demo: median slope 2.3°, 8/8 closures survivable, lower-slope route ≈ shortest route, and GO +76 min. **Nothing in the scenario can fail, so there is nothing to decide.** Every proposal must be judged on one test: does it create a real "turn back" moment on this gentle terrain, inside a 30-second film? Most don't.

## 1. Attack

**A. isro #1, the Mars24 sunset clock.** Lunar-artemis is right, and I'll put numbers on it. At 18.4°N near equinox, a 3-hour EVA that starts at 10:00 LTST ends at 13:00 with the sun around 60° above the horizon. The sun sits more than 20° above the horizon from roughly 08:20 to 15:40 LTST in every season at that latitude. To make sunset bind, the team would have to *choose* a late start, which means the demo invents its own tension. Using this as a constraint costs M effort for a label. Keep a single "sun elevation at return: N°" readout and spend nothing more on it.

**B. red-team, the real May 2024 SPE "collapsing the envelope".** That event was measured by Curiosity at Gale, not at Jezero. More to the point, a solar particle event does not shrink a walking envelope. The physical action is "shelter within X min", and X is a number the team would make up. A real NASA dataset would end up driving a made-up consequence, presented as if one followed from the other. A Validity judge from SRAG will take that apart. RAD stays as context, as I said in round 1. It is not a trigger.

**C. viz-ux #2, HiRISE 1 m for display with CTX 20 m for routing.** This is the worst of both. The 3D view would show boulders and ridges that the planner cannot see, so the route will visibly run through features it ignores. In a 30-second shot that reads as "the planner is blind". The honest version is jpl C2: use HiRISE to *conservatively coarsen* routing slopes, or don't touch it. The same goes for the sky shaders and SSAO in viz #3: they cost days and earn no points.

(Honourable mention: earth E4, the lost-comms search rings. They need M effort, rest on behaviour priors with zero Mars data, and only matter after the scenario has already failed.)

## 2. Defend or concede (my round-1 items)

- **#3 Earth light-time envelope: conceded to lunar-artemis.** Earth is out of the tactical loop at 4–24 min one way. A walkback decision lives between the EV crew and the base IV crewmember. Artemis already moves authority to IV at 5–14 s of delay. But the concession cuts *against* lunar's own framing of the AI. If Earth can't answer, the onboard answer must be self-checking, and that is the verified-numbers gate. So keep latency as **one caption line in the film**, not a feature. The link to model is base to crew line of sight, which I steal below.
- **#2 consumables / O2 %: dropped as a headline.** Magurin already ships a Santee metabolic model. There is also no Mars suit spec, so an "O2 34%" figure is a hypothesis built on a hypothesis. Keep the Apollo 1440 BTU/h walkback rate as a cited footnote only.
- **#1 Tobler, direction-aware time: kept, downgraded.** On 2.3° median terrain the uphill/downhill asymmetry is a few percent. It's a credibility fix ("why is downhill as slow as uphill?"), not a demo beat. Merge it with jpl C3, which uses Apollo walking rates.
- **#6 Monte Carlo: merged into jpl C1.** Theirs is better because it is calibrated on 27 real drives.
- **#4 degraded-crew walkback: defended, and promoted.** It's the cheapest way to create real tension. "Crewmate injured: half pace" is just `speedMPerMin/2` passed to the existing `/api/reach` and `/api/rehearse`. That's S effort and needs no schema change beyond a labelled preset. The Apollo walkback and rideback logic is the precedent, and it is the case MCC actually plans to. LIFELINE has a "Rover fails" button. We go further: we show *where along the route the governing case flips* and recolour the ribbon under it. Without this, the 3 km box never says no.
- **#5 cuff card: kept, merged** with lunar L4 (Map Book) and earth E2 (trigger gates).

## 3. Steal

1. **lunar L2 + L3: blind minutes, then minutes to regain contact.** It is the FOD constraint word for word, and it is the only *measured* tension on this terrain: the default Sid route is blind for 73% of the outbound leg, with an 805 m blind stretch, while the screen shows GO +76. Sharpen it in three ways. (a) Compute blind minutes **under the degraded-crew case**: an injured crewmember in a blind valley is the real nightmare. (b) Add "move to contact, then decide" as the third rehearsal card. (c) Label the mast height and say that a real architecture would add a rover relay, so this is the worst case.
2. **earth E2 + viz #4: trigger gates and the point-of-no-return ribbon, as one feature.** Gates drawn on the terrain *are* the rows of the cuff card. Sharpen it: compute each gate time against the **governing case**, which is the tighter of the healthy and degraded walkback, as Apollo did. Print the same gates on the cuff card: "Gate B: pass by T+0:52 or turn."

## 4. Vote: top 7 across the panel

1. **Line-of-sight blind minutes and regain-contact field** (lunar L2/L3, isro #4, jpl C7). It turns GO +76 into amber on real terrain and is the FOD constraint verbatim. **S–M**
2. **Point-of-no-return ribbon, trigger gates and a printable cuff card** (viz #4, earth E2, lunar L4, eva #5). The thesis becomes one image plus a real flight product. **S–M**
3. **Degraded-crew governing case** (eva #4). Half-pace walkback, showing where it flips; the only cheap source of a "no". **S**
4. **"Orbit said / Rover found" per site** (planetary A). CRISM olivine at Brac, confirmed by Liu 2022. It's multi-mission, ground-truthed and nobody else has it. **S–M**
5. **Verified AI flight products** (lunar L4, ai C, eva #7). The model drafts the call-up and the Map Book prose, the numbers are server-filled, and a proof strip shows one draft rejected live. **S–M**
6. **AI red-teams the plan** (ai B on top of ai A's tool layer). The model searches for the cheapest event plus case that breaks the return; the server scores it. This is AI used to falsify, now that blind zones and the degraded case give it something to find. **M**
7. **Direction-aware Tobler time with P90 margins** (jpl C3 + C1, eva #1/#6). Shows "with 90% confidence" instead of +76.34. **S–M**

Cut list: sunset clock as a constraint, SPE trigger, HiRISE as display only, first-person view, Earth countdown, O2 %.

## 5. The 30-second film (every number read from screen, shown here as N)

1. **0–4 s.** LROC image of Apollo 14's tracks ending short of Cone's rim. Caption: "1971. Turned back by the clock." (lunar L1)
2. **4–10 s.** Jezero in 3D, real CTX terrain. The route Base → Brac draws on, with the ribbon green and gates A–C ticking along it. Caption: "Real terrain. Real Perseverance sample site. Plan the way back first."
3. **10–15 s.** Blind-zone shading drops over the route. The badge flips from GO to amber: "N min out of contact with base."
4. **15–21 s.** Rehearsal paused at Gate B. Tap "Crewmate injured: half pace". The envelope shrinks, the ribbon goes red past the gate, and three cards appear: Return now / Move to contact / Continue.
5. **21–27 s.** The AI writes the call ("Turn back now; contact in N min; margin N min"). The "N/N numbers verified against planner" chips light up, and a struck-through rejected draft flashes once.
6. **27–30 s.** The printed cuff card, then the end card: "Earth is 20 light-minutes away. The answer has to be onboard, and checkable."

## 6. Positioning line

Every other Marswalk planner tells you how to get there. MARS RETURN tells you exactly where you must turn back when a crewmate is hurt and base can't hear you, and proves every number it gives you.
