import { afterEach, describe, expect, it, vi } from "vitest";
import { loadImage } from "../src/mission/api";
import { checkNumber } from "../src/mission/numberInput";

describe("typed numbers", () => {
  it("accepts complete numbers within the limits", () => {
    expect(checkNumber("25", { min: 0 })).toEqual({ value: 25 });
    expect(checkNumber(" 2.5 ", { min: 0 })).toEqual({ value: 2.5 });
    expect(checkNumber("0", { min: 0 })).toEqual({ value: 0 });
  });

  it("rejects a minus sign instead of repairing it", () => {
    // "-10" in a duration used to become 1010: the minus reset the field and the digits were appended.
    expect(checkNumber("-", { min: 0 })).toEqual({ error: "Enter a number." });
    expect(checkNumber("-10", { min: 0 })).toEqual({ error: "Must be 0 or more." });
  });

  it("rejects empty, non-numeric and out-of-range text", () => {
    expect(checkNumber("", { min: 0 })).toEqual({ error: "Enter a number." });
    expect(checkNumber("abc")).toEqual({ error: "Enter a number." });
    expect(checkNumber("Infinity")).toEqual({ error: "Enter a number." });
    expect(checkNumber("45", { min: 5, max: 30 })).toEqual({ error: "Must be 30 or less." });
    expect(checkNumber("2", { min: 5, max: 30 })).toEqual({ error: "Must be 5 or more." });
  });

  it("treats speed zero as invalid, as the service does", () => {
    expect(checkNumber("0", { above: 0, max: 1000 })).toEqual({ error: "Must be more than 0." });
    expect(checkNumber("0.5", { above: 0, max: 1000 })).toEqual({ value: 0.5 });
  });
});

describe("imagery loading", () => {
  afterEach(() => vi.unstubAllGlobals());
  const stub = (response: Partial<Response> | Error, decodes = true) => {
    vi.stubGlobal("fetch", vi.fn(async () => { if (response instanceof Error) throw response; return response as Response; }));
    vi.stubGlobal("createImageBitmap", vi.fn(async () => { if (!decodes) throw new Error("decode"); return { close() {} }; }));
    vi.stubGlobal("URL", { ...URL, createObjectURL: () => "blob:imagery" });
  };
  const ok = { ok: true, blob: async () => new Blob(["x"]) };

  it("returns a URL only for an image that loads and decodes", async () => {
    stub(ok);
    expect(await loadImage("/api/assets/imagery.webp")).toBe("blob:imagery");
  });

  it("reports an unlisted, failing, unreachable or undecodable image as missing", async () => {
    stub(ok);
    expect(await loadImage(undefined)).toBeNull();
    stub({ ok: false, blob: async () => new Blob() });
    expect(await loadImage("/api/assets/imagery.webp")).toBeNull();
    stub(new TypeError("network"));
    expect(await loadImage("/api/assets/imagery.webp")).toBeNull();
    stub(ok, false);
    expect(await loadImage("/api/assets/imagery.webp")).toBeNull();
  });
});
