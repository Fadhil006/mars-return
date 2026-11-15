# lunar-artemis — round 2

Starting fact: on this terrain slope does not bind, the stress test never fails, and every stop is GO. Any proposal that adds precision to a scenario with no tension is wasted effort. Only one constraint measured so far actually bites, and that is line of sight to base.

## 1. Attack

**A. ai-strategist B, "Red-team this plan" with LLM adversarial search.**
- There is nothing for it to find. 8/8 closures survive at every stop, with a median slope of 2.3°.
- The search space is 150×150 cells times a handful of event types. Brute force covers it in about a second (the stress grid already does this).
- Using an LLM as a search heuristic over a space you can enumerate is theatre. A JPL judge will ask "why not just enumerate?", and the only honest answer is "to show AI".
- The search does become interesting if the oracle includes contact (blind minutes). Then the cheapest failure is real: "the 805 m blind stretch on the Sid leg". Even so, enumerate first. The LLM only *explains* the worst case.

**B. eva-human-factors #3 and ai-strategist G, the Earth light-time envelope or "Ask Earth" countdown.**
- This models the wrong link. NASA's own 2026 review (Elston et al., IEEE Aero) moves EVA authority to the IV crewmember already at the Moon's 5–14 s delay.
- At 4–22 min one way, Earth is not in the decision loop for a 3 h walk at all. The real-time link is EV crew to base, and the base cannot see 73% of the Sid outbound leg.
- A countdown to Earth is a pretty animation of an irrelevant number, and it cannot fit in 30 s next to the real story.

**C. isro #5, HRSC cross-check (and, harsher, #1, the sunset clock).**
- HRSC is a 50 m DTM checking a 20 m one, on a floor with 22 m of total relief. It cannot flip a decision and cannot be seen in a film. Partner-agency goodwill does not earn points if it is invisible.
- **Sunset, with numbers.** At 18.4°N with Mars' 25.2° obliquity, cos H = −tan φ·tan δ gives day lengths of **10.8–13.2 Mars hours**. The earliest sunset is about **17:24 LTST**. A 3 h EVA meets sunset only if it starts after about 14:20 LTST, and no one would plan that.
- At the lunar south pole the Sun sits about 1.5° above the horizon, so illumination *is* the route (VIPER planned shadows to 8 h). At Jezero it is a label on the timeline. Concede it to a caption.
- Runner-up: the eva #2 claim "O2 at return: 34%" built on an invented suit loadout. It replaces one hypothetical number with a falsely precise one. Use the Apollo walkback rule in minutes instead (3.3 km/h, 20% pad, ALSJ planning document).

## 2. Defend or concede (my own)

- **L2, minutes out of contact.** *Concede novelty:* Protikriti already has line of sight and Sightline has blind zones. *Defend priority:* it is the **only constraint that makes the scenario tense**.
  - It flips the demo route: the badge shows "GO +76 min" while the crew is out of sight for 27 min.
  - It is an Artemis FOD rule word for word ("maximum time without line of sight to lander", ASCEND 2025).
  - Everyone has a blind-zone *picture*. Nobody has blind *minutes* that feed the verdict and the rehearsal.
- **L3, the regain-contact field (VIPER "Safe Haven").** *Keep, still novel.* No rival offers "move to contact, then decide" as a rehearsal option. It is the same multi-source Dijkstra as earth E5's refuges, but needs no invented refuge, because the refuges are the cells the base can see.
- **L4, Map Book plus cuff card.** *Keep, merged* with eva #5 and ai F. One product, AI-drafted prose, server-filled numbers.
- **L1, the Apollo 14 opening.** *Defend* against earth E6, the Everest framing. Apollo 14 is a real *spaceflight* turn-back, decided by the clock. LROC imagery proves it, and it uses 4 s of film. Everest is Earth framing a Mars challenge does not need.
- **L5, far-first ordering. Drop.** Every stop passes with a large margin, so ordering changes nothing on screen.
- **L6, horizon views. Drop.** It contradicts my own Horizon Match trap, and Sightline owns it.

