"use client";

import { useI18n } from "@/i18n/client";

/** Grade boundaries, mirroring scoring.GRADES on the server. */
export const GRADE_BANDS = [
  { letter: "A", range: "90–100" },
  { letter: "B", range: "80–89" },
  { letter: "C", range: "65–79" },
  { letter: "D", range: "50–64" },
  { letter: "F", range: "0–49" },
] as const;

interface GradeScaleProps {
  /** Grade of the checked site, highlighted in the scale. */
  current?: string;
  /** Score of the checked site, out of 100. */
  score?: number;
  headingLevel?: "h2" | "h3";
  id?: string;
}

/** The full A to F scale in plain words, from the best grade to the worst. */
export function GradeScale({ current, score, headingLevel = "h2", id }: GradeScaleProps) {
  const { t } = useI18n();
  const Heading = headingLevel;

  return (
    <div className="max-w-[760px]">
      <Heading id={id} className="font-serif text-2xl leading-8 font-semibold md:text-[28px] md:leading-9">
        {t.grades.title}
      </Heading>
      <p className="mt-2">{t.grades.intro}</p>

      <ol className="mt-4 border-t border-ink">
        {GRADE_BANDS.map(({ letter, range }) => {
          const isCurrent = letter === current;
          return (
            <li
              key={letter}
              aria-current={isCurrent ? "true" : undefined}
              className={`grid grid-cols-[48px_minmax(0,1fr)] gap-x-4 border-b border-rule py-3 sm:grid-cols-[48px_110px_minmax(0,1fr)] ${
                isCurrent ? "border-s-4 border-s-stamp ps-3" : "ps-4"
              }`}
            >
              <span
                aria-hidden="true"
                className="flex size-10 items-center justify-center border-2 border-double border-stamp font-serif text-2xl font-bold text-stamp"
              >
                {letter}
              </span>
              <span className="sr-only">{t.report.gradeLabel(letter)}</span>
              <span dir="ltr" className="self-center font-mono text-sm text-muted sm:text-start">
                {range} {t.grades.points}
              </span>
              <span className="col-start-2 self-center sm:col-start-auto">
                {isCurrent && (
                  <span className="label-caps me-2 inline-block text-stamp">{t.grades.thisSite}</span>
                )}
                <span className={isCurrent ? "font-semibold" : ""}>{t.grades.meanings[letter]}</span>
              </span>
            </li>
          );
        })}
      </ol>

      <p className="mt-4 text-sm">{t.grades.howCalculated}</p>
      {score !== undefined && current && <p className="mt-2 text-sm font-semibold">{t.grades.yourScore(score)}</p>}
    </div>
  );
}
