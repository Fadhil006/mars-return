# Working as two groups of three

Read the plans in `docs/plans/` and the draft contract in `shared/api-contract.md`. A3 and B1 approve shared interface changes together. A1 owns scientific data/coordinates, A2 owns numerical results, B2 owns scene transforms, and B3 owns generated explanations.

## Workflow

- Pick one task from your group plan, name its owner and reviewer, and state the acceptance check.
- After the first repository commit, use a short task branch such as `group-a/terrain-crop` or `group-b/mission-map`.
- Keep changes small. Avoid editing another person's module without coordinating.
- Agree units and response shapes before independently building integrations.
- Integrate against explicit synthetic fixtures early; replace them with versioned real data once validated.
- Never mark implementation tasks complete because a folder or README exists.
- Document the actual command and result of meaningful verification in the change description.
- Keep authoritative plans in `docs/plans/`; chat exports are snapshots.

## Shared boundaries

A3 owns API validation and trusted plan lookup. B3 owns `server/assistant.py` and the model adapter. A1 provides the same coordinate transform and region package to both map views. B1 discards stale responses. B2 does not independently reinterpret geographical coordinates. B3 displays trusted metrics and cites evidence rather than recalculating route values in prompts.

## Data and assets

Raw downloads and generated bulk region assets are ignored. Commit source records and suitable small metadata after review. Package larger demo data separately with checksums and reproducible acquisition instructions. Do not commit API keys, local `.env` files, or generated scientific claims. Record licenses/attribution for dependencies, media and datasets before submission.

## Checkpoints

H1: contract/fixture agreement. H3: data gate. H6: real terrain in both views. H9: complete round trip. H12: scenario rehearsal. H27: validation. H30: feature freeze. See the shared plan for the full schedule.
