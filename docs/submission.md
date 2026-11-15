# Submission kit — paste-ready text, video script, recording steps

Fill the `[brackets]`. Every number below was read from the running app on dataset `7e08b277f6761b7c`; re-read them from the screen on the day you record, and change the text if they differ.

## 1. Form fields

**Project name:** MARS RETURN

**Challenge:** Interplanetary Survival Guide: Martian Map

**Summary** (about 1,250 characters including spaces; the limit is 1,500):

> MARS RETURN is a mission rehearsal tool for a Marswalk in Jezero Crater. It plans round trips from a hypothetical base to five real Perseverance sampling sites over real MRO CTX terrain, and answers the question every walk must answer: can we still get back?
>
> Most route planners stop at "the route fits the time budget." MARS RETURN also asks whether base can still see you. It computes line of sight from the base over the real terrain and reports the longest time out of contact. On the default route to Sid, the walk fits with over an hour to spare, yet the crew is out of sight of base for about an hour at a stretch, longer than a 15-minute contact rule allows.
>
> Rehearse the walk, pause anywhere, change the scenario (a blocked corridor, less time) and make the call yourself before the planner shows its answer: return now, or continue? Then compare your decision with the planner's numbers.
>
> An assistant explains each result, but it never calculates. Every number it says is shown next to the saved plan value it repeats, and an AI answer with any number not in the plan is thrown away.
>
> The base, speed, time budget and contact rule are hypothetical inputs; routes are model results on 20 m orbital terrain, not certified guidance.

**Project details** (longer field; trim if the form limits it):

> **What it does.** Choose a Perseverance sampling site. The planner finds two routes (shortest, and lower slope) over real CTX elevation at 20 m, with the round-trip time, on-site time, reserve and remaining margin. It then computes line of sight from a hypothetical base mast to every cell, shades where the base cannot see, and reports total and longest continuous time out of contact, including time spent at a site the base cannot see. Three of the five sites break a 15-minute contact rule even though every route fits the time budget.
>
> **Rehearsal.** Play the walk in 2D or 3D, pause anywhere, add a hypothetical event, and request return options. The options stay hidden until you decide (10-second countdown). Then the app shows "Return now" against "Continue, then return", and says how your call compares. Committing before seeing a model's answer reduces over-reliance on it (Buçinca et al. 2021).
>
> **Also:** a return envelope (every point from which the crew can still walk home in time), a closure stress test along the way home, a per-excursion radiation estimate from Curiosity's RAD measurements, an evidence panel with source cards for every site, and a mission report.
>
> **How AI is used.** The assistant never computes route numbers. It reads the saved plan through a trusted lookup, and every number in an answer is traced to the stored value it repeats ("11 of 11 numbers traced to planner output"). Safety, hazard and radiation questions get fixed answers that state what the planner does not model. The public demo uses fixed templates; with an Anthropic key a Claude model can word the answers, and any answer whose numbers or citations do not match the plan is discarded.
>
> **Validation.** 134 backend and 42 frontend automated tests; A* checked against an independent Dijkstra; the line-of-sight code tested on synthetic terrain with known answers; per-site contact results recorded in docs/validation.md.
>
> **Built with:** Python, FastAPI, NumPy, rasterio; React, TypeScript, Vite, Three.js; Docker on Render.
>
> **Limits.** The base, mast height, speed, budget, contact rule and blocked corridor are hypothetical. Line of sight is geometric only (no antennas, relays or radio effects). 20 m terrain cannot show boulders or ripples. Nothing here is certified navigation, communications or safety guidance.

**NASA data:**

- MRO CTX DEM, Jezero Crater, 20 m (USGS Astrogeology, Mars 2020 science investigation maps): https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif
- MRO CTX orthomosaic, Jezero Crater, 5 m: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXortho_mosaic_5m.tif
- Mars 2020 Perseverance waypoints (end-of-drive localizations): https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json
- Mars 2020 Perseverance traverse: https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_traverse.json
- Mars 2020 rock sample inventory: https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/
- Perseverance location map: https://science.nasa.gov/mission/mars-2020-perseverance/location-map/
- PDS Geosciences Node, Mars 2020 (Rover PLACES): https://pds-geosciences.wustl.edu/missions/mars2020/places.htm
- MSL Curiosity RAD surface dose (Hassler et al. 2014, Science): https://doi.org/10.1126/science.1244797

**Other data and tools:** USGS Astrogeology map projection and processing records (`data/sources/`); SwRI RAD release; FastAPI, NumPy, rasterio, React, Three.js, Vite; Render for hosting.

**AI use (SI tools):** Code and documentation were written with the help of Claude (Anthropic) through Claude Code; the team designed the approach and reviewed, tested and validated the code. In the app, an optional Claude model can word the assistant's explanations, but it never calculates and its answers are discarded unless every number matches the saved plan; the public demo runs without a model. No NASA data, imagery or branding is AI-generated. The video uses screen recordings of the app and a human voice-over; it contains no AI-generated images or voice.

**Links:**
- Live demo: `[Render URL]`
- Repository: https://github.com/Fadhil006/mars-return
- Video: `[YouTube or Drive link]`

## 2. Thirty-second video with voice-over

About 75 words, at a calm speaking pace of about 2.5 words per second. Record the voice-over separately, then lay it over the screen capture. Add English subtitles: the guide asks for them on any video not in English, and they help judges watching muted.

| Time | On screen | Voice-over |
|---|---|---|
| 0–5 s | Jezero map, Sid selected, press **Compare routes**; the route draws and "Within budget, 1 h 16 m" appears | "On Mars, the way back matters more than the way out." |
| 5–12 s | The "Base cannot see here" wash and the dashed blind stretch; Routes tab shows **Exceeds contact rule, 1 h 03 m** | "This walk to Sid fits the time budget with over an hour to spare. But the terrain hides the crew from base for about an hour at a stretch." |
| 12–18 s | Rehearse, drag the playhead partway, **Request return options**; the countdown panel | "So before the planner answers, you decide. Return now, or continue?" |
| 18–25 s | Click **Continue, then return**; the comparison line, then Assistant tab: **✓ 11 of 11 numbers traced** | "Then the planner shows the result on real NASA terrain, and the assistant explains it, with every number traced to the plan." |
| 25–30 s | End card: MARS RETURN · "Plan the way back first." · team name · "Base and scenario are hypothetical" | "MARS RETURN. Plan the way back first." |

**Before recording:**
1. Open the deployed app once so it is warm; the free Render plan sleeps after about 15 minutes of no traffic and takes up to a minute to wake.
2. Browser at 1600 × 1000 or 1920 × 1080, zoom 100 %, no bookmarks bar, notifications off.
3. Do one dry run of the clicks so the recording has no searching. Set the playhead first, then start recording at step 3 if the 30 s is tight.
4. Scroll the assistant panel so the "numbers traced" line is in view before you cut to it.

**Rules to keep** (from `docs/submission-checklist.md`): 30 seconds or less; English or English subtitles; a public link tested in a private window; no images or voice of anyone under 18; no "safe", "certified" or "survival" claims; keep the "Hypothetical" labels visible in frame.

## 3. Final steps on the form

1. Paste the fields above, then add the Render URL and the video link.
2. Tick "Agree to Terms and Conditions" and "Confirm All Work is Original".
3. Click "Submit for Judging" and wait for the confirmation banner. Take a screenshot of it.
