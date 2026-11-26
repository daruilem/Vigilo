import { afterEach, describe, expect, it } from "vitest";

import { finding, report } from "@/test/fixtures";

import { compare, forgetSnapshot, loadSnapshot, parseSnapshot, saveSnapshot, snapshotOf } from "./history";

const hsts = finding({ id: "headers.hsts", severity: "medium" });
const csp = finding({ id: "headers.csp", severity: "high", headline: "Nothing limits what your pages can load" });
const git = finding({ id: "files.git", severity: "high", headline: "Your Git folder can be downloaded" });
const passed = finding({ id: "tls.certificate", status: "pass", severity: "info" });

afterEach(() => window.localStorage.clear());

describe("snapshotOf", () => {
  it("keeps only the date, score, grade and the problems, nothing observed", () => {
    const snap = snapshotOf(report([hsts, passed]));
    expect(snap).toEqual({
      v: 1,
      target: "shop.example",
      finishedAt: "2026-11-23T20:00:10Z",
      score: 54,
      grade: "D",
      issues: [{ id: "headers.hsts", headline: hsts.headline, severity: "medium" }],
    });
    expect(JSON.stringify(snap)).not.toContain("not sent");
  });
});

describe("compare", () => {
  it("lists fixed and new problems and the score change", () => {
    const before = snapshotOf(report([hsts, git]));
    const after = { ...report([hsts, csp]), score: 70, grade: "C" };
    const change = compare(before, after);
    expect(change.fixed.map((i) => i.id)).toEqual(["files.git"]);
    expect(change.added.map((i) => i.id)).toEqual(["headers.csp"]);
    expect(change.remaining).toBe(1);
    expect(change.scoreDelta).toBe(16);
  });
});

describe("parseSnapshot", () => {
  const valid = JSON.stringify(snapshotOf(report([hsts])));

  it("accepts its own format for the same site", () => {
    expect(parseSnapshot(valid, "shop.example")?.score).toBe(54);
  });

  it.each([
    ["another site", valid, "other.example"],
    ["broken JSON", "{", "shop.example"],
    ["unknown version", valid.replace('"v":1', '"v":2'), "shop.example"],
    ["bad severity", valid.replace('"medium"', '"urgent"'), "shop.example"],
    ["bad date", valid.replace("2026-11-23T20:00:10Z", "yesterday"), "shop.example"],
  ])("rejects %s", (_, raw, target) => {
    expect(parseSnapshot(raw, target)).toBeNull();
  });
});

describe("storage", () => {
  it("saves, loads and forgets a site", () => {
    expect(loadSnapshot("shop.example")).toBeNull();
    expect(saveSnapshot(report([hsts]))).toBe(true);
    expect(loadSnapshot("shop.example")?.issues).toHaveLength(1);
    forgetSnapshot("shop.example");
    expect(loadSnapshot("shop.example")).toBeNull();
  });

  it("keeps the 20 most recent sites", () => {
    for (let day = 1; day <= 22; day++) {
      const r = report([hsts]);
      saveSnapshot({
        ...r,
        target: `site${day}.example`,
        finished_at: `2026-11-${String(day).padStart(2, "0")}T10:00:00Z`,
      });
    }
    expect(window.localStorage.length).toBe(20);
    expect(loadSnapshot("site1.example")).toBeNull();
    expect(loadSnapshot("site22.example")).not.toBeNull();
  });
});
