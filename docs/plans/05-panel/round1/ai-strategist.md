# ai-strategist — round 1 (Applied-AI lead, Space Apps / NASA-AI judge lens)

## 1. Three-minute judge look: the AI story

**Verdict: the AI is the weakest part of the entry, and it hides the strongest part.**

- **It is a third tab with three canned buttons.** Default panel is Evidence, so a judge has to find "Assistant", press "Can I still return?", and get a paragraph that repeats the Routes tab. That reads as a rule-based FAQ, which is exactly what MarsWay ships ("offline rule-based assistant"). There is nothing to tell them apart on screen.
- **Without `MODEL_API_KEY` the demo shows "Standard explanation".** A judge thinks: no AI. With the key, the model only rephrases a `referenceAnswer` (`server/assistant.py`, effort low). Either way it is a bolt-on.
- **It refuses the first questions a judge will type.** The `TOPICS` regex in `server/assistant.py` sends `radiation|dust|safe|hazard|surviv*` straight to "The supplied evidence does not cover this." Radiation is now a data layer (commits ea4a3e9 and 282dad3), yet "What's my radiation dose?" gets a refusal. "Is this route safe?" should get an honest "not certified; here is what the model does and doesn't say". Instead it gets a stonewall.
- **"It cannot change routes, inputs or the map."** This is the opposite of what wins. The rule is *the model must not calculate*. It is not *the model must not act*. Calling the real planner is allowed, and it is the whole opportunity.
- **The best AI-safety engineering is invisible.** `_consistent()` checks every number in a model answer against stored facts, and answers that fail are thrown away. That is a real, defensible "grounded LLM" design. No judge will ever see it.

