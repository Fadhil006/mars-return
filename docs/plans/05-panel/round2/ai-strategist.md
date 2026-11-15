# ai-strategist — round 2

## 0. Decide-first vs Flight Director: which AI design wins?

**Short answer: neither one alone.**

- **earth-crossdomain's E1 contains no AI.** It is a quiz modal: hide the cards, run a countdown, reveal. It is also the best idea on the panel, because Buçinca et al. (CSCW 2021) show that explanations *increase* over-reliance while forcing a commitment first reduces it.
- **My Flight Director is real AI, but it needs a judge to type.** That is invisible in a 30 s video and slow live (several planner calls plus model latency). Worse, an agent that answers before the human has thought is exactly the over-reliance pattern E1 indicts.

**The design that wins "best use of AI" puts the AI on both sides of the human's decision, and never in the arithmetic:**

1. **AI as adversary (before).** The model picks *the* event to inject. It chooses the nastiest plausible one from a small set: closure location, time loss, comms loss in a blind stretch. The server scores every candidate. This is my B, narrowed to "choose the event", not "search for failures".
2. **The human commits.** E1: "Return now or continue?", 10 s countdown, answer locked.
3. **The planner reveals.** The server's numbers appear.
4. **AI as referee (after).** A two-line debrief of the human's choice against the planner's numbers. Every number is a chip linked to its source, with a counter such as "9/9 traced". A wrong model answer is visibly rejected (my C).

That is the AI → human → physics → AI loop. It is the JPL Dec 2025 propose-and-verify pattern plus a human-judgement test. **The free-text Flight Director survives only as the live-link feature** for judges who type ("what if we lose 30 min at Brac?"). It is not the film.

## 1. Attack: the three weakest proposals

1. **viz-ux #2, HiRISE 1 m DTM as the 3D display over CTX 20 m routing.**
   - You would render boulders and ridges that the router never saw, then draw a route straight through them. The first domain judge asks "why does your safe route cross that scarp?" and Validity is gone.
   - It costs M effort for a mismatch you then have to disclaim.
   - planetary-geologist's HiRISE 25 cm *ortho* tiles (S effort, imagery only) give 90% of the polish with no geometry contradiction. jpl C2's "what 20 m hides" is the honest use of HiRISE elevation.
2. **eva-human-factors #2, #4 and #6: consumables walkback, a degraded-crew case, P(return).**
   - No Mars suit exists. Its O2, cooling and battery rates would be invented, then fed through Pandolf at 0.38 g, and dressed as physiology. That is a hypothetical number laundered into a "physical" one, which our rules exist to prevent.
   - It is three M items, all invisible in 30 s.
   - Keep #1 and #5 only.
3. **isro #1, the Mars24 sunset clock.** lunar-artemis is right, and the moderator's facts settle it. At 18°N, a 3 h EVA started mid-sol never meets sunset. It is a scheduling label dressed as a constraint, at M effort.

## 2. Defend or concede (my round-1 items)

- **E (vision "second look"): conceded and dropped.** jpl-traverse and planetary-geologist are right. 5 m CTX cannot show what matters, there are no labels, and the result would be an unvalidated layer beside real ones.
- **G (Earth comm-delay countdown): conceded.** lunar-artemis is right that Earth is out of the loop at Mars light-time. The link that matters is crew to base, and the viewshed models it.
- **B (red-team search): narrowed.** With median slope 2.3° and 8/8 closures passing, a blind failure search returns "unbreakable", which is honest but dull. Its job becomes *picking the injected event*, including comms loss in the real blind stretch, which is where the tension actually lives.
- **A (Flight Director): kept, but demoted** to the live-link feature. It also absorbs isro #6 (flight rules typed in English → checked JSON) and jpl C6 (the model proposes a stop order, the server evaluates it). They are one tool layer.
- **C (proof strip) and D (fix the refusals): defended, both S.** D is a bug. "Is it safe?" and "radiation?" must not stonewall a judge.

## 3. Steal (and sharpen)

1. **lunar-artemis L2/L3: viewshed, plus "move to contact, then decide".** This is the only proposal that creates real tension in this gentle terrain. The default Sid plan shows GO +76 min, yet the outbound leg is 73% out of sight, with an 805 m (about 27 min) blind stretch.
   - **Sharpen:** the AI adversary injects "comms lost" *inside* that stretch. The human decides. The server reveals return now / continue / move to contact. Three server-computed options, one visible AI move.
2. **planetary-geologist A: "Orbit said / Rover found".** CRISM shows olivine at Brac; Liu 2022 reports an olivine cumulate there. Nobody else has an orbit-vs-ground check.
   - **Sharpen with honest AI:** Claude reads the Sample Dossier Initial Reports *offline* and drafts each "Rover found" line with a page citation. A human approves it, and a test asserts every line has a sourceId (the geologist's F). This is AI reading NASA documents, verified, and stored as data. It shows up in the film as one card.

## 4. Vote: top 7 across the panel

1. **Viewshed blind minutes + "move to contact" option** (lunar L2/L3, jpl C7). It creates the missing tension, and it is Artemis flight-rule real. **S–M.**
2. **The AI→human→physics→AI rehearsal loop.** AI picks the event, the human decides first, the planner reveals, AI debriefs with the proof strip and a live rejection (earth E1 + my B and C). It is the honest "best use of AI" beat and fits in 8 s of video. **S–M.**
3. **Point-of-no-return ribbon with trigger gates** (viz #4 + earth E2). The thesis as one image, recolouring live. **M.**
4. **Orbit said / Rover found, AI-drafted with page citations** (geologist A+F). The only orbit-vs-ground check in the field. **S–M.**
5. **Grade-signed, asymmetric time plus a P90 margin band calibrated on the 27 drives** (jpl C1/C3, eva #1). It kills "+76.34 min" false precision, using real rover data. **M.**
6. **The Flight Director tool layer for the live link.** English what-ifs and flight rules go in, server-checked results come out (my A + isro #6 + jpl C6). **M.**
7. **HiRISE 25 cm ortho basemap plus fixing the assistant's refusals** (geologist D + my D). Cheap Presentation and Validity hygiene. **S.**

## 5. The 30-second film (6 shots)

1. **0–4 s.** Black frame: "56% of Everest deaths happen on the way down." Hard cut to the HiRISE Jezero basemap zooming to the box.
2. **4–9 s.** The route to Sid draws on and reads GO, then the blind stretch greys out: "out of sight of base for 27 min." The ribbon is green.
3. **9–14 s.** The walker pauses in the blind stretch. Card: "AI red team: comms lost here." Prompt: "Return now or continue? 5…" The viewer answers in their head.
4. **14–20 s.** Reveal the planner's three options (return now / continue / move to contact). The ribbon recolours and the point-of-no-return marker drops.
5. **20–26 s.** The AI debrief with chips and the counter "9/9 numbers traced to planner". A one-frame flash: "model said 42 min → rejected".
6. **26–30 s.** The Brac card: "Orbit: olivine. Rover: olivine cumulate." End card: "AI proposes. Physics checks. You decide."

Every number on screen is read from the running app, not written into the script.

## 6. Positioning line

**"The only Jezero planner where AI tries to break your walk home, you make the call, and a planner tested against Perseverance's real drives grades both of you: the propose-and-verify loop JPL used to drive Perseverance in this crater."**
