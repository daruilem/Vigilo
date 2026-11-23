import type { Finding, ScanReport } from "@/lib/types";

export function finding(overrides: Partial<Finding> = {}): Finding {
  return {
    id: "headers.hsts",
    check: "headers",
    title: "HTTP Strict Transport Security (HSTS)",
    headline: "Browsers are not told to always use HTTPS",
    status: "fail",
    severity: "medium",
    description: "A visitor on a public Wi-Fi can be downgraded.",
    recommendation: "Send the header.",
    observed: [{ label: "Strict-Transport-Security", value: "not sent" }],
    note: null,
    fixes: {
      apache: { intro: "Add to .htaccess:", code: 'Header always set Strict-Transport-Security "max-age=31536000"' },
      nginx: { intro: "Add to the server block:", code: 'add_header Strict-Transport-Security "max-age=31536000" always;' },
    },
    follow_up: null,
    ...overrides,
  };
}

export function report(findings: Finding[]): ScanReport {
  return {
    target: "shop.example",
    started_at: "2026-11-23T20:00:00Z",
    finished_at: "2026-11-23T20:00:10Z",
    score: 54,
    grade: "D",
    findings,
    signature: "test-signature",
  };
}
