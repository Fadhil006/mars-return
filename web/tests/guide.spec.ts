import { describe, expect, it } from "vitest";
import { GUIDE_STEPS, GUIDE_TERMS, guideSeen, markGuideSeen } from "../src/guide/content";

const memory = () => {
  const data = new Map<string, string>();
  return { getItem: (k: string) => data.get(k) ?? null, setItem: (k: string, v: string) => void data.set(k, v) };
};
const broken = { getItem: () => { throw new Error("blocked"); }, setItem: () => { throw new Error("blocked"); } };

describe("new-user guide", () => {
  it("gives every step something to do and a reason", () => {
    expect(GUIDE_STEPS.length).toBeGreaterThan(3);
    for (const step of GUIDE_STEPS) {
      expect(step.title).not.toBe("");
      expect(step.doThis.length).toBeGreaterThan(0);
      expect(step.why).not.toBe("");
    }
    expect(GUIDE_TERMS.map((t) => t.term)).toContain("Return envelope");
  });

  it("names controls that exist in the app", () => {
    // Quoted labels in the guide must match real on-screen text, so a renamed button breaks this test.
    const files = import.meta.glob<string>(["../src/**/*.{ts,tsx}", "!../src/guide/**"], { query: "?raw", import: "default", eager: true });
    const src = Object.values(files).join("\n");
    const quoted = GUIDE_STEPS.flatMap((s) => s.doThis).join(" ").match(/“[^”]+”/g) ?? [];
    expect(quoted.length).toBeGreaterThan(10);
    const ui = new Set(["Mission", "Map", "Results"]); // the narrow-screen pane buttons are capitalised from keys
    for (const q of quoted) {
      const label = q.slice(1, -1);
      if (!ui.has(label)) expect(src, label).toContain(label);
    }
  });

  it("opens once, then remembers it was seen", () => {
    const s = memory();
    expect(guideSeen(s)).toBe(false);
    markGuideSeen(s);
    expect(guideSeen(s)).toBe(true);
  });

  it("still works when browser storage is blocked or missing", () => {
    expect(guideSeen(broken)).toBe(false);
    expect(() => markGuideSeen(broken)).not.toThrow();
    expect(guideSeen(null)).toBe(false);
  });
});
