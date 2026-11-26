"use client";

import { useEffect, useId, useRef, useState } from "react";

import { useI18n } from "@/i18n/client";
import { ApiError, startActiveScan, streamActiveScan } from "@/lib/api";
import type { OwnershipProof, ScanReport, Step } from "@/lib/types";

import { ScanLog } from "./ScanLog";

interface ActiveScanProps {
  proof: OwnershipProof;
  /** The verification code: the server checks it is still published before starting. */
  token: string;
  onReport: (report: ScanReport) => void;
}

type State =
  | { kind: "conditions"; error: string }
  | { kind: "starting" }
  | { kind: "running"; steps: Step[] }
  | { kind: "stopped"; steps: Step[]; message: string };

/**
 * Last step before an active scan: the conditions, an explicit agreement, then the live
 * log of the scan. The report is handed to the parent, which shows it full page.
 */
export function ActiveScan({ proof, token, onReport }: ActiveScanProps) {
  const { t, locale } = useI18n();
  const a = t.active;
  const id = useId();
  const [state, setState] = useState<State>({ kind: "conditions", error: "" });
  const [accepted, setAccepted] = useState(false);
  const stopRef = useRef<(() => void) | null>(null);
  const runningHeading = useRef<HTMLHeadingElement>(null);

  useEffect(() => () => stopRef.current?.(), []);
  useEffect(() => {
    if (state.kind === "running" || state.kind === "stopped") runningHeading.current?.focus();
  }, [state.kind]);

  async function launch() {
    if (!accepted) {
      setState({ kind: "conditions", error: a.mustAccept });
      return;
    }
    setState({ kind: "starting" });
    let jobId: string;
    try {
      jobId = (await startActiveScan(proof.domain, token, proof.ownership_pass, locale)).job_id;
    } catch (err) {
      const message =
        err instanceof ApiError && err.message
          ? err.message
          : err instanceof ApiError && err.code === "network"
            ? t.errors.network
            : a.failed;
      setState({ kind: "conditions", error: message });
      return;
    }

    setState({ kind: "running", steps: [] });
    const update = (change: (steps: Step[]) => Step[]) =>
      setState((s) => (s.kind === "running" ? { ...s, steps: change(s.steps) } : s));

    stopRef.current = streamActiveScan(jobId, locale, {
      onPlan: (plan) => update(() => plan.map((s) => ({ ...s, state: "pending" as const, at: null }))),
      onStep: (stepId, stepState) =>
        update((steps) => steps.map((s) => (s.id === stepId ? { ...s, state: stepState, at: new Date() } : s))),
      onReport,
      onFailure: (failure) =>
        setState((s) => ({
          kind: "stopped",
          steps: s.kind === "running" ? s.steps : [],
          message: failure?.message || t.errors.network,
        })),
    });
  }

  if (state.kind === "running" || state.kind === "stopped") {
    const stopped = state.kind === "stopped";
    return (
      <div className="mt-2 flex flex-col gap-4">
        <h4 ref={runningHeading} tabIndex={-1} className="font-serif text-xl leading-7 font-semibold">
          {stopped ? a.stoppedTitle : a.runningTitle(proof.domain)}
        </h4>
        {stopped ? (
          <p role="alert" className="flex gap-2.5 text-high">
            <span aria-hidden="true" className="font-mono font-medium">
              !
            </span>
            <span>{state.message}</span>
          </p>
        ) : (
          <p className="text-muted">{a.runningIntro}</p>
        )}
        {state.steps.length > 0 && <ScanLog steps={state.steps} />}
        {stopped && (
          <div>
            <button
              type="button"
              onClick={() => setState({ kind: "conditions", error: "" })}
              className="h-12 cursor-pointer rounded-xs border border-ink px-5 font-semibold"
            >
              {a.retry}
            </button>
          </div>
        )}
      </div>
    );
  }

  const starting = state.kind === "starting";
  const error = state.kind === "conditions" ? state.error : "";
  return (
    <div className="mt-2 flex flex-col gap-4">
      <h4 id={`${id}-conditions`} className="font-semibold">
        {a.conditionsTitle}
      </h4>
      <ul aria-labelledby={`${id}-conditions`} className="flex flex-col border-t border-rule text-sm">
        {a.conditions.map((condition) => (
          <li key={condition} className="border-b border-rule py-2.5">
            {condition}
          </li>
        ))}
      </ul>
      <label className="flex cursor-pointer items-start gap-3">
        <input
          type="checkbox"
          checked={accepted}
          onChange={(e) => setAccepted(e.target.checked)}
          aria-describedby={error ? `${id}-error` : undefined}
          className="mt-1 size-4 shrink-0 cursor-pointer accent-ink"
        />
        <span>{a.accept}</span>
      </label>
      <div>
        <button
          type="button"
          onClick={launch}
          disabled={starting}
          aria-busy={starting}
          className="h-12 cursor-pointer rounded-xs bg-stamp px-6 font-semibold text-white disabled:cursor-wait disabled:opacity-80"
        >
          {starting ? a.launching : a.launch}
        </button>
      </div>
      {error && (
        <p id={`${id}-error`} role="alert" className="flex gap-2.5 text-sm text-high">
          <span aria-hidden="true" className="font-mono font-medium">
            !
          </span>
          <span>{error}</span>
        </p>
      )}
    </div>
  );
}
