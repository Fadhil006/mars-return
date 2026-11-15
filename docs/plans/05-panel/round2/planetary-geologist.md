# Round 2: `planetary-geologist`

## 1. ATTACK: the three weakest proposals

**a. isro #1, the "deadline is sunset" Mars24 clock (and isro #2, where it feeds the shrinking ring).**
- Jezero sits at 18.4°N, where a sol has about 12 h of daylight. The EVA lasts 3 h and runs mid-sol. Sunset therefore can't bind unless you start after about 14:00 LMST, which nobody would plan.
- Lunar-artemis is right, and I concede it on isro's behalf: this is an M-effort clock for a constraint that never triggers.
- The video would show a countdown that never matters. Judges will notice the slack.
- If lighting matters at all, it is **low sun angle and long shadows over the Séítah ridges**, which affects visibility, not the deadline. That is display only (viz #3).

**b. isro #5 (HRSC as an independent second DEM) and jpl C4 (the Stack et al. photogeologic sand classes).**
- **HRSC:** the SIM 3464 bundle ships HRSC h0988 at about 50 m. That is roughly 60×60 posts over our 3 km box, coarser than the 20 m CTX it is supposed to check. A cross-check at lower resolution proves nothing about the cells that matter. It is also ESA data, not "NASA missions".
- **Stack et al. classes:** jpl's "MOESM3 probably holds the GIS" is unverified. The Caltech record I found lists only MOESM1 (PDF) and MOESM2 (TIF). Even if the GIS exists, "sand: slow or no-go" speeds are invented numbers sitting on a 1:5k unit boundary. That is synthetic data dressed up as geology.
- Edwards & Buz thermal inertia gives the same "loose ground" signal with a real measurement. In our box it ranges 176 to 272, which is narrow, so it barely moves anything either.

**c. ai-strategist E ("vision second look") and earth E4/E5 (lost-comms SAR ring, refuges with ETOPS).**
- **Vision second look:** 25 cm HiRISE can't resolve rocks smaller than about 0.75 m, there is no Jezero ground truth to validate against, and it is a hallucination surface sitting next to the evidence panel. A geology judge's first question will be "precision and recall?", and we would have no answer.
- **E4/E5:** each is clever, but each needs new routing seeds, schema changes and invented priors ("most likely on the planned return line"). Each also burns a day for a beat that won't fit in a 30 s film.
- **The underlying problem:** the scenario has *no tension*. Margins of +76 min and 8/8 closures passing will not be fixed by more rings. They are fixed by a real constraint, and the viewshed is that constraint (see below).

## 2. DEFEND or concede

- **A, "Orbit said / Rover found": defend hard.** The facts now confirm it is unique: nobody else does orbit against ground.
  - It costs a 1.4 MB CC-BY raster plus a citation table.
  - Brac is a clean, citable success (CRISM high-confidence olivine, Liu 2022 olivine cumulate). Sid and Roubion showing no detection is an *honest negative*, and that is what earns Validity points.
  - One caveat to fix: check the CRISM-to-CTX registration on one landmark before claiming per-pixel agreement.
- **B, science triage in the rehearsal: concede as specified.** With 8/8 passes and +76 min there is nothing to triage. It comes back only once the line-of-sight rule and P90 margins create real pressure. Then it collapses into one line inside the rehearsal: "dropping Issole buys 18 min".
- **C, the corridor science score: drop it.** Magurin already sells science per EVA. A weighted score with hypothetical weights adds a number I can't validate.
- **D, HiRISE 25 cm via Trek WMTS: defend.** It is S effort, verified 200, 20 zoom levels. It is the single cheapest Presentation jump.
- **E, thermal inertia: demote it** to a one-line evidence row that names Mars Odyssey. Everyone has it.
- **F, Roubion: keep the fix** (S). Do not walk a crew to a failed coring attempt.

## 3. STEAL

1. **viz-ux #6, "Ground truth" frames, merged with my A as an *Orbit / Rover / Crew* triptych.**
   - **Orbit:** the CRISM pixel class at the stop.
   - **Rover:** the actual Mastcam-Z or Navcam raw frame from that sol, billboarded in 3D, with its PDS or raw-image link.
   - **Crew:** one sentence from the Sample Dossier Initial Report on what a human adds, for example "abrasion patch only 5 cm; a crew could map the cumulate's layering over 10s of metres".
   - **Sharpening:** the triptych is the *science* half of the video. It has no hallucination risk because every panel is a file with a URL.
2. **lunar L2 / jpl C7, minutes without line of sight as a flight rule.**
   - This is the only proposal that turns our gentle terrain into a real decision: on the Sid route the base is out of sight for 73% of the outbound leg, including one blind stretch of 805 m (about 27 min).
   - **Sharpening:** grey the blind segments on the point-of-no-return ribbon, and make "max 20 min blind" a labelled hypothetical rule. GO +76 then becomes **NO-GO**, or a reroute that costs margin. *That* is the tension the stress test lacks, and it gives science triage (my B) something to trade against.

## 4. VOTE: top 7 across the panel

| Rank | Proposal | Why | Effort |
|---|---|---|---|
| 1 | **Line-of-sight flight rule** (lunar L2, jpl C7, isro #4) in plan and rehearsal | Creates the only real tension. Measured: Sid route blind 73%, with an 805 m gap | S–M |
| 2 | **Point-of-no-return ribbon, recoloured live by the event** (viz #4, plus earth E2 gates as markers) | The core question answered in 2 s on screen. The server computes it | S–M |
| 3 | **Orbit / Rover / Crew card** (my A plus viz #6) | Nobody does orbit against ground; Brac is a citable confirmation. Adds CRISM and Mastcam-Z | S–M |
| 4 | **AI proposes, planner checks** (ai A, jpl C6 and ai C, with a visible proof strip) | The JPL Dec 2025 pattern. The model picks inputs and stop order; every number comes from a tool result and turns green when verified | M |
| 5 | **HiRISE 25 cm ortho basemap and a context descent** (my D, viz #1) | Cheapest Presentation win. Tiles verified; cache them locally, no runtime dependency on Trek | S |
| 6 | **P90 margins calibrated on 27 real drives** (jpl C1) | Replaces the false precision of "+76.34" with a band grounded in Perseverance data | M |
| 7 | **"Red-team this plan"** (ai B) | The AI searches for the cheapest failure, now including blind stretches. The server scores every candidate. A dramatic beat | M (after #4) |

Below the line: fix the refusals (ai D, S) is a must-do chore, not a differentiator.

## 5. The 30-second film (six shots)

1. **0–4 s.** MOLA Jezero zooms through CTX to the 3 km box, then into **HiRISE 25 cm**. Caption: "Real NASA orbital data · Jezero Crater".
2. **4–9 s.** Brac. A CRISM olivine pixel glows, the frame cuts to Perseverance's Mastcam-Z frame of the same outcrop, then text: "Orbit predicted olivine. Perseverance confirmed it (Liu 2022)."
3. **9–15 s.** Typed prompt: "Brac and back in 3 h." The agent calls the planner, the route draws in green, and a grey band appears: "27 min out of sight of base". The verdict flips GO → **NO-GO** and the route reroutes.
4. **15–22 s.** Mid-walk event: "−30 min, wheel-less crew slowed". The ribbon bleeds amber to red, the point-of-no-return marker drops, and the cards show "Return now +14 · Continue −9" as a P90 band.
5. **22–27 s.** A two-line AI call. Each number ticks green against the server (the proof strip). Caption: "The AI never computes a number."
6. **27–30 s.** End card: badges for MRO (CTX · HiRISE · CRISM), Odyssey, Mars 2020 and MSL, plus the positioning line.

## 6. Positioning line

**"MARS RETURN rehearses the moment a Marswalk goes wrong: an AI proposes, a planner calibrated on Perseverance's real drives checks every number, and every science stop shows where orbit was proven right on the ground."**
