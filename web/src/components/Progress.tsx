"use client";

import { useId, useState } from "react";

import { DATE_LOCALES } from "@/i18n";
import { useI18n } from "@/i18n/client";
import { compare, forgetSnapshot, saveSnapshot, type IssueSummary, type Snapshot } from "@/lib/history";
import type { ScanReport } from "@/lib/types";

import { Label, Section } from "./Section";
import { SeverityMark } from "./SeverityMark";

type Saved = "no" | "yes" | "failed" | "forgotten";

interface ProgressProps {
  report: ScanReport;
  /** Summary of the previous check of this site, kept on this device; null if none. */
  previous: Snapshot | null;
}

const DATE_OPTIONS: Intl.DateTimeFormatOptions = {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
};

/**
 * With a previous summary: what was fixed, what is new, how the score moved.
 * Without one: an offer to remember this report on this device (opt-in, nothing is
 * written before the visitor asks).
 */
export function Progress({ report, previous }: ProgressProps) {
  const { t, locale } = useI18n();
  const titleId = useId();
  const [saved, setSaved] = useState<Saved>(previous ? "yes" : "no");

  function remember() {
    setSaved(saveSnapshot(report) ? "yes" : "failed");
  }

  function forget() {
    forgetSnapshot(report.target);
    setSaved("forgotten");
  }

  const status =
    saved === "forgotten"
      ? t.progress.forgotten
      : saved === "failed"
        ? t.progress.storageFailed
        : saved === "yes" && !previous
          ? t.progress.remembered
          : "";

  const forgetButton = saved === "yes" && (
    <button
      type="button"
      onClick={forget}
      className="mt-6 min-h-11 cursor-pointer rounded-xs border border-ink px-5 font-semibold"
    >
      {t.progress.forget}
    </button>
  );

  if (!previous) {
    return (
      <Section labelledBy={titleId} rail={<Label>{t.progress.rail}</Label>} className="print:hidden">
        <div className="max-w-[760px]">
          <h2 id={titleId} className="font-serif text-2xl leading-8 font-semibold">
            {t.progress.offerTitle}
          </h2>
          <p className="mt-2">{t.progress.offerText}</p>
          {saved === "no" && (
            <button
              type="button"
              onClick={remember}
              className="mt-6 min-h-11 cursor-pointer rounded-xs border border-ink px-5 font-semibold"
            >
              {t.progress.remember}
            </button>
          )}
          {forgetButton}
          <p role="status" className="mt-3 text-sm">
            {status}
          </p>
        </div>
      </Section>
    );
  }

  const change = compare(previous, report);
  const delta = change.scoreDelta > 0 ? `+${change.scoreDelta}` : String(change.scoreDelta);
  const unchanged = change.fixed.length === 0 && change.added.length === 0 && change.scoreDelta === 0;
  const date = new Intl.DateTimeFormat(DATE_LOCALES[locale], DATE_OPTIONS).format(
    new Date(previous.finishedAt),
  );

  return (
    <Section labelledBy={titleId} rail={<Label>{t.progress.rail}</Label>}>
      <div className="max-w-[760px]">
        <h2 id={titleId} className="font-serif text-2xl leading-8 font-semibold md:text-[28px] md:leading-9">
          {t.progress.title}
        </h2>
        <p className="mt-1 text-sm text-muted">{t.progress.lastCheck(date)}</p>

        <dl className="mt-5 grid grid-cols-[max-content_minmax(0,1fr)] gap-x-6 gap-y-1 border-t border-ink pt-3">
          <dt className="text-muted">{t.progress.score}</dt>
          <dd dir="ltr" className="text-start font-mono">
            {previous.score} → {report.score}{" "}
            <span className={change.scoreDelta > 0 ? "text-pass" : change.scoreDelta < 0 ? "text-high" : ""}>
              ({delta})
            </span>
          </dd>
          <dt className="text-muted">{t.progress.grade}</dt>
          <dd dir="ltr" className="text-start font-mono">
            {previous.grade} → {report.grade}
          </dd>
        </dl>

        {unchanged ? (
          <p className="mt-5">{t.progress.noChange}</p>
        ) : (
          <>
            <IssueList kind="fixed" title={t.progress.fixed(change.fixed.length)} items={change.fixed} />
            <IssueList kind="added" title={t.progress.added(change.added.length)} items={change.added} />
          </>
        )}
        <p className="mt-5 text-sm">{t.progress.remaining(change.remaining)}</p>

        <div className="print:hidden">
          {forgetButton}
          <p role="status" className="mt-3 text-sm">
            {status}
          </p>
        </div>
      </div>
    </Section>
  );
}

function IssueList({ kind, title, items }: { kind: "fixed" | "added"; title: string; items: IssueSummary[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-6">
      <h3 className={`font-semibold ${kind === "fixed" ? "text-pass" : "text-high"}`}>{title}</h3>
      <ul className="mt-2 border-t border-rule">
        {items.map((item) => (
          <li key={item.id} className="flex flex-wrap items-baseline gap-x-4 gap-y-1 border-b border-rule py-2.5">
            {kind === "added" && (
              <span className="shrink-0">
                <SeverityMark kind={item.severity} />
              </span>
            )}
            <span className={kind === "fixed" ? "text-muted line-through decoration-1" : ""}>{item.headline}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
