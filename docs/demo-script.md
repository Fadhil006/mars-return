# Demo script — B3

Follows the narrative in `docs/design/design.md` section 14, using the labels in the built interface. No figures are quoted here: read every number from the screen, and have A2 check any figure used in the pitch and A1 check data attribution. The two-minute length is an internal target, not an event rule.

## Before starting

- Start the API and the application (`docs/run-demo.md`). Confirm the mission bar shows the dataset version and that it does **not** say "Development sample data".
- The initial mission is preloaded: a hypothetical base and a preselected Perseverance sampling site, with its evidence open.

## Narrative

The story: *the plan says GO, but the base cannot see you for most of the walk. Would you have turned back in time?*

1. **Problem.** "An explorer has a science goal and a fixed time to get back. Which route, and how much margin is left?"
2. **Destination.** Sid is preselected. In the **Evidence** tab, point to the samples from NASA's inventory and one source card. Say that the base and the crew scenario are hypothetical.
3. **GO.** Press **Compare routes**. Read the remaining margin and "Within budget" from the **Routes** tab.
4. **But.** Point to the dark wash on the map, "Base cannot see here", and the dashed stretch of the route. Read **Out of sight of base** in the Routes tab: "Exceeds contact rule", with the longest stretch. Say why it is long: Sid itself is out of sight, so the time on site counts too. The mast height and the 15 min rule are hypothetical inputs.
5. **Your call.** Press **Rehearse selected route**, drag the playhead partway, optionally tick **Hypothetical corridor blocked**, and press **Request return options**. The options stay hidden: let the audience (or a judge) choose **Return now** or **Continue, then return** before the countdown ends. Read the line that compares the call with the planner's results, then both option cards.
6. **Proof.** In the **Assistant** tab ask "Can I still return?". Point to "n of n numbers traced to planner output" and click one number chip: it highlights the same value in the Routes tab. Say what happens to a model answer that invents a number: it is discarded, and the standard explanation is shown instead (covered by `server/tests/test_assistant.py`).
7. **Close.** Optionally switch to **3D terrain**. Press **Open mission report**. State what is measured (real CTX terrain, real Perseverance sampling sites) and what is hypothetical (base, mast, contact rule, speed, budget, corridor). Nothing here is certified navigation, communications or safety guidance.

For the 30-second video, use steps 3 → 4 → 5 → 6 only; see `docs/plans/06-winning-execution-plan.md` section 4.

## If something fails live

- **Model unavailable:** the answer is labelled "Standard explanation". Say so and continue.
- **Service unavailable:** the application shows the failure and removes the old route. Say so; do not present an earlier result as current.
- **No WebGL:** stay in the 2D map; it has the same route and controls.
- Do not substitute a recording without announcing it.

## Do not claim

Physical survival, live weather, new discoveries, validated astronaut operations, real radio coverage (line of sight is geometric only), or an accuracy figure for the assistant.
