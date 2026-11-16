// The new-user guide: what to do, in the order the app expects it, and why each step matters.
// Labels in quotes match the on-screen controls exactly, so a reader can find them.

export interface GuideStep {
  title: string;
  /** Heading over `doThis`; "What to do" unless the step only explains. */
  doLabel?: string;
  /** What to do, one action per line. */
  doThis: string[];
  /** Why the step matters, in plain words. */
  why: string;
}

export interface GuideTerm {
  term: string;
  meaning: string;
}

export const GUIDE_STEPS: GuideStep[] = [
  {
    title: "What this tool is for",
    doLabel: "The idea",
    doThis: [
      "You are planning a crew excursion in Jezero Crater, Mars: drive from a base to a science site and come back.",
      "The map, elevation and slope come from real NASA orbiter data (MRO CTX). The destinations are real Perseverance sampling sites.",
      "The base, time budget, speed and slope limit are assumptions you set. They are marked “Hypothetical” or “Assumption”.",
    ],
    why: "The question the tool answers is simple: if plans change on the way, can the crew still get back in time?",
  },
  {
    title: "1 · Set up the excursion",
    doThis: [
      "In the “Excursion plan” panel on the left, choose a “Destination”.",
      "Check the assumptions: traverse speed, max slope, on-site science time and reserve.",
      "Set the “Total time budget”. It must cover outbound + on-site + return + reserve.",
      "On a phone, use the “Mission”, “Map” and “Results” buttons to switch between panels.",
    ],
    why: "These numbers drive all the time arithmetic. They are scenario inputs, not certified safety limits, so try different values.",
  },
  {
    title: "2 · Compare routes",
    doThis: [
      "Press “Compare routes”. The planner finds a round trip over the terrain.",
      "The “Routes” tab shows two options: “Shortest distance” and “Lower slope”. Pick one to see it on the map.",
      "Read the time bar: outbound, on-site, return and reserve against your budget. What is left over is the margin.",
    ],
    why: "Shortest is not always safest: steeper ground is slower and riskier. The margin tells you how much can go wrong before the trip no longer fits.",
  },
  {
    title: "3 · Look at the ground",
    doThis: [
      "Switch between “2D” and “3D” at the top of the map.",
      "Open “Layers” to show imagery, slope, science stops, the real Perseverance traverse, and where the crew is out of sight of base.",
      "Hatched areas have no elevation data (see the map legend). The planner never routes through them.",
    ],
    why: "Seeing the slope and the gaps in the data explains why a route bends where it does, and where the model knows less.",
  },
  {
    title: "4 · Rehearse and change the scenario",
    doThis: [
      "Press “Rehearse” (top) or Play in the strip at the bottom. Drag the slider to any point on the route.",
      "Pause, then change the scenario: tick “Hypothetical corridor blocked” or lower the “Remaining time”.",
      "Press “Request return options”. Make your own call first (“Return now” or “Continue, then return”), then see the planner’s answer.",
      "Press “Show return envelope” to shade every place from which the crew can still reach base in time.",
    ],
    why: "This is the heart of the tool: rehearsing a surprise mid-traverse and checking whether the way home still works.",
  },
  {
    title: "5 · Check the evidence and ask questions",
    doThis: [
      "In “Routes”, press “Stress-test the way home” to block the return at points along the way. “Robust” means it survives every single closure.",
      "The “Evidence” tab shows why the site matters, NASA’s sample records and the data sources.",
      "The “Assistant” tab answers questions about the current plan, using only the planner’s stored numbers, with citations.",
    ],
    why: "Every number traces back to the planner and a cited source, so you can trust and explain the result.",
  },
  {
    title: "6 · Make the report",
    doThis: [
      "Press “Report” (top) or “Open mission report” (bottom right).",
      "Use “Print or save as PDF” to keep or share it.",
    ],
    why: "The report collects the route, assumptions, scenario, sources and limits in one place. It only ever uses a current result.",
  },
];

export const GUIDE_TERMS: GuideTerm[] = [
  { term: "Margin", meaning: "Time left over after outbound, on-site, return and reserve. Negative means the trip does not fit the budget." },
  { term: "Reserve", meaning: "Time held back for the unexpected. The planner never spends it on walking." },
  { term: "Return envelope", meaning: "The area from which the crew can still get back to base with the time remaining." },
  { term: "Hypothetical", meaning: "A purple tag. The base, blocked corridor and scenario are invented for rehearsal, not real mission facts." },
  { term: "Current / Outdated", meaning: "The status at the top right. Change any input and results turn Outdated until you compare routes again." },
  { term: "Model results", meaning: "Routes are calculated from 20 m elevation cells. They are planning estimates, not certified navigation." },
];

const SEEN_KEY = "mars-return.guide-seen";

type Store = Pick<Storage, "getItem" | "setItem">;

/** Browser storage can be missing or throw (private windows, blocked site data); then the guide opens as if new. */
function store(): Store | null {
  try { return globalThis.localStorage ?? null; } catch { return null; }
}

export function guideSeen(s: Store | null = store()): boolean {
  try { return s?.getItem(SEEN_KEY) === "1"; } catch { return false; }
}

export function markGuideSeen(s: Store | null = store()): void {
  try { s?.setItem(SEEN_KEY, "1"); } catch { /* not remembered; the guide opens again next visit */ }
}
