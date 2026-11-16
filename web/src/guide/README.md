# New-user guide — B1

`GuideDialog.tsx` is a step-by-step walkthrough: what to do at each phase (set up, compare routes, look at the ground, rehearse, check evidence, report), why it matters, and a final page explaining the labels (margin, reserve, return envelope, hypothetical, outdated, model results).

- The text lives in `content.ts` as data. Labels in “curly quotes” must match on-screen text; `tests/guide.spec.ts` fails if a quoted control no longer exists.
- It opens by itself on a first visit, after the region loads, and from the header "Guide" button at any time. "Seen" is remembered in `localStorage` only as a convenience; if storage is blocked, the guide just opens again.
- Keyboard: Escape closes, Left/Right arrows change page, Tab stays inside the dialog.
