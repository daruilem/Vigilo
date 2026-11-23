import type { Finding, Severity } from "./types";

const SEVERITY_RANK: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export interface SplitFindings {
  issues: Finding[]; // to fix, most serious first
  passed: Finding[]; // passed checks and neutral notes
  errors: Finding[]; // checks that could not run
}

export function splitFindings(findings: Finding[]): SplitFindings {
  const issues = findings
    .map((finding, index) => ({ finding, index }))
    .filter(({ finding }) => finding.status === "fail" || finding.status === "warn")
    .sort(
      (a, b) =>
        SEVERITY_RANK[a.finding.severity] - SEVERITY_RANK[b.finding.severity] ||
        a.index - b.index,
    )
    .map(({ finding }) => finding);

  return {
    issues,
    passed: findings.filter((f) => f.status === "pass" || f.status === "info"),
    errors: findings.filter((f) => f.status === "error"),
  };
}

export function countBySeverity(issues: Finding[]): [Severity, number][] {
  const order: Severity[] = ["critical", "high", "medium", "low"];
  return order
    .map((severity) => [severity, issues.filter((f) => f.severity === severity).length] as [
      Severity,
      number,
    ])
    .filter(([, count]) => count > 0);
}

export function sectionNumber(index: number): string {
  return String(index + 1).padStart(2, "0");
}

export function displayHost(target: string): string {
  return target.replace(/^https?:\/\//i, "").replace(/\/.*$/, "");
}
