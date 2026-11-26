import { splitFindings } from "./report";
import type { ScanReport, Severity } from "./types";

/**
 * Progress between two check-ups of the same site, kept in the visitor's own browser.
 *
 * Nothing is sent anywhere: a short summary (date, score, grade, problem names) is written
 * to localStorage only after the visitor asks for it (German TDDDG § 25: storing on the
 * device needs consent unless the visitor requested the feature).
 */

export interface IssueSummary {
  id: string;
  headline: string;
  severity: Severity;
}

export interface Snapshot {
  v: 1;
  target: string;
  finishedAt: string;
  score: number;
  grade: string;
  issues: IssueSummary[];
}

export interface Comparison {
  previous: Snapshot;
  scoreDelta: number;
  fixed: IssueSummary[];
  added: IssueSummary[];
  remaining: number;
}

const PREFIX = "vigilo.history.";
const MAX_SITES = 20;
const SEVERITIES: Severity[] = ["critical", "high", "medium", "low", "info"];

export function snapshotOf(report: ScanReport): Snapshot {
  return {
    v: 1,
    target: report.target,
    finishedAt: report.finished_at,
    score: report.score,
    grade: report.grade,
    issues: splitFindings(report.findings).issues.map((f) => ({
      id: f.id,
      headline: f.headline ?? f.title,
      severity: f.severity,
    })),
  };
}

export function compare(previous: Snapshot, report: ScanReport): Comparison {
  const current = snapshotOf(report);
  const before = new Set(previous.issues.map((i) => i.id));
  const now = new Set(current.issues.map((i) => i.id));
  return {
    previous,
    scoreDelta: current.score - previous.score,
    fixed: previous.issues.filter((i) => !now.has(i.id)),
    added: current.issues.filter((i) => !before.has(i.id)),
    remaining: current.issues.filter((i) => before.has(i.id)).length,
  };
}

/** Anything read back from storage is checked: it may be old, edited or corrupt. */
export function parseSnapshot(raw: string | null, target: string): Snapshot | null {
  if (!raw) return null;
  try {
    const data: unknown = JSON.parse(raw);
    if (!isSnapshot(data) || data.target !== target) return null;
    return data;
  } catch {
    return null;
  }
}

function isSnapshot(value: unknown): value is Snapshot {
  if (typeof value !== "object" || value === null) return false;
  const s = value as Record<string, unknown>;
  return (
    s.v === 1 &&
    typeof s.target === "string" &&
    typeof s.finishedAt === "string" &&
    !Number.isNaN(Date.parse(s.finishedAt)) &&
    typeof s.score === "number" &&
    typeof s.grade === "string" &&
    Array.isArray(s.issues) &&
    s.issues.every(
      (i: unknown) =>
        typeof i === "object" &&
        i !== null &&
        typeof (i as IssueSummary).id === "string" &&
        typeof (i as IssueSummary).headline === "string" &&
        SEVERITIES.includes((i as IssueSummary).severity),
    )
  );
}

// --- storage (localStorage can be missing or full: private mode, quotas) ----------------

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function loadSnapshot(target: string): Snapshot | null {
  try {
    return parseSnapshot(storage()?.getItem(PREFIX + target) ?? null, target);
  } catch {
    return null;
  }
}

export function saveSnapshot(report: ScanReport): boolean {
  const store = storage();
  if (!store) return false;
  try {
    store.setItem(PREFIX + report.target, JSON.stringify(snapshotOf(report)));
    prune(store);
    return true;
  } catch {
    return false;
  }
}

export function forgetSnapshot(target: string): void {
  try {
    storage()?.removeItem(PREFIX + target);
  } catch {
    // Nothing to do: storage is unavailable, so nothing was kept either.
  }
}

/** Keep the most recent sites only. */
function prune(store: Storage): void {
  const entries: { key: string; at: number }[] = [];
  for (let i = 0; i < store.length; i++) {
    const key = store.key(i);
    if (!key?.startsWith(PREFIX)) continue;
    const snapshot = parseSnapshot(store.getItem(key), key.slice(PREFIX.length));
    entries.push({ key, at: snapshot ? Date.parse(snapshot.finishedAt) : 0 });
  }
  entries
    .sort((a, b) => b.at - a.at)
    .slice(MAX_SITES)
    .forEach(({ key }) => store.removeItem(key));
}
