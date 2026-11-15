# isro-scientist — Round 2

## 2 first, because I was challenged: the sunset clock. I CONCEDE, with numbers.

I implemented Mars24 (Allison & McEwen 2000; GISS algorithm) in `scratchpad/mars24.py` and checked it against the GISS worked example: Ls at 2000-01-06 00:00 UTC comes out as 277.188° (GISS gives 277.187°). Results at Jezero (18.44°N, 77.45°E):

| UTC date | Ls | Sunrise / sunset (LTST) | Sun > 15° | Noon elevation |
|---|---|---|---|---|
| 2026-11-15 | 22.5° | 05:49 / 18:12 | 06:51–17:08 | 81° |
| 2027-02-01 | 57.7° | 05:31 / 18:29 | 06:37–17:21 | 87° |
| 2027-06-15 | 117.1° | 05:28 / 18:31 | 06:36–17:23 | 86° |
| 2027-10-01 | 171.4° | 05:55 / 18:03 | 06:59–17:01 | 75° |

Across the season the sun stays above 15° for 10.0–10.8 Mars-hours, and sunset moves by less than 30 minutes. A 3 h EVA started mid-morning returns with the sun near 50° or higher. lunar-artemis is right: at 18°N sunset is a label, not a constraint.

- **Keep only a single line in the report:** "Sun at planned return: X°, sunset 18:12 LTST." That costs S, and it is honest scheduling context.
- **Drop #1 (sunset clock) and #2 (shrinking ring).** LIFELINE already ships a shrinking safe-zone slider, and with no sun constraint my ring has nothing real driving it.

The rest of my round-1 list:

- **#4 viewshed:** I concede the novelty (Sightline has it), but it goes to the top of my vote. It is the only measured fact that flips the demo verdict. The route shows GO +76 min, yet the crew is out of sight of base for 73% of the outbound leg, including a single 805 m blind stretch. Novelty comes from turning it into a rule the rehearsal enforces.
- **#3 "Pragyan moment":** this survives, and the facts make it stronger. The terrain is too gentle (median slope 2.3°, every stop passes 8/8 closures), so tension can only come from what the map cannot see: comms, and features below the DEM's resolution. Narrow it to one real feature from the HiRISE window (jpl C2), not a full HiRISE pipeline.
- **#5 HRSC: demoted to optional.** At 50 m it is coarser than CTX, and it is invisible in 30 s. The CRISM orbit-vs-ground check (geologist) is the better multi-mission, multi-instrument story.
- **#6 flight rules:** survives. It merges with lunar-artemis L2 and ai-strategist A (below).
- **#7 cache and return: dropped.** Geologist B is the correct version of that idea.

## 1. ATTACK

1. **eva-human-factors #3 (latency-shifted envelope) and #2 ("consumables walkback, Mars numbers").** Earth round-trip light-time models the wrong link. At 6–44 min of round trip, Earth is out of the loop and the base IV crewmember decides, as lunar-artemis showed from Artemis practice. Worse, no Mars suit has published consumable figures. Any "Mars numbers" will be invented, then relabelled as minutes, which is our current budget with a costume on. That breaks the "hypothetical stays labelled" rule in spirit. It also adds 2 days of M work for a shaded band nobody can read in a 30 s video.
2. **red-team's "real SPE collapses the envelope".** The data is real but the physics is theatre. The May 2024 solar storm gave Curiosity's RAD a surface dose of roughly 8 mGy (NASA reported it as about 30 chest X-rays). That is not something that forces a 3-hour EVA home in minutes. To make the envelope "collapse" you would have to invent a dose threshold, and a radiation-literate judge at an international jury will catch that immediately. Use the real event as context in the report, not as the trigger.
3. **viz-ux #1 and #3 (4 s context descent, SSAO, sky fog, ACES) plus #2 (HiRISE as a display swap).** With a 30 s cap the descent costs 13% of the film to say "this is Mars". Protikriti's Cesium globe wins any beauty contest anyway. HiRISE as a display layer means re-texturing and fixing the edge mask for pixels nobody will notice at 1080p. Spend those days on verdicts instead. Exception: viz #4 (the ribbon) is excellent, and I vote for it.

## 3. STEAL

1. **Geologist A+B: "Orbit said / Rover found" plus science triage under contingency.** This is sample-return doctrine done properly: when the plan breaks, decide what you give up. Sharpen it by making line of sight the event that triggers triage. The rule "never out of sight > 10 min" kills Sid, and the server re-ranks the remaining stops by science per minute of margin and per minute blind. One sentence carries the whole entry: "Keep contact, keep the confirmed olivine, drop the dust-covered site."
2. **ai-strategist A + jpl C6: the AI proposes, the planner disposes.** JPL did exactly this in Dec 2025, with Claude in Jezero. Sharpen it with my #6: the agent's first job is to compile plain-language flight rules into validated constraint JSON. Its second is to call `/plan`, `/rehearse` and `/reach` with those constraints. The "proof strip" (ai-strategist C) shows every number traced to a tool result. Keep it to one tool loop, a fixed tool set, and a deterministic fallback when no key is set.

## 4. VOTE: ranked top 7

1. **Line-of-sight flight rule (lunar L2 / jpl C7 / my #4).** Viewshed plus "max minutes blind", so GO +76 becomes NO-GO on the demo route. **S–M.**
2. **AI Flight Director that compiles flight rules and calls the real planner, with a proof strip** (ai-strat A+C, jpl C6, my #6). It is the visible, honest AI story, and Protikriti has no LLM. **M.**
3. **Science triage under contingency, with "Orbit said / Rover found" per stop** (geologist A+B). Nobody else does orbit-vs-ground, and nobody else triages science under a contingency. **M.**
4. **Point-of-no-return ribbon with trigger gates** (viz #4 + earth E2). One per-cell "margin if you turn here" field drives both. Readable in 2 s of video. **S–M.**
5. **Calibrated margins: P90 from the 27 real Perseverance drives** (jpl C1). Kills the false precision of "+76.34" with a 0.88–1.29 band. **S–M.**
6. **Safe Haven / minutes to regain contact** (lunar L3). It turns "you're blind" into "walk 140 m north to regain contact", which is the actionable half of #1. **M.**
7. **Report as an Artemis-style Map Book and cuff card** (lunar L4 / eva #5). The AI drafts it, the server checks it, and it is what a crew would actually carry. **S–M.**

## 5. The 30-second film (6 shots)

1. **0–3 s.** ISRO NavCam still of Pragyan's 4 m crater, credited, with the caption "27 Aug 2023: the rover saw a crater 3 m ahead. Every explorer asks: can we still get back?"
2. **3–8 s.** Jezero 3D, base to Sid route drawn, verdict "GO, +76 min" in green.
3. **8–14 s.** Typed: "Never lose sight of base for more than 10 minutes." The proof strip shows the parsed rule. The ribbon turns red over the 805 m blind stretch, and the verdict flips to NO-GO ("27 min out of contact").
4. **14–21 s.** Typed: "What can we still do?" Visible tool calls run, the server re-plans, and the answer is the stops that keep contact, ranked by science. The confirmed-olivine card reads "CRISM predicted, Perseverance confirmed", with citation chips.
5. **21–27 s.** Rehearsal pause, event, "Return now" against "Continue then return", each with its P90 margin. Caption: "Planner checked against 27 real Perseverance drives."
6. **27–30 s.** End card with the positioning line and the URL.

## 6. Positioning line

**"The AI writes the flight rules and a tested planner enforces them. MARS RETURN is the only Mars EVA tool that tells you, mid-walk, what science to give up to still get home, with every number traced to the server and checked against real Perseverance drives."**
