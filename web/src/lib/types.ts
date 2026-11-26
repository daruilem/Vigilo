// Mirrors the Pydantic models in src/vigilo/models.py.

export type Status = "pass" | "warn" | "fail" | "info" | "error";
export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Platform = "apache" | "nginx" | "cloudflare" | "wordpress";

export const PLATFORMS: Platform[] = ["apache", "nginx", "cloudflare", "wordpress"];

export interface Observation {
  label: string;
  value: string;
}

export interface Fix {
  intro: string;
  code: string;
}

export interface Finding {
  id: string;
  check: string;
  title: string;
  headline: string | null;
  status: Status;
  severity: Severity;
  description: string;
  recommendation: string | null;
  observed: Observation[];
  note: string | null;
  fixes: Partial<Record<Platform, Fix>>;
  follow_up: string | null;
  /** Machine-readable details, e.g. {platform, hosted} on cms.detected. */
  evidence?: Record<string, unknown>;
}

export interface ScanReport {
  target: string;
  /** Passive check-up, or active scan of a verified domain (graded separately). */
  kind?: "passive" | "active";
  started_at: string;
  finished_at: string;
  score: number;
  grade: string;
  findings: Finding[];
  signature: string | null;
}

export type StepState = "pending" | "running" | "done" | "failed";

export interface Step {
  id: string;
  label: string;
  state: StepState;
  at: Date | null;
}

export interface ScanFailure {
  code: string;
  message: string;
}

export type ProofMethod = "meta" | "file" | "dns";

/** Mirrors api.ChallengeResponse: what to publish to prove control of a domain. */
export interface OwnershipChallenge {
  domain: string;
  token: string;
  expires_at: number; // Unix time, seconds
  meta: { tag: string };
  file: { name: string; url: string; content: string };
  dns: { name: string; type: "TXT"; value: string };
}

/** Mirrors api.VerifyResponse. */
export interface OwnershipProof {
  domain: string;
  method: ProofMethod;
  ownership_pass: string;
  expires_at: number;
}

/** Mirrors api.ActiveScanStarted. */
export interface ActiveScanStarted {
  job_id: string;
  domain: string;
}
