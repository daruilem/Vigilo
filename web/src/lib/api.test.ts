import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FakeEventSource } from "@/test/fakeEventSource";
import { report } from "@/test/fixtures";

import { fetchReportPdf, pdfFileName, streamScan, type ScanHandlers } from "./api";

function handlers(): ScanHandlers {
  return { onPlan: vi.fn(), onStep: vi.fn(), onReport: vi.fn(), onFailure: vi.fn() };
}

describe("streamScan", () => {
  beforeEach(() => vi.stubGlobal("EventSource", FakeEventSource));
  afterEach(() => vi.unstubAllGlobals());

  it("sends the target with explicit authorisation", () => {
    streamScan("shop.example", "en", handlers());
    const url = new URL(FakeEventSource.last.url);
    expect(url.pathname).toBe("/api/v1/scans/stream");
    expect(url.searchParams.get("target")).toBe("shop.example");
    expect(url.searchParams.get("authorized")).toBe("true");
    expect(url.searchParams.get("lang")).toBe("en");
  });

  it("forwards progress, then closes on the report", () => {
    const h = handlers();
    streamScan("shop.example", "en", h);
    const source = FakeEventSource.last;
    source.emit("progress", { type: "plan", steps: [{ id: "connect", label: "Connect" }] });
    source.emit("progress", { type: "step", id: "connect", state: "done" });
    source.emit("report", report([]));
    expect(h.onPlan).toHaveBeenCalledWith([{ id: "connect", label: "Connect" }]);
    expect(h.onStep).toHaveBeenCalledWith("connect", "done");
    expect(h.onReport).toHaveBeenCalledOnce();
    expect(source.closed).toBe(true);
    // The connection closing afterwards must not be reported as a failure.
    source.onerror?.();
    expect(h.onFailure).not.toHaveBeenCalled();
  });

  it("reports server failures with their message", () => {
    const h = handlers();
    streamScan("shop.example", "en", h);
    FakeEventSource.last.emit("failure", { code: "timeout", message: "Too slow." });
    expect(h.onFailure).toHaveBeenCalledWith({ code: "timeout", message: "Too slow." });
  });

  it("stops instead of retrying when the service cannot be reached", () => {
    const h = handlers();
    streamScan("shop.example", "en", h);
    FakeEventSource.last.onerror?.();
    expect(h.onFailure).toHaveBeenCalledWith(null);
    expect(FakeEventSource.last.closed).toBe(true);
  });
});

describe("fetchReportPdf", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends the signed report with the language and hosting", async () => {
    const fetchMock = vi.fn(async () => new Response("%PDF", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const blob = await fetchReportPdf(report([]), "de", "nginx");
    expect(blob.size).toBe(4);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/api\/v1\/reports\/pdf$/);
    const body = JSON.parse(init.body as string);
    expect(body).toMatchObject({ lang: "de", platform: "nginx" });
    expect(body.report.signature).toBe("test-signature");
  });

  it("surfaces the server's message when the report is refused", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => Response.json({ detail: { message: "Run the check again." } }, { status: 400 })),
    );
    await expect(fetchReportPdf(report([]), "en", "apache")).rejects.toThrow("Run the check again.");
  });

  it("builds a safe file name", () => {
    expect(pdfFileName({ ...report([]), target: "shop.example" })).toBe("vigilo-shop.example-2026-11-23.pdf");
  });
});
