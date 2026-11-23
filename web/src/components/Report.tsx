"use client";

import { forwardRef, useId, useState } from "react";

import { fetchReportPdf, pdfFileName } from "@/lib/api";

import { DATE_LOCALES } from "@/i18n";
import { useI18n } from "@/i18n/client";
import { countBySeverity, sectionNumber, splitFindings } from "@/lib/report";
import type { Platform, ScanReport } from "@/lib/types";

import { GradeScale } from "./GradeScale";
import { GradeStamp } from "./GradeStamp";
import { IssueSection } from "./IssueSection";
import { Label, Section, SectionNumber } from "./Section";
import { SeverityMark } from "./SeverityMark";

interface ReportProps {
  report: ScanReport;
  onNewCheck: () => void;
}

const DATE_OPTIONS: Intl.DateTimeFormatOptions = {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZoneName: "short",
};

export const Report = forwardRef<HTMLHeadingElement, ReportProps>(function Report(
  { report, onNewCheck },
  headingRef,
) {
  const { t, locale } = useI18n();
  const { issues, passed, errors } = splitFindings(report.findings);
  const counts = countBySeverity(issues);
  // One hosting choice for the whole report: a site has a single hosting.
  const [platform, setPlatform] = useState<Platform>("apache");
  const [showPassed, setShowPassed] = useState(false);
  const [showScale, setShowScale] = useState(false);
  const scaleId = useId();
  const [pdf, setPdf] = useState<{ state: "idle" | "loading" | "failed"; message?: string }>({ state: "idle" });

  async function downloadPdf() {
    setPdf({ state: "loading" });
    try {
      const blob = await fetchReportPdf(report, locale, platform);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = pdfFileName(report);
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
      setPdf({ state: "idle" });
    } catch (error) {
      setPdf({ state: "failed", message: (error instanceof Error && error.message) || t.report.pdfFailed });
    }
  }
  const passedListId = useId();
  const nextNumber = issues.length;

  return (
    <article aria-labelledby="report-title">
      <Section first rail={<Label>{t.report.rail}</Label>}>
        <div className="flex flex-wrap items-start justify-between gap-8">
          <div className="min-w-0 flex-[1_1_420px]">
            <h1
              id="report-title"
              ref={headingRef}
              tabIndex={-1}
              className="font-serif text-[32px] leading-10 font-semibold md:text-[40px] md:leading-[48px]"
            >
              {t.report.title}
            </h1>
            <p dir="ltr" className="mt-2 font-mono text-base leading-6 wrap-anywhere md:text-xl md:leading-7">
              https://{report.target}/
            </p>
            <dl className="mt-6 grid grid-cols-[max-content_minmax(0,1fr)] gap-x-6 gap-y-1 text-sm">
              <dt className="text-muted">{t.report.checkedOn}</dt>
              <dd className="font-mono">{new Intl.DateTimeFormat(DATE_LOCALES[locale], DATE_OPTIONS).format(new Date(report.finished_at))}</dd>
              <dt className="text-muted">{t.report.method}</dt>
              <dd>{t.report.methodValue}</dd>
              <dt className="text-muted">{t.report.kept}</dt>
              <dd>{t.report.keptValue}</dd>
            </dl>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:flex-wrap print:hidden">
              <button
                type="button"
                onClick={downloadPdf}
                disabled={pdf.state === "loading"}
                aria-busy={pdf.state === "loading"}
                className="h-12 cursor-pointer rounded-xs bg-stamp px-6 font-semibold text-white disabled:cursor-wait disabled:opacity-80"
              >
                {pdf.state === "loading" ? t.report.preparingPdf : t.report.downloadPdf}
              </button>
              <button
                type="button"
                onClick={onNewCheck}
                className="h-12 cursor-pointer rounded-xs border border-ink px-5 font-semibold"
              >
                {t.report.newCheck}
              </button>
            </div>
            <p role="status" className="mt-3 text-sm text-high print:hidden">
              {pdf.state === "failed" ? pdf.message : ""}
            </p>
          </div>

          <div className="flex items-center gap-4 md:flex-col md:gap-3">
            <GradeStamp grade={report.grade} />
            <div className="md:text-center">
              <p className="font-semibold">{t.report.issuesCount(issues.length)}</p>
              {counts.length > 0 && (
                <p className="text-sm text-muted">
                  {counts.map(([severity, n]) => `${n} ${t.severity[severity].toLowerCase()}`).join(" · ")}
                </p>
              )}
              <button
                type="button"
                aria-expanded={showScale}
                aria-controls={scaleId}
                onClick={() => setShowScale((v) => !v)}
                className="mt-2 min-h-11 cursor-pointer text-sm underline underline-offset-4 hover:text-stamp print:hidden"
              >
                {showScale ? t.grades.hide : t.grades.toggle(report.grade)}
              </button>
            </div>
          </div>
        </div>
      </Section>

      <div id={scaleId} hidden={!showScale}>
        {showScale && (
          <Section labelledBy={`${scaleId}-title`} rail={<Label>{t.grades.rail}</Label>}>
            <GradeScale id={`${scaleId}-title`} current={report.grade} score={report.score} />
          </Section>
        )}
      </div>

      {issues.length > 0 && (
        <p className="mb-2 text-sm text-muted md:ms-[208px] print:hidden">{t.report.hostingNote}</p>
      )}

      {issues.map((finding, index) => (
        <IssueSection
          key={finding.id}
          finding={finding}
          number={sectionNumber(index)}
          platform={platform}
          onPlatformChange={setPlatform}
        />
      ))}

      {issues.length === 0 && (
        <Section rail={<SeverityMark kind="pass" />}>
          <p className="max-w-[760px]">{t.report.allClear}</p>
        </Section>
      )}

      {errors.length > 0 && (
        <Section
          labelledBy="errors-title"
          rail={
            <>
              <SectionNumber value={sectionNumber(nextNumber)} />
              <SeverityMark kind="note" />
            </>
          }
        >
          <div className="max-w-[760px]">
            <h2 id="errors-title" className="font-serif text-2xl leading-8 font-semibold md:text-[28px] md:leading-9">
              {t.report.notChecked(errors.length)}
            </h2>
            <p className="mt-2">{t.report.notCheckedIntro}</p>
            <ul className="mt-3 border-t border-ink">
              {errors.map((f) => (
                <li key={f.id} className="border-b border-rule py-3">
                  {f.title}
                </li>
              ))}
            </ul>
          </div>
        </Section>
      )}

      {passed.length > 0 && (
        <Section
          labelledBy="passed-title"
          rail={
            <>
              <SectionNumber value={sectionNumber(nextNumber + (errors.length > 0 ? 1 : 0))} />
              <SeverityMark kind="pass" />
            </>
          }
        >
          <div className="max-w-[760px]">
            <h2 id="passed-title">
              <button
                type="button"
                aria-expanded={showPassed}
                aria-controls={passedListId}
                onClick={() => setShowPassed((v) => !v)}
                className="flex min-h-11 cursor-pointer items-center gap-3 text-start font-serif text-2xl leading-8 font-semibold md:text-[28px] md:leading-9"
              >
                <span aria-hidden="true" className="w-5 font-mono text-xl print:hidden">
                  {showPassed ? "−" : "+"}
                </span>
                <span>{t.report.passed(passed.length)}</span>
              </button>
            </h2>
            <ul
              id={passedListId}
              className={`mt-3 border-t border-ink ${showPassed ? "" : "hidden print:block"}`}
            >
              {passed.map((f) => (
                <li
                  key={f.id}
                  className="grid grid-cols-1 gap-x-6 border-b border-rule py-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]"
                >
                  <span className="flex items-start gap-2">
                    {f.status === "info" && <span className="sr-only">{t.severity.note}: </span>}
                    <span>{f.headline ?? f.title}</span>
                  </span>
                  <span
                    className={`font-mono text-sm leading-6 break-words ${
                      f.status === "info" ? "text-muted" : "text-pass"
                    }`}
                  >
                    {f.observed.map((o) => `${o.label}: ${o.value}`).join(" · ")}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </Section>
      )}
    </article>
  );
});
