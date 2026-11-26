import type {
  ActiveScanStarted,
  OwnershipChallenge,
  OwnershipProof,
  Platform,
  ProofMethod,
  ScanFailure,
  ScanReport,
  StepState,
} from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_VIGILO_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

type ProgressEvent =
  | { type: "plan"; steps: { id: string; label: string }[] }
  | { type: "step"; id: string; state: StepState };

export interface ScanHandlers {
  onPlan: (steps: { id: string; label: string }[]) => void;
  onStep: (id: string, state: StepState) => void;
  onReport: (report: ScanReport) => void;
  onFailure: (failure: ScanFailure | null) => void; // null: the service could not be reached
}

/**
 * Starts a passive check-up and streams its progress (Server-Sent Events).
 * Returns a function that stops listening.
 */
export function streamScan(target: string, lang: string, handlers: ScanHandlers): () => void {
  const params = new URLSearchParams({ target, authorized: "true", lang });
  return streamEvents(`${API_URL}/api/v1/scans/stream?${params}`, handlers);
}

/** Follows a running active scan, from its start. Same events as the passive check-up. */
export function streamActiveScan(jobId: string, lang: string, handlers: ScanHandlers): () => void {
  const params = new URLSearchParams({ lang });
  return streamEvents(
    `${API_URL}/api/v1/active-scans/${encodeURIComponent(jobId)}/stream?${params}`,
    handlers,
  );
}

function streamEvents(url: string, handlers: ScanHandlers): () => void {
  const source = new EventSource(url);
  let finished = false;

  const finish = () => {
    finished = true;
    source.close();
  };

  source.addEventListener("progress", (event) => {
    const data = JSON.parse((event as MessageEvent<string>).data) as ProgressEvent;
    if (data.type === "plan") handlers.onPlan(data.steps);
    else handlers.onStep(data.id, data.state);
  });

  source.addEventListener("report", (event) => {
    finish();
    handlers.onReport(JSON.parse((event as MessageEvent<string>).data) as ScanReport);
  });

  source.addEventListener("failure", (event) => {
    finish();
    handlers.onFailure(JSON.parse((event as MessageEvent<string>).data) as ScanFailure);
  });

  // Native connection error. EventSource would retry forever, and for the passive
  // check-up a retry would start a new scan, so stop here.
  source.onerror = () => {
    if (finished) return;
    finish();
    handlers.onFailure(null);
  };

  return finish;
}

export class PdfError extends Error {}

/**
 * Asks the server to turn a report into a PDF file. The report carries the server's
 * signature, so only unmodified reports are accepted.
 */
export async function fetchReportPdf(report: ScanReport, lang: string, platform: Platform): Promise<Blob> {
  const response = await fetch(`${API_URL}/api/v1/reports/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report, lang, platform }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: { message?: string } } | null;
    throw new PdfError(body?.detail?.message ?? "");
  }
  return response.blob();
}

export function pdfFileName(report: ScanReport): string {
  const safe = report.target.replace(/[^a-z0-9.-]/gi, "-");
  const kind = report.kind === "active" ? "active-" : "";
  return `vigilo-${kind}${safe}-${report.finished_at.slice(0, 10)}.pdf`;
}

/** An error answered by the API. `message` is already translated; empty if unreachable. */
export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("network", "");
  }
  if (!response.ok) {
    const data = (await response.json().catch(() => null)) as { detail?: Partial<ScanFailure> } | null;
    throw new ApiError(data?.detail?.code ?? "internal", data?.detail?.message ?? "");
  }
  return (await response.json()) as T;
}

/** A verification code to publish in DNS or in a file. */
export function requestChallenge(target: string, lang: string): Promise<OwnershipChallenge> {
  return postJson("/api/v1/ownership/challenge", { target, lang });
}

/** Asks the server to look for the published code; `auto` tries every method. */
export function verifyOwnership(
  target: string,
  token: string,
  method: ProofMethod | "auto",
  lang: string,
): Promise<OwnershipProof> {
  return postJson("/api/v1/ownership/verify", { target, token, method, lang });
}

/**
 * Starts an active scan of a verified domain. The server checks the published proof
 * again before starting, then answers with the id of the background job.
 */
export function startActiveScan(
  target: string,
  token: string,
  ownershipPass: string,
  lang: string,
): Promise<ActiveScanStarted> {
  return postJson("/api/v1/active-scans", {
    target,
    token,
    ownership_pass: ownershipPass,
    accept_terms: true,
    lang,
  });
}
