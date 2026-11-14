# Demo script — B3

Follows the narrative in `docs/design/design.md` section 14, using the labels in the built interface. No figures are quoted here: read every number from the screen, and have A2 check any figure used in the pitch and A1 check data attribution. The two-minute length is an internal target, not an event rule.

## Before starting

- Start the API and the application (`docs/run-demo.md`). Confirm the mission bar shows the dataset version and that it does **not** say "Development sample data".
- The initial mission is preloaded: a hypothetical base and a preselected Perseverance sampling site, with its evidence open.

## Narrative

1. **Problem.** "An explorer has a science goal and a fixed amount of time to get back. Which route, and how much margin is left?"
2. **Destination.** Choose a destination from the list or the map. In the **Evidence** tab, point to the samples from NASA's inventory, "Location and its limits", and one source card: its mission, date, resolution and limitation. Say that the base and the crew scenario are hypothetical.
3. **Routes.** Press **Request routes**. In the **Routes** tab compare "Shortest distance" with "Lower slope" and read the remaining-margin row from the screen. If both modes return the same route, say so; that is a valid result.
4. **Terrain.** Switch to **3D terrain** (vertical scale 1×; the toggle shows relief 3× taller, labelled). Press **Rehearse selected route**, play, and pause partway.
5. **Change.** Tick **Hypothetical corridor blocked**, or reduce the remaining time, and press **Request return options**. Show both cards: "Return now" and "Continue, then return", each with its own status and margin. Optionally show the return envelope and the closure stress test.
6. **Why.** In the **Assistant** tab ask "Can I still return?". Point to the badge that says whether the answer is "AI model" or "Standard explanation", then select a source chip to open the cited source in the Evidence tab.
7. **Close.** Press **Open mission report**. State what works now, what was measured, and what would still need validating: the routes are model results on 20 m orbital terrain, the speed is constant, and nothing here is certified navigation or safety guidance.

## If something fails live

- **Model unavailable:** the answer is labelled "Standard explanation". Say so and continue.
- **Service unavailable:** the application shows the failure and removes the old route. Say so; do not present an earlier result as current.
- **No WebGL:** stay in the 2D map; it has the same route and controls.
- Do not substitute a recording without announcing it.

## Do not claim

Physical survival, live weather, new discoveries, validated astronaut operations, or an accuracy figure for the assistant.
