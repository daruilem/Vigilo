import { describe, expect, it } from "vitest";

import { finding } from "@/test/fixtures";

import { countBySeverity, displayHost, sectionNumber, splitFindings } from "./report";

describe("splitFindings", () => {
  it("sorts issues by severity, then by original order", () => {
    const low = finding({ id: "low", severity: "low", status: "warn" });
    const high = finding({ id: "high", severity: "high" });
    const medium1 = finding({ id: "m1", severity: "medium" });
    const medium2 = finding({ id: "m2", severity: "medium" });
    const { issues } = splitFindings([low, medium1, high, medium2]);
    expect(issues.map((f) => f.id)).toEqual(["high", "m1", "m2", "low"]);
  });

  it("separates passed checks, notes and errors", () => {
    const { issues, passed, errors } = splitFindings([
      finding({ id: "p", status: "pass", severity: "info" }),
      finding({ id: "i", status: "info", severity: "info" }),
      finding({ id: "e", status: "error", severity: "info" }),
    ]);
    expect(issues).toEqual([]);
    expect(passed.map((f) => f.id)).toEqual(["p", "i"]);
    expect(errors.map((f) => f.id)).toEqual(["e"]);
  });
});

describe("helpers", () => {
  it("counts issues by severity, skipping empty levels", () => {
    const counts = countBySeverity([
      finding({ severity: "high" }),
      finding({ severity: "low" }),
      finding({ severity: "low" }),
    ]);
    expect(counts).toEqual([
      ["high", 1],
      ["low", 2],
    ]);
  });

  it("formats section numbers and hosts", () => {
    expect(sectionNumber(0)).toBe("01");
    expect(sectionNumber(11)).toBe("12");
    expect(displayHost("https://www.shop.example/page")).toBe("www.shop.example");
  });
});
