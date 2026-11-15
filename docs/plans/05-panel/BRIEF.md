# Panel brief — MARS RETURN "make it stand out" review

You are one member of a hostile expert review panel. The team wants to WIN NASA Space Apps 2026,
challenge "Interplanetary Survival Guide: Martian Map" (layered, integrated view of a Martian location/route
combining data from multiple NASA science missions, supporting a "Marswalk" with science along the way).
Judging (per search results): Impact, Creativity, Validity, Relevance, Presentation; a demo video is required.
The team's thesis: "everyone will use AI; whoever uses AI best wins." Make this entry unforgettable.

## The product
- Repo: /home/fadhil/Projects/mars-return (READ-ONLY for you. Do not edit, commit or push anything.)
- Running live at http://127.0.0.1:8000/ (FastAPI serves the built React/Vite/Three.js frontend + /api/*; Swagger at /docs).
- Read first: CLAUDE.md, docs/challenge-alignment.md (has competitor analysis), docs/demo-script.md,
  docs/design/ , docs/plans/03-group-a-winning-plan.md, docs/plans/04-group-b-build-plan.md, docs/validation.md,
  web/src/** (frontend, ~2.2k lines), server/assistant.py, server/mission.py, server/evidence.py.
- API: GET /api/region, /api/assets/{name}; POST /api/plan, /api/rehearse, /api/reach, /api/stress, /api/brief.
- Screenshots already taken: /tmp/claude-1000/-home-fadhil-Projects-mars-return/1749d742-482d-4d51-b913-828d13213f60/scratchpad/shots/home-desktop.png (1600x1000) and /tmp/claude-1000/-home-fadhil-Projects-mars-return/1749d742-482d-4d51-b913-828d13213f60/scratchpad/shots/home-mobile.png
  (390x844 — note it was STILL on "Loading the region" after 15 s of virtual time; investigate if relevant).
- Take more screenshots yourself with:
  `chromium --headless=new --no-sandbox --enable-unsafe-swiftshader --window-size=1600,1000 --virtual-time-budget=15000 --screenshot=/tmp/claude-1000/-home-fadhil-Projects-mars-return/1749d742-482d-4d51-b913-828d13213f60/scratchpad/shots/<you>-<name>.png http://127.0.0.1:8000/`
  (Playwright MCP is broken here: no Chrome. To drive clicks, call the API directly with curl, or write a tiny
  script in /tmp/claude-1000/-home-fadhil-Projects-mars-return/1749d742-482d-4d51-b913-828d13213f60/scratchpad that uses chromium's --remote-debugging-port if you really need interaction.)
  Then view PNGs with the Read tool.

What it does today: Jezero Crater, real MRO/CTX DEM (20 m) + 5 m image; 5 real Perseverance sampling sites
from rover localizations; a hypothetical base; two route objectives (shortest / lower slope); round-trip time
budget; "rehearsal" — pause mid-route, inject an event (blocked corridor / less time), compare "return now" vs
"continue then return"; return envelope (reach); single-closure stress test; MSL RAD radiation estimate;
2D map + 3D terrain; Evidence tab with source citations; Assistant tab (deterministic templates unless
MODEL_API_KEY set; model answers kept only if numbers/citations match the stored plan); Mission report.

Competitors already public (same challenge): Team Protikriti "Jezero Marswalk planner" (CesiumJS globe, A*,
15° slope, walk-home card, range rings, hazards, rover street view, weather, ~25 datasets) and Team UnknownX
"MarsWay" (2D map, globe, first-person EVA view, short/safer/science routes, offline rule-based assistant).
Search GitHub / devpost / spaceappschallenge.org for MORE 2026 entries of this challenge.

## Non-negotiable project rules (proposals that break these are rejected)
- Synthetic data is never presented as real; no runtime fallback to fixtures.
- Hypothetical inputs stay labelled; nothing is "certified safety".
- The assistant must not recalculate route numbers: it reads server-computed metrics via trusted_context and cites.
- Bulk data stays out of Git. No API keys committed.

## Your job (round 1)
1. Use the product as a judge would in a 3-minute look. Be brutal: what looks amateur, confusing, generic,
   unconvincing, scientifically weak, or forgettable? Why would a judge score a competitor higher?
2. RESEARCH ONLINE (WebSearch / web-fetch agent / exa if available): find the best real-world tools and
   research in your domain and say concretely what they do better. Cite URLs. Recent (2024-2026) work preferred.
3. Propose the 5-8 highest-leverage changes from your expertise, each with: what, why it wins points
   (which criterion), evidence/source, rough effort (S/M/L for a 6-person student team with ~days left),
   and what real data/API it would use. Mark at least 2 as "NOVEL — nobody else will have this".
   Prefer ideas where AI is used in a way that is scientifically honest and visibly clever, not a chatbot bolt-on.
4. Name one idea from ANOTHER discipline you suspect the panel will push that you think is a trap, and why.

Write your full output to /tmp/claude-1000/-home-fadhil-Projects-mars-return/1749d742-482d-4d51-b913-828d13213f60/scratchpad/round1/<your-id>.md (markdown, <= ~1500 words, dense, no filler).
Your final message back should be a 10-line summary of your top points.
