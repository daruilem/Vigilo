import { useI18n } from "@/i18n/client";
import type { Severity } from "@/lib/types";

export type MarkKind = Severity | "pass" | "note";

/**
 * Each level has its own shape and is always written out, so it reads without colour
 * (colour blindness, black and white printing).
 */
export function SeverityMark({ kind }: { kind: MarkKind }) {
  const { t } = useI18n();
  switch (kind) {
    case "critical":
    case "high":
      return (
        <Mark className="text-high" label={t.severity[kind]}>
          <rect x="0" y="0" width="14" height="14" fill="currentColor" />
        </Mark>
      );
    case "medium":
      return (
        <Mark className="text-medium" label={t.severity.medium}>
          <rect x="1.5" y="1.5" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="3" />
          <rect x="1.5" y="1.5" width="5.5" height="11" fill="currentColor" />
        </Mark>
      );
    case "low":
      return (
        <Mark className="text-muted" label={t.severity.low}>
          <rect x="0.75" y="0.75" width="12.5" height="12.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </Mark>
      );
    case "pass":
      return (
        <Mark className="text-pass" label={t.severity.pass}>
          <path d="M2 7.5 L5.5 11 L12 3" fill="none" stroke="currentColor" strokeWidth="2" />
        </Mark>
      );
    default:
      return (
        <Mark className="text-muted" label={t.severity.note}>
          <circle cx="7" cy="7" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <rect x="6.25" y="6" width="1.5" height="4.5" fill="currentColor" />
          <rect x="6.25" y="3.5" width="1.5" height="1.5" fill="currentColor" />
        </Mark>
      );
  }
}

function Mark({
  className,
  label,
  children,
}: {
  className: string;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        {children}
      </svg>
      <span className="label-caps">{label}</span>
    </span>
  );
}
