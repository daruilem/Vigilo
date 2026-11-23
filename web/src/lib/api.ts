import type { Platform, ScanFailure, ScanReport, StepState } from "./types";

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
 * Starts a scan and streams its progress (Server-Sent Events).
 * Returns a function that stops listening.
 */
export function streamScan(target: string, lang: string, handlers: ScanHandlers): () => void {
  const params = new URLSearchParams({ target, authorized: "true", lang });
  const source = new EventSource(`${API_URL}/api/v1/scans/stream?${params}`);
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

  // Native connection error. EventSource would retry forever, and a retry would start a
  // new scan, so stop here.
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
  return `vigilo-${safe}-${report.finished_at.slice(0, 10)}.pdf`;
}
