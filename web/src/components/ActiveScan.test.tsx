import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MESSAGES } from "@/i18n";
import type { OwnershipProof } from "@/lib/types";
import { FakeEventSource } from "@/test/fakeEventSource";
import { finding, report } from "@/test/fixtures";

import { ActiveScan } from "./ActiveScan";

const a = MESSAGES.en.active;
const proof: OwnershipProof = {
  domain: "shop.example",
  method: "file",
  ownership_pass: "file.1800000000.signed",
  expires_at: 1_800_000_000,
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function setup(response: Response) {
  const fetchMock = vi.fn(async () => response);
  vi.stubGlobal("fetch", fetchMock);
  const onReport = vi.fn();
  render(<ActiveScan proof={proof} token="abc.1800000000.def" onReport={onReport} />);
  return { user: userEvent.setup(), fetchMock, onReport };
}

beforeEach(() => vi.stubGlobal("EventSource", FakeEventSource));
afterEach(() => vi.unstubAllGlobals());

describe("ActiveScan", () => {
  it("does not start before the conditions are accepted", async () => {
    const { user, fetchMock } = setup(json({ job_id: "job1", domain: "shop.example" }, 202));
    for (const condition of a.conditions) expect(screen.getByText(condition)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: a.launch }));
    expect(screen.getByRole("alert")).toHaveTextContent(a.mustAccept);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("starts with the pass and the code, follows the log and hands over the report", async () => {
    const { user, fetchMock, onReport } = setup(json({ job_id: "job1", domain: "shop.example" }, 202));
    await user.click(screen.getByRole("checkbox", { name: a.accept }));
    await user.click(screen.getByRole("button", { name: a.launch }));

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/active-scans");
    expect(JSON.parse(init.body as string)).toEqual({
      target: "shop.example",
      token: "abc.1800000000.def",
      ownership_pass: "file.1800000000.signed",
      accept_terms: true,
      lang: "en",
    });
    expect(FakeEventSource.last.url).toBe("http://localhost:8000/api/v1/active-scans/job1/stream?lang=en");
    expect(screen.getByRole("heading", { name: a.runningTitle("shop.example") })).toHaveFocus();

    act(() => {
      FakeEventSource.last.emit("progress", {
        type: "plan",
        steps: [{ id: "nuclei", label: "Known vulnerabilities and exposed files (Nuclei)" }],
      });
      FakeEventSource.last.emit("progress", { type: "step", id: "nuclei", state: "running" });
    });
    expect(screen.getByText("Known vulnerabilities and exposed files (Nuclei)")).toBeInTheDocument();

    const activeReport = { ...report([finding({ id: "active.zap.10098", check: "active" })]), kind: "active" as const };
    act(() => FakeEventSource.last.emit("report", activeReport));
    expect(onReport).toHaveBeenCalledWith(activeReport);
    expect(FakeEventSource.last.closed).toBe(true);
  });

  it("shows why the server refused, for example when the proof was removed", async () => {
    const message = "We could not find the file https://shop.example/.well-known/vigilo-verification.txt.";
    const { user } = setup(json({ detail: { code: "file_not_found", message } }, 422));
    await user.click(screen.getByRole("checkbox", { name: a.accept }));
    await user.click(screen.getByRole("button", { name: a.launch }));
    expect(screen.getByRole("alert")).toHaveTextContent(message);
    expect(screen.getByRole("button", { name: a.launch })).toBeEnabled();
  });

  it("offers to try again when the scan stops", async () => {
    const { user } = setup(json({ job_id: "job1", domain: "shop.example" }, 202));
    await user.click(screen.getByRole("checkbox", { name: a.accept }));
    await user.click(screen.getByRole("button", { name: a.launch }));
    act(() => FakeEventSource.last.emit("failure", { code: "active_failed", message: "The tools could not run." }));
    expect(screen.getByRole("heading", { name: a.stoppedTitle })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("The tools could not run.");
    await user.click(screen.getByRole("button", { name: a.retry }));
    expect(screen.getByRole("button", { name: a.launch })).toBeInTheDocument();
  });
});
