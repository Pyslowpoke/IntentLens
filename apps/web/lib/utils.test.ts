import { describe, it, expect } from "vitest";
import { formatNumber } from "./api";
import { cn } from "./utils";
describe("display contracts", () => {
  it("does not turn missing results into zero", () => {
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(0)).toBe("0");
    expect(formatNumber(-1234.5)).toBe("-1,234.5");
  });
  it("merges UI variants predictably", () =>
    expect(cn("p-2 text-sm", "p-4")).toBe("text-sm p-4"));
});
