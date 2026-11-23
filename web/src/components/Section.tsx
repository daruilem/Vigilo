import type { ReactNode } from "react";

interface SectionProps {
  rail: ReactNode;
  children: ReactNode;
  labelledBy?: string;
  first?: boolean;
  className?: string;
}

/**
 * The page grid: a 160 px margin column (section number, label, severity) and the
 * content column. Below 720 px the margin column folds into a row above the content.
 * Sections are separated by a hairline rule, never by cards.
 */
export function Section({ rail, children, labelledBy, first = false, className = "" }: SectionProps) {
  return (
    <section
      aria-labelledby={labelledBy}
      className={`grid grid-cols-1 gap-y-3 md:grid-cols-[160px_minmax(0,1fr)] md:gap-x-12 ${
        first ? "pt-10 pb-8" : "border-t border-rule pt-6 pb-8"
      } ${className}`}
    >
      <div className="flex flex-row items-center gap-4 md:flex-col md:items-start md:gap-1.5">
        {rail}
      </div>
      <div className="min-w-0">{children}</div>
    </section>
  );
}

export function Label({ children, id }: { children: ReactNode; id?: string }) {
  return (
    <span id={id} className="label-caps">
      {children}
    </span>
  );
}

export function SectionNumber({ value }: { value: string }) {
  return <span className="font-mono text-sm">{value}</span>;
}