**Why a competitor could outscore us on "AI":** AstroMind/MarswalkAI (DEV post, IBM Granite) claims an "AI route plan, hazard map, EVA checklist" (https://dev.to/walsal201/astromind-4ji4). Its AI is ungrounded, but it is visible and bold. Judges reward what they see.

## 2. What real AI work does better (cited)

- **NASA JPL + Claude planned Perseverance drives in Jezero, 8 and 10 Dec 2025 (sols 1707/1709).** Claude read orbital imagery with vision and produced waypoints, about 400 m in 10 m segments, written in Rover Markup Language. It critiqued and revised its own plan. Every plan then went through the rover's daily simulation (more than 500,000 variables) before humans approved it. Ground images later showed sand ripples that Claude had not seen. https://www.anthropic.com/news/claude-on-mars, https://www.space.com/space-exploration/mars-rovers/nasas-perseverance-mars-rover-completes-its-1st-drive-planned-by-ai, https://www.engadget.com/ai/nasa-used-claude-to-plot-a-route-for-its-perseverance-rover-on-mars-203150701.html
  → **Same crater, same pattern: the AI proposes, a deterministic simulator decides.** Our architecture already has the simulator half. That is the pitch.
- **ROSA (JPL, 2024/25):** a ReAct-style LLM agent that calls robot tools in natural language. It shows that "the LLM drives tools and never invents state" is the accepted JPL pattern. https://arxiv.org/html/2410.06472v2
- **AI4Mars:** about 326K crowd labels on rover-camera images, DeepLabv3 above 96% (CVPRW 2021). It was later expanded to include Perseverance. This is *rover-level* imagery, so it does not apply to our CTX orbital tiles. https://openaccess.thecvf.com/content/CVPR2021W/AI4Space/papers/Swan_AI4MARS_A_Dataset_for_Terrain-Aware_Autonomous_Driving_on_Mars_CVPRW_2021_paper.pdf
- **MOMO, Mars Orbital Model (CVPR 2026, ASU + JPL):** a masked-autoencoder (MAE) foundation model trained on about 12M HiRISE, CTX and THEMIS samples. Weights are public and it is evaluated on Mars-Bench. This is the Mars counterpart of Prithvi, which is Earth/HLS only and not usable here. https://arxiv.org/abs/2604.02719, https://huggingface.co/Mirali33/MOMO
- **NOAH-H** (ExoMars HiRISE terrain classifier) was applied to Jezero, but its weights are not confirmed open. **Ono et al., Mars 2020 traversability tools**, are where "terrain class → traversability → route" comes from. https://oro.open.ac.uk/84535, https://www-robotics.jpl.nasa.gov/media/documents/Data-driven%20surface%20traversability%20analysis%20for%20Mars%202020%20landing%20site%20selection.pdf

## 3. Highest-leverage changes

### A. "Flight Director" agent: the LLM *drives the real planner* — **NOVEL**
- **What:** turn `/api/brief` into a tool-calling agent. Its tools are thin wrappers over `/api/plan`, `/api/rehearse`, `/api/reach` and `/api/stress`, plus `get_evidence(stopId)`. A judge types: *"We're 40 min out toward Brac and lose 30 min to a dust-clogged wheel. Do we push on or turn back?"* The agent sets the pause point and budget, calls `rehearse`, maybe also `reach`, and answers. The map updates live with each call. A visible **tool trace** lists every call as a card (inputs → planner output).
- **Honesty:** the model only chooses *inputs*, and every number comes from a `tool_result`. Extend `_consistent()` so that any number in the final answer must appear in this turn's tool results or in the user's own stated inputs. Every agent-chosen input is tagged "Hypothetical (AI-chosen)".
- **Wins:** Creativity and Impact ("ask in English, get a tested what-if"). Relevance: it is the JPL pattern, in the same crater.
- **Feasibility:** Claude tool use with `strict: true` schemas mirroring the Pydantic models. Note that on Opus 5.5 / Sonnet 5.5 a forced `tool_choice` is a 400, so use `auto`. For a fast demo, use Sonnet 5.5 or Haiku 5.5 at low effort, or Opus 5.5 `speed:"fast"`, and stream the trace so the waiting is part of the show. Cap it at about 6 tool calls. The key stays server-side; nothing goes in the web bundle.
- **Effort:** M (about 1.5–2 days, B3 + A3). Data: the existing planner.

### B. "Red-team this plan": adversarial scenario search — **NOVEL**
- **What:** one button. The agent searches for the *smallest plausible event that breaks the return*: a closure placed at a narrow point, a time loss at the worst minute, a lower slope ceiling, or two events combined. It uses `/api/stress` and `/api/rehearse` as the oracle and returns the **3 cheapest ways this mission fails**. Each comes with the planner's own margin and a "replay on map" button.
- **Why it beats the existing stress grid:** the grid tries N circles blindly. The LLM proposes *meaningful* failures (it reads the elevation profile and route geometry, e.g. "the only gap between the two craters"), and the server scores every one. This is AI for *falsification*, not chat. No competitor will have it.
- **Honesty:** the AI ranks scenarios but never computes a margin. The output is labelled "hypothetical stressors, model results".
- **Wins:** Validity (it stress-tests its own answer), Creativity, Presentation (a dramatic demo beat). **Effort:** M. Reuses A's tool layer, so it costs about +0.5 day after A.

### C. Make verification *visible*: the "proof strip" — S
- Every number in an AI answer becomes a chip that links to the metric or tool call it came from. A counter reads "7/7 numbers traced to planner output".
- In the demo, show one rejection live. A dev toggle injects a wrong number, and the UI says "Model answer rejected: 42 min not in planner output → standard explanation shown." Judges have seen 50 chatbots and none that catches its own hallucination on stage.
- **Wins:** Validity and Creativity. Cite the JPL "simulate before trust" step. **Effort:** S (½ day). The data already exists (`metricRefs`, `_consistent`).

### D. Fix the refusals; answer hard questions honestly — S
- Replace the regex stonewall with grounded partial answers:
  - **radiation:** give the MSL RAD estimate with its citation and "not a dose limit".
  - **safe / hazard:** "this tool doesn't certify safety; here's slope max/mean, the no-data mask, and 20 m resolution limits", with the cited limitation fields.
  - **dust / weather:** "no weather input; scenario only".
- An answer of "here's what we know and what we don't" scores Validity points. A refusal scores zero. **Effort:** S. Owner B3; touches `TOPICS` and the templates only.

### E. Vision "second look" at the corridor, labelled as interpretation — M
- Send Claude (vision) the 5 m CTX crop along the chosen corridor together with the server's slope profile. It returns at most 5 *hypotheses* with boxes, e.g. "possible crater rim", "possible dune/ripple field". Each hypothesis is shown in a distinct style and tagged "AI interpretation, unverified, 5 m imagery cannot resolve rocks".
- Cross-check each hypothesis against server slope stats, and show "agrees / disagrees with DEM".
- This is literally what JPL did, and ripples were the miss in the JPL story. It makes a great narrative ("AI saw X; the DEM confirms Y; orbit can't see Z").
- **Risk:** hallucination. Mitigate by restricting labels to a closed vocabulary through structured output, and never feeding the result into routing. **Effort:** M.

### F. Auto-generated mission debrief — S
- Claude drafts the Mission report narrative from `trusted_context` plus the agent trace: decision, alternatives rejected, margins, what the data can't see. It goes through the same number check. If the check fails, fall back to the template. **Effort:** S. Wins Presentation, and the judge leaves with the artifact.

### G. Comm-delay framing (optional garnish) — S
- An "Ask Earth" mode delays the answer by the real one-way light time for the demo date (JPL Horizons distance), with a visible countdown. The same question answered "onboard" (the agent, A) returns at once.
- This dramatises *why* "return now vs continue" must be decided locally. Use the Web Speech API (native, no key) for voice input.
- Keep it to a few seconds of the demo, and label the timer as compressed. **Effort:** S. Do it only after A–D.

**Order:** D → C → A → B → F → E → G. D+C fit in one day and already change the judge's impression. A+B are the "nobody else has this" pair.

**Not recommended within days:** fine-tuning MOMO / AI4Mars-style segmentation. AI4Mars is rover-view imagery; MOMO needs a downstream head and labelled Jezero CTX tiles. That is L effort, it would output an unvalidated hazard layer, and it would weaken Validity. Cite MOMO in "future work" instead.

## 4. Trap from another discipline

**"Add a first-person EVA street view / photoreal walk" (3D/UX).** MarsWay already has one, so it is not distinctive. At eye level, a 20 m DEM is blobby mush and looks *worse* than their globe. It costs days of Three.js work and changes no decision. Runner-up trap: **"live Mars weather"** from REMS/MEDA. Those are past point measurements, not forecasts, and calling them live breaks the hypothetical-labelling rule.

## Sources
- https://www.anthropic.com/news/claude-on-mars
- https://www.space.com/space-exploration/mars-rovers/nasas-perseverance-mars-rover-completes-its-1st-drive-planned-by-ai
- https://www.engadget.com/ai/nasa-used-claude-to-plot-a-route-for-its-perseverance-rover-on-mars-203150701.html
- https://arxiv.org/html/2410.06472v2 (ROSA)
- https://openaccess.thecvf.com/content/CVPR2021W/AI4Space/papers/Swan_AI4MARS_A_Dataset_for_Terrain-Aware_Autonomous_Driving_on_Mars_CVPRW_2021_paper.pdf
- https://data.nasa.gov/dataset/ai4mars-a-dataset-for-terrain-aware-autonomous-driving-on-mars
- https://arxiv.org/abs/2604.02719, https://huggingface.co/Mirali33/MOMO (MOMO)
- https://oro.open.ac.uk/84535 (NOAH-H, Jezero)
- https://www-robotics.jpl.nasa.gov/media/documents/Data-driven%20surface%20traversability%20analysis%20for%20Mars%202020%20landing%20site%20selection.pdf
- https://dev.to/walsal201/astromind-4ji4 (competitor, AI-branded Marswalk)
