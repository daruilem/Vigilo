"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { useI18n } from "@/i18n/client";
import { streamScan } from "@/lib/api";
import { displayHost } from "@/lib/report";
import type { ScanFailure, ScanReport, Step } from "@/lib/types";

import { Report } from "./Report";
import { ScanForm } from "./ScanForm";
import { ScanLog } from "./ScanLog";
import { Label, Section } from "./Section";

type Phase =
  | { kind: "idle"; target: string }
  | { kind: "scanning"; target: string; steps: Step[] }
  | { kind: "failed"; target: string; steps: Step[]; failure: ScanFailure | null }
  | { kind: "report"; target: string; report: ScanReport };

/** The whole check-up flow on one page: form, live log, then report or error. */
export function Checkup() {
  const { t, locale } = useI18n();
  const [phase, setPhase] = useState<Phase>({ kind: "idle", target: "" });
  const headingRef = useRef<HTMLHeadingElement>(null);
  const stopRef = useRef<(() => void) | null>(null);

  // Move focus to the new heading when the screen changes, for keyboard and screen readers.
  useEffect(() => {
    if (phase.kind !== "idle") headingRef.current?.focus();
  }, [phase.kind]);

  function start(target: string) {
    stopRef.current?.();
    setPhase({ kind: "scanning", target, steps: [] });

    const updateSteps = (update: (steps: Step[]) => Step[]) =>
      setPhase((p) => (p.kind === "scanning" ? { ...p, steps: update(p.steps) } : p));

    stopRef.current = streamScan(target, locale, {
      onPlan: (plan) =>
        updateSteps(() => plan.map((s) => ({ ...s, state: "pending" as const, at: null }))),
      onStep: (id, state) =>
        updateSteps((steps) =>
          steps.map((s) => (s.id === id ? { ...s, state, at: new Date() } : s)),
        ),
      onReport: (report) => setPhase({ kind: "report", target, report }),
      onFailure: (failure) =>
        setPhase((p) => ({
          kind: "failed",
          target,
          failure,
          steps: p.kind === "scanning" ? p.steps : [],
        })),
    });
  }

  function reset(target = "") {
    stopRef.current?.();
    setPhase({ kind: "idle", target });
  }

  if (phase.kind === "report") {
    return <Report ref={headingRef} report={phase.report} onNewCheck={() => reset()} />;
  }

  if (phase.kind === "scanning" || phase.kind === "failed") {
    const failed = phase.kind === "failed";
    return (
      <Section first rail={<Label>{failed ? t.errors.rail : t.scan.rail}</Label>}>
        <div className="max-w-[760px]">
          <h1
            ref={headingRef}
            tabIndex={-1}
            className="font-serif text-[32px] leading-10 font-semibold md:text-[40px] md:leading-[48px]"
          >
            {failed ? t.errors.title : t.scan.title(displayHost(phase.target))}
          </h1>

          {failed ? (
            <div role="alert" className="mt-3 flex gap-2.5 text-high">
              <span aria-hidden="true" className="font-mono font-medium">
                !
              </span>
              <p>{phase.failure?.message ?? t.errors.network}</p>
            </div>
          ) : (
            <p className="mt-3 text-muted">{t.scan.intro}</p>
          )}

          {phase.steps.length > 0 && (
            <div className="mt-8">
              <ScanLog steps={phase.steps} />
            </div>
          )}

          {failed && (
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => start(phase.target)}
                className="h-12 cursor-pointer rounded-xs bg-stamp px-6 font-semibold text-white"
              >
                {t.errors.retry}
              </button>
              <button
                type="button"
                onClick={() => reset(phase.target)}
                className="h-12 cursor-pointer rounded-xs border border-ink px-5 font-semibold"
              >
                {t.errors.edit}
              </button>
            </div>
          )}
        </div>
      </Section>
    );
  }

  return (
    <Section first labelledBy="home-title" rail={<Label>{t.home.rail}</Label>}>
      <div className="max-w-[760px]">
        <h1
          id="home-title"
          className="font-serif text-[32px] leading-10 font-semibold md:text-[40px] md:leading-[48px]"
        >
          {t.home.title}
        </h1>
        <p className="mt-3 max-w-[640px]">{t.home.intro}</p>

        <div className="mt-8">
          <ScanForm key={phase.target} initialTarget={phase.target} onSubmit={start} />
        </div>

        <dl
          aria-label={t.home.scopeLabel}
          className="mt-10 grid grid-cols-1 border-t border-ink text-sm sm:grid-cols-[120px_minmax(0,1fr)]"
        >
          {t.home.scope.map((line) => (
            <div key={line.term} className="contents">
              <dt className="pt-3 font-semibold sm:border-b sm:border-rule sm:pb-3">{line.term}</dt>
              <dd className="border-b border-rule pb-3 sm:pt-3">{line.text}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-sm">
          <Link href={`/${locale}/method`}>{t.home.methodLink}</Link>
        </p>
      </div>
    </Section>
  );
}
