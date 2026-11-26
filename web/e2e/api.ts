import type { Page } from "@playwright/test";

import type { Finding, ScanReport } from "../src/lib/types";

/** A simulated Vigilo API: answers the browser's requests without any real scan. */

const STEPS = [
  { id: "connect", label: "Connecting to the website" },
  { id: "tls", label: "TLS certificate, protocol versions and HTTPS redirect" },
  { id: "headers", label: "HTTP security headers" },
];

function issue(overrides: Partial<Finding>): Finding {
  return {
    id: "headers.hsts",
    check: "headers",
    title: "HTTP Strict Transport Security (HSTS)",
    headline: "Browsers are not told to always use HTTPS",
    status: "fail",
    severity: "medium",
    description: "Browsers are not told to always use a secure connection.",
    recommendation: null,
    observed: [{ label: "Strict-Transport-Security", value: "not sent" }],
    note: null,
    fixes: {
      apache: {
        intro: "Add this to .htaccess:",
        code: 'Header always set Strict-Transport-Security "max-age=31536000"',
      },
      nginx: {
        intro: "Add this inside the server { } block:",
        code: 'add_header Strict-Transport-Security "max-age=31536000" always;',
      },
    },
    follow_up: null,
    ...overrides,
  };
}

const GIT = issue({
  id: "files.git",
  check: "files",
  title: "Exposed Git repository",
  headline: "Your Git folder can be downloaded by anyone",
  severity: "high",
  observed: [{ label: "GET /.git/HEAD", value: "200 OK · 23 bytes" }],
});
const CERT: Finding = issue({
  id: "tls.certificate",
  check: "tls",
  title: "Certificate validity",
  headline: "Certificate is valid",
  status: "pass",
  severity: "info",
  observed: [{ label: "Issuer", value: "R11" }],
  fixes: {},
});

export function makeReport(kind: "first" | "improved"): ScanReport {
  const findings = kind === "first" ? [GIT, issue({}), CERT] : [issue({}), CERT];
  const score = kind === "first" ? 70 : 90;
  return {
    target: "shop.example",
    started_at: "2026-11-26T10:00:00Z",
    finished_at: kind === "first" ? "2026-11-26T10:00:08Z" : "2026-11-27T10:00:08Z",
    score,
    grade: kind === "first" ? "C" : "A",
    findings,
    signature: "e2e-signature",
  };
}

function sse(report: ScanReport): string {
  const events = [
    ["progress", { type: "plan", steps: STEPS }],
    ...STEPS.flatMap((s) => [
      ["progress", { type: "step", id: s.id, state: "running" }],
      ["progress", { type: "step", id: s.id, state: "done" }],
    ]),
    ["report", report],
  ] as const;
  return events.map(([name, data]) => `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`).join("");
}

/** Every scan answers with the next report of `reports` (the last one repeats). */
export async function simulateApi(page: Page, reports: ScanReport[]): Promise<void> {
  let next = 0;
  await page.route("**/api/v1/scans/stream?*", (route) => {
    const report = reports[Math.min(next++, reports.length - 1)];
    return route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream", "Access-Control-Allow-Origin": "*" },
      body: sse(report),
    });
  });
  await page.route("**/api/v1/reports/pdf", (route) =>
    route.fulfill({
      status: 200,
      headers: { "Content-Type": "application/pdf", "Access-Control-Allow-Origin": "*" },
      body: Buffer.from("%PDF-1.4\n%e2e\n"),
    }),
  );
}
