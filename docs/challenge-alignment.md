# Martian Map challenge alignment

Research date: 12 November 2026.

Official challenge: https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/

The official-domain search result describes the challenge as creating a layered, integrated view of a Martian location or route, combining data from multiple NASA science missions to support a Marswalk with science along the way. Direct retrieval failed TLS issuer verification in this environment; the indexed challenge description was available through web search. The current Resources tab and submission-specific requirements still need direct verification. No TLS verification was bypassed.

## What Group A contributes

- MRO/CTX real elevation and matched imagery, distributed by USGS, for terrain and routes.
- NASA Mars 2020 Perseverance science/sample context, explicitly distinguished from orbital terrain evidence.
- Two transparent grid-routing objectives, explicit round trips, and hypothetical closure/time-budget rehearsals.
- Source IDs, dataset/model versions, uncertainty and limitations carried to Group B.

## What this does not establish

Orbital DEMs are not current obstacle maps; hypothetical closures are not live weather. Constant-speed budgets and a selected slope threshold are not certified astronaut survival limits. A documented sample region is not an exact sample-site coordinate. The multiple-mission evidence requirement is not met by calling several derivatives of one DEM separate missions; Group B must actually expose the source-backed surface-mission context alongside orbital terrain.

The frontend, 2D/3D alignment, grounded assistant, and final submission requirements remain shared Group B integration gates, not backend-only accomplishments.

## Competitive check — 14 November 2026

Direct retrieval of spaceappschallenge.org again failed TLS issuer verification; nothing was bypassed. The Resources tab, 2026 Judging & Awards Guide and Project Submission Guide are still unread and must be opened in a browser by a team member. Search results name five judging criteria (Impact, Creativity, Validity, Relevance, Presentation) and a required project demo; the detailed wording found was from the 2025 guide.

Two public entries for the same challenge were read from their GitHub READMEs:

- [Team Protikriti, "Jezero Marswalk planner"](https://github.com/AhsanulHoque22/Nasa-Space-Apps-Challenge-2026-Team-Protikriti): live static site, CesiumJS globe, A* routing under a 15° slope limit, a "can the crew still walk home" safety card, walking-range rings, hazard markers, rover street view and weather. It lists about 25 NASA/USGS datasets across MGS, MRO, Odyssey, MSL and Mars 2020.
- [Team UnknownX, "MarsWay"](https://github.com/ahsanur-official/Interplanetary-Survival-Guide-Martian-Map): live site, 2D map, globe, first-person EVA view, short/safer/science route comparison and an offline rule-based assistant.

Consequences for this project:

- Jezero, slope-limited A* routing and a walk-home check are not distinctive on their own. Do not pitch them as the novelty.
- What neither README describes is a mid-route rehearsal: an event at a chosen point, then "return now" against "continue then return", with reproducible numbers, explicit provenance labels and tested arithmetic. That, plus the validation record, is the defensible difference.
- The largest gap is breadth of mission data. This project routes on one orbital product (MRO/CTX) with Perseverance context as text. The challenge asks for several science missions combined. Adding one or two real layers that change a decision (for example MGS/MOLA regional context, MRO/CRISM minerals for choosing science stops, or Perseverance MEDA conditions) matters more than further backend hardening.
- The science stops are still hypothetical grid points. Tying at least one to a real located Perseverance observation (PDS Rover PLACES is the recorded lead) would strengthen Relevance and Validity.
- There is no frontend, hosted demo or video yet. Other teams already have live sites; Presentation cannot be scored without one.
