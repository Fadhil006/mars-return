# earth-crossdomain — round 2

**What the live app shows** (screenshot `shots/viz-ux-d- rehearse.png`): a large green "1 h 16 m · Within budget". Rehearsal is a form: a checkbox, a "Remaining time 180" text box, and "Request return options". The demo route spends 73% of the outbound leg out of the base's line of sight, yet the app shows GO. Nothing on screen pressures the user to keep going, so nothing tests their judgement. Every Earth accident review I know (NTSB Envoy E170 in 2024; ATSB VFR-into-weather; Firth's Everest descent deaths) is about the moment a person had the numbers and kept going anyway. This app currently has no such moment. Fix the missing tension first; everything else depends on it.

## 1. Attacks

**A1. isro #1, the Mars24 sunset clock. Kill it.** Jezero sits at 18°N. A 3 h EVA started mid-sol ends hours before the sun gets low, so the budget never binds, and lunar-artemis is right about that. On Earth the comparison is a ski-tour turnaround: you set it from what actually limits the day, and darkness is only the limit in winter or at the poles. Building M-sized ephemeris code for a constraint that never activates is engineering for show. Add one label line ("sun elevation at return: 41°, not limiting") and move on.

**A2. eva #2 and #6: consumables walkback plus Monte Carlo "P(return) 94%".** eva itself admits 0.38 g suited slope walking has no published calibration. A Monte Carlo over invented spreads of metabolic rate and suit loadout produces a precise-looking percentage built on nothing. That is the same mistake as a learned avalanche-risk score with no accident data behind it. On terrain with a 2.3° median slope, metabolic cost tracks distance almost exactly, so O2 percentage is just minutes in a different unit. The honest uncertainty is jpl C1: a band calibrated against 27 real Perseverance drives (p10–p90 ratio 0.88–1.29). Use that, and label consumables as future work.

**A3. ai-strategist A and B: a Flight Director agent and a red-team search, *as currently scoped*.** Three problems:
- On this terrain every stop passes 8/8 closures. The agent will cheerfully confirm GO, and the red-team will find "lose more than 76 minutes" and nothing else. Agent theatre on a scenario with no tension makes the AI look stupid.
- A live tool-calling loop needs a server-side API key on a public link that judges will open. That means cost, abuse, and a fallback to "Standard explanation" exactly when a judge clicks.
- Six streamed tool calls do not fit a 30 s film.

Build the tension first (LOS, calibrated band). After that, B (red-team) becomes cheap and genuinely interesting, because "the cheapest failure is a 4-minute delay inside the 27-minute blind stretch" is a real finding.

## 2. Defend or concede

- **E1 "Decide first" (cognitive forcing): defended, and now essential.** It is the only proposal on the panel aimed at the person rather than the arithmetic. Concession: with no tension, "continue" is always correct and the test is empty. It only works once LOS or the calibrated band makes the default route amber. In a 30 s film it is a 3 s countdown beat; on the live link it is where the judge is actually caught out.
- **E2 trigger gates: merged.** It is the same object as viz #4 (the point-of-no-return ribbon) and eva #5 (the cuff card). Build one thing: the ribbon with 3 clock gates on it, then print it as the cuff card.
- **E3 Mars Return Exposure Scale: conceded as a standalone feature.** On flat terrain every route would be Class 0. It survives only as the one-line roll-up of isro #6's PASS/FAIL flight-rule table, with blind minutes and the P90 margin as inputs.
- **E4 lost-comms search ring: promoted.** The facts make it the default case, not a hypothetical. The Sid route has an 805 m (about 27 min) blind stretch. "If they go silent at the entry point and are overdue, where does the rescue rover look?" is the forward reach from that last known point, ranked in ISRID-style tiers. Merge it into lunar L3.
- **E5 ETOPS refuges: dropped as written.** lunar L3's "safe haven = nearest cell with contact" is the better refuge, with no invented depot. I keep only the ETOPS framing (see Steal 1).
- **E6 Everest hook: dropped.** Apollo 14 at Cone Crater (lunar L1) is the same story but in space, with NASA imagery and the exact "called back by the clock" decision. It is strictly better.

## 3. Steal

1. **lunar L2 and L3 (LOS minutes plus the Safe Haven field), sharpened with ETOPS.** ETOPS does not say "avoid the ocean". It says "never be more than N minutes from an adequate alternate". So the flight rule becomes **"never more than 10 min from contact"**. The planner reports the worst point on the route ("max 27 min from contact at km 0.9"), and the rehearsal adds "move to contact (N min), then decide". Mark the equal-time point between returning to base and climbing to contact. Aviation people recognise this within a second.
2. **ai-strategist C (proof strip), sharpened with Buçinca 2021.** Explanations alone *increase* over-reliance, so a checkmark alone is not enough. Order it: the human commits (E1), then the server numbers appear, then the AI debrief appears with "6/6 numbers traced to planner". One staged rejection ("42 min not in planner output, discarded") is the single most credible AI beat available to any team.

## 4. Vote: top 7

1. **LOS flight rule plus point-of-no-return ribbon with gates** (lunar L2, viz #4, my E2, eva #5 cuff card). It flips the demo route from GO to amber on real terrain and creates the tension everything else needs. S–M.
2. **Calibrated P90 margin from 27 Perseverance drives, rounded to whole minutes** (jpl C1, C8). It kills "+76.34", and the margin is validated against Mars rather than assumed. S–M.
3. **Safe Haven rehearsal with a "move to contact" option and the lost-comms search ring** (lunar L3, my E4). It answers both "can we get back?" and "where do we look if they don't?", and no rival has either. M.
4. **Decide first, then a verified AI debrief with the proof strip and a live rejection** (my E1, ai C, eva #7 uplink format). AI that makes humans think, with honesty visible on screen. S.
5. **Orbit-said / rover-found card** (planetary A). The only novel science on the panel: CRISM olivine at Brac confirmed by Liu 2022. Adds a mission. S–M.
6. **Plain-language flight rules turned into a PASS/FAIL table** (isro #6, roll-up from my E3). The model only parses rules into constraints and the server judges them. The right AI shape. M.
7. **Apollo 14 cold open plus HiRISE 25 cm basemap** (lunar L1, planetary D). Ends the "soft orange noise" first impression and gives a real precedent. S.

**Not on the list:** the sunset clock, consumables Monte Carlo, the Earth light-time countdown, first-person walk mode, and any learned risk model.

## 5. The 30-second film

| s | Shot |
|---|---|
| 0–4 | LROC image of Apollo 14 tracks stopping short of the Cone rim. Caption: "1971. 30 m from the rim. Called back by the clock." |
| 4–10 | Jezero on the HiRISE basemap. The route to Sid draws in, reading "GO +1 h 16". Blind segments then flash red: "27 min out of contact". The status flips to amber under the rule "max 10 min". |
| 10–14 | Rehearsal at T+40. Event: "Corridor blocked." Full-screen prompt: **"Your call: return or continue?"**, with a 3-2-1 countdown. |
| 14–20 | The server reveals three options: return now, continue, move to contact (6 min). The ribbon recolours, the point-of-no-return marker drops, and the search ring appears over the blind stretch. |
| 20–25 | The AI uplink: one time-tagged line with source chips and "6/6 numbers traced". A struck-through rejected sentence fades out. |
| 25–30 | Brac: "Orbit said olivine. Rover found olivine cumulate." End card with the positioning line. |

## 6. Positioning line

**"The only Mars planner that makes you make the turnaround call before it shows you the answer, then proves every number its AI says against math tested on Perseverance's real drives."**
