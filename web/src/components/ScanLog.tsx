import { DATE_LOCALES } from "@/i18n";
import { useI18n } from "@/i18n/client";
import type { Step } from "@/lib/types";

const TIME_OPTIONS: Intl.DateTimeFormatOptions = {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
};

const STATE_CLASS: Record<Step["state"], string> = {
  pending: "text-muted",
  running: "text-ink font-medium",
  done: "text-pass",
  failed: "text-high font-medium",
};

/** Execution log: one line per step, updated as the server reports progress. */
export function ScanLog({ steps }: { steps: Step[] }) {
  const { t, locale } = useI18n();
  const timeFormat = new Intl.DateTimeFormat(DATE_LOCALES[locale], TIME_OPTIONS);
  return (
    <ol
      role="log"
      aria-live="polite"
      aria-label={t.scan.logLabel}
      className="border-t border-ink font-mono text-sm leading-5"
    >
      {steps.map((step) => (
        <li
          key={step.id}
          className="grid grid-cols-[72px_minmax(0,1fr)] gap-x-4 gap-y-1 border-b border-rule py-3 sm:grid-cols-[72px_minmax(0,1fr)_120px]"
        >
          <span dir="ltr" className="text-muted">{step.at ? timeFormat.format(step.at) : "--:--:--"}</span>
          <span className={step.state === "pending" ? "text-muted" : ""}>{step.label}</span>
          <span className={`col-start-2 sm:col-start-auto sm:text-end ${STATE_CLASS[step.state]}`}>
            {t.scan.states[step.state]}
          </span>
        </li>
      ))}
    </ol>
  );
}
