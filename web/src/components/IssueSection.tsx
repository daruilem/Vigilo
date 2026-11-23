import { useI18n } from "@/i18n/client";
import type { Finding, Platform } from "@/lib/types";

import { FixTabs } from "./FixTabs";
import { Label, Section, SectionNumber } from "./Section";
import { SeverityMark } from "./SeverityMark";

// Mirrors scoring.UNSCORED_CHECKS on the server.
const UNGRADED_CHECK = "privacy";

interface IssueSectionProps {
  finding: Finding;
  number: string;
  platform: Platform;
  onPlatformChange: (platform: Platform) => void;
}

export function IssueSection({ finding, number, platform, onPlatformChange }: IssueSectionProps) {
  const { t } = useI18n();
  const slug = finding.id.replace(/[^a-z0-9-]/gi, "-");
  const headingId = `issue-${slug}`;
  const fixLabelId = `fix-label-${slug}`;
  const hasFixes = Object.keys(finding.fixes).length > 0;

  return (
    <Section
      labelledBy={headingId}
      rail={
        <>
          <SectionNumber value={number} />
          <SeverityMark kind={finding.severity} />
          {finding.check === UNGRADED_CHECK && (
            <span className="text-xs text-muted" title={t.report.notGradedHint}>
              {t.report.notGraded}
            </span>
          )}
        </>
      }
    >
      <div className="flex max-w-[760px] flex-col gap-5">
        <div>
          <h2 id={headingId} className="font-serif text-2xl leading-8 font-semibold md:text-[28px] md:leading-9">
            {finding.headline ?? finding.title}
          </h2>
          {finding.headline && (
            <p className="mt-1 font-mono text-[13px] leading-5 text-muted">{finding.title}</p>
          )}
        </div>

        {finding.observed.length > 0 && (
          <div>
            <p className="mb-2">
              <Label>{t.report.observed}</Label>
            </p>
            <dl className="overflow-x-auto border border-rule px-3.5 py-2.5 font-mono text-sm leading-5">
              {finding.observed.map((o, index) => (
                // Labels repeat (an active scan finding lists several addresses).
                <div key={index} className="flex flex-wrap gap-x-4">
                  <dt dir="auto" className="text-muted">{o.label}</dt>
                  <dd dir="auto" className="font-medium break-all text-high">{o.value}</dd>
                </div>
              ))}
            </dl>
            {finding.note && <p className="mt-1.5 text-sm text-muted">{finding.note}</p>}
          </div>
        )}

        <div>
          <p className="mb-2">
            <Label>{t.report.why}</Label>
          </p>
          <p>{finding.description}</p>
        </div>

        <div>
          <p className="mb-2">
            <Label id={fixLabelId}>{hasFixes ? t.report.fix : t.report.fixFallback}</Label>
          </p>
          {hasFixes ? (
            <FixTabs
              findingId={finding.id}
              fixes={finding.fixes}
              platform={platform}
              onPlatformChange={onPlatformChange}
              labelId={fixLabelId}
            />
          ) : (
            <p>{finding.recommendation}</p>
          )}
          {finding.follow_up && (
            <p className="mt-3 text-sm">
              <span className="font-semibold">{t.report.then} </span>
              {finding.follow_up}
            </p>
          )}
        </div>
      </div>
    </Section>
  );
}
