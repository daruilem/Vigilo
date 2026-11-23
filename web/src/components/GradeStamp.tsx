import { useI18n } from "@/i18n/client";

/** The verdict: a letter in a double-ruled frame, like an inspection stamp. */
export function GradeStamp({ grade, size = "large" }: { grade: string; size?: "large" | "small" }) {
  const { t } = useI18n();
  const large = size === "large";
  return (
    <div
      role="img"
      aria-label={t.report.gradeLabel(grade)}
      className={`flex flex-col items-center border-4 border-double border-stamp text-stamp ${
        large ? "w-[136px] pt-2.5 pb-3.5" : "w-24 pt-1.5 pb-2"
      }`}
    >
      <span aria-hidden="true" className={`${large ? "text-[11px]" : "text-[10px]"} font-semibold uppercase leading-4 tracking-[0.12em]`}>
        {t.report.grade}
      </span>
      <span
        aria-hidden="true"
        className={`font-serif font-bold ${large ? "text-[88px] leading-[88px]" : "text-[64px] leading-[64px]"}`}
      >
        {grade}
      </span>
    </div>
  );
}