## 3. Steal (and sharpen)

1. **planetary-geologist A, "Orbit said / Rover found".** It is the only verified, unique science claim on the panel (CRISM olivine at Brac, confirmed by Liu 2022).
   - *Sharpen:* make it the *reason to walk* in the Map Book POI page: "orbit predicts X, a human checks it here".
   - Make sites the orbit is silent about (Sid, Roubion) explicit "a crew adds information here" targets. That answers the empty `scientificQuestion` field.
2. **viz-ux #4 point-of-no-return ribbon, plus earth E2 trigger gates, plus isro #2 shrinking ring.** These are one idea.
   - *Sharpen:* give the ribbon two channels. Colour shows return margin. **Dashes** mark stretches where the base cannot see the crew.
   - Gates sit at the ends of blind stretches: "Gate B: reach line of sight by 01:12, or turn."
   - That puts the Apollo FOD rule and the k-PERIL trigger on one glanceable line. All numbers come from `mission.py`.

## 4. Vote: panel top 7

1. **Return ribbon with gates and blind-stretch dashes** (viz 4, earth E2, isro 2, lunar L2). This is the thesis as one image, and it gives the scenario tension. **S–M.**
2. **Minutes out of contact plus the regain-contact field** (lunar L2/L3, jpl C7, isro 4). It is the only binding constraint, flips the Sid verdict, and adds a "move to contact" option. **S–M.**
3. **Flight Director agent with a visible proof strip** (ai A and C). This is the JPL Dec 2025 Claude pattern in the same crater: an LLM sets the inputs, the planner computes, and every number is traced or the answer is rejected. Protikriti has no LLM. **M.**
4. **Orbit said / Rover found per site** (geologist A). It is unique, verified, and is the science reason to walk. **S–M.**
5. **Calibrated margins from 27 Perseverance drives** (jpl C1 and C8). Show "+76 min (P90 +55)" with whole minutes and a real-Mars band, and apply the same band to blind minutes. **S.**
6. **Map Book and cuff card, drafted by AI and gated on numbers** (lunar L4, eva 5, ai F). The judge leaves holding the NASA flight-product format. **M.**
7. **Grade-signed, asymmetric walking time** (eva 1, jpl C3). This is defensive: Protikriti has Tobler, so a JSC judge would mark us down without it. **S.**

Not in the top 7: red-team AI search, Earth latency, HRSC, the sunset clock, the HiRISE 3D upgrade (nice, but L-ish), and lost-comms ISRID rings (morbid, and they duplicate #2 once contact exists).

## 5. The 30-second film

| # | s | Shot |
|---|---|---|
| 1 | 0–4 | LROC NAC: Apollo 14 tracks stopping short of Cone Crater's rim. Text: "1971. 30 m from the rim. Called back by the clock." |
| 2 | 4–9 | Fast descent into the Jezero box in 3D. The Sid route draws on with a green ribbon and the badge "GO · +76 min". |
| 3 | 9–14 | The contact layer switches on. The ribbon goes to dashes along 805 m and the badge flips amber: "27 min where base can't hear you." Text: "The map said GO." |
| 4 | 14–21 | Typed into the assistant: "Rover fails here, T+30. Push to Sid or turn?" Tool-call cards fire (rehearse, contact). The ribbon recolours, and three options appear: return now, continue, move to contact. |
| 5 | 21–26 | Proof strip: "All numbers traced to the planner. 1 rejected." Then a cut to the Brac card: "Orbit: olivine. Rover: olivine cumulate." |
| 6 | 26–30 | The printed cuff card and Map Book page. End card: "MARS RETURN. Real Jezero terrain. Hypothetical base. AI that can't invent a number." |

Every element is either built already or covered by votes 1–6. The 805 m and 27 min figures must come from the server at recording time, not from this document.

## 6. Positioning line

"MARS RETURN rehearses the minute a Marswalk goes wrong, including when base stops hearing you, and its AI flight controller may only speak numbers the planner computed on real Jezero terrain and checked against Perseverance's own drives."
