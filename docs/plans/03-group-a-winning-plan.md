# Group A plan, revision 2 — 14 November 2026

Supersedes the open items in [01-group-a-data-and-routing.md](01-group-a-data-and-routing.md). Scope is Group A only: data, routing, mission arithmetic, API and evidence. Reasoning is in [challenge alignment](../challenge-alignment.md): other teams already ship Jezero slope-limited routing with a walk-home check, so that alone will not stand out.

## What Group A must hand over to make the entry competitive

| # | Deliverable | Judging criterion it serves | Status |
|---|---|---|---|
| 1 | Real science stops: Perseverance sampling sites located from NASA rover localizations | Relevance, Validity | Done |
| 2 | Second mission as data, not prose: Mars 2020 traverse layer in the region bundle | Relevance | Done |
| 3 | Cross-mission check: rover elevations against the orbital CTX grid | Validity | Done |
| 4 | Return envelope (`/api/reach`): where the crew can still get home from | Creativity, Impact | Done |
| 5 | Closure stress test (`/api/stress`): does the way home survive any single closure | Creativity | Done |
| 6 | A third mission layer that changes a decision | Relevance | Open |
| 7 | Slope-dependent walking speed in place of constant speed | Validity | Open |
| 8 | Real landmarks for the 2D/3D alignment review | Validity | Open |
| 9 | Deterministic explanation text for the assistant fallback | Presentation | Open |

## The pitch Group A's numbers support

"Can we still get back?" is answered three ways, each from tested arithmetic on real terrain:

1. **Before leaving:** the round trip to a real Perseverance sampling site, two route objectives, with margin.
2. **Before committing:** the stress test closes each stretch of the way home in turn and reports the worst case.
3. **When something changes:** the rehearsal compares returning now with continuing, and the return envelope redraws the ground from which return is still possible.

Do not claim the routing itself is new. Claim the rehearsal, the stress test and the provenance.

## Open work, in order

6. **Third mission layer.** Candidates, cheapest first: Perseverance MEDA conditions for the sols of each sample (PDS), MRO/CRISM mineral context for choosing stops, MGS/MOLA regional context. Add it only if it changes what the tool tells the crew.
7. **Walking speed.** Replace constant speed with a documented slope-dependent rule. This changes `modelVersion` and every recorded number, so do it once, early, and re-run `scripts.validate_demo`.
8. **Landmarks.** Three rover localizations (for example sols 13, 180 and 362) give Group B fixed points to check 2D and 3D registration against.
9. **Explanation fallback.** A template sentence per result, built from the saved record through `server.evidence.trusted_context`, so the demo explains itself without a model key.

## Rules that still hold

Real data stays labelled as real, scenario inputs as hypothetical. A rover localization is not a drill-hole coordinate. Every number in the pitch must come from `docs/validation-results.json`.
