"use client";

import { useRef, type KeyboardEvent } from "react";

import { useI18n } from "@/i18n/client";
import { PLATFORMS, type Fix, type Platform } from "@/lib/types";

import { CopyButton } from "./CopyButton";

interface FixTabsProps {
  findingId: string;
  fixes: Partial<Record<Platform, Fix>>;
  platform: Platform;
  onPlatformChange: (platform: Platform) => void;
  labelId: string;
}

/** WAI-ARIA tabs: arrow keys, Home and End move between hostings. */
export function FixTabs({ findingId, fixes, platform, onPlatformChange, labelId }: FixTabsProps) {
  const { t } = useI18n();
  const available = PLATFORMS.filter((p) => fixes[p]);
  const active = available.includes(platform) ? platform : available[0];
  const tabs = useRef<Partial<Record<Platform, HTMLButtonElement | null>>>({});
  const base = `fix-${findingId.replace(/[^a-z0-9-]/gi, "-")}`;

  if (!active) return null;
  const fix = fixes[active]!;

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const index = available.indexOf(active!);
    let next: number | null = null;
    if (event.key === "ArrowRight") next = (index + 1) % available.length;
    if (event.key === "ArrowLeft") next = (index - 1 + available.length) % available.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = available.length - 1;
    if (next === null) return;
    event.preventDefault();
    const target = available[next];
    onPlatformChange(target);
    tabs.current[target]?.focus();
  }

  return (
    <div>
      <div
        role="tablist"
        aria-labelledby={labelId}
        className="flex overflow-x-auto print:hidden"
      >
        {available.map((p) => {
          const selected = p === active;
          return (
            <button
              key={p}
              ref={(el) => {
                tabs.current[p] = el;
              }}
              id={`${base}-tab-${p}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`${base}-panel`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onPlatformChange(p)}
              onKeyDown={onKeyDown}
              className={`h-11 shrink-0 cursor-pointer whitespace-nowrap border px-3 text-sm md:px-4 ${
                selected
                  ? "border-ink border-b-transparent font-semibold"
                  : "border-transparent border-b-ink text-muted hover:text-ink"
              }`}
            >
              {t.platforms[p]}
            </button>
          );
        })}
        {/* Continues the bottom rule after the last tab. */}
        <span aria-hidden="true" className="min-w-4 grow border-b border-ink" />
      </div>

      <div
        id={`${base}-panel`}
        role="tabpanel"
        aria-labelledby={`${base}-tab-${active}`}
        className="border border-t-0 border-ink p-3 md:p-4 print:border-t"
      >
        <p className="hidden label-caps print:block print:mb-2">{t.platforms[active]}</p>
        <p className="text-sm">{fix.intro}</p>
        <div className="mt-3 flex flex-col border border-rule md:flex-row md:items-start">
          <pre dir="ltr" className="min-w-0 grow px-3.5 py-3 font-mono text-[13px] leading-5 whitespace-pre-wrap wrap-anywhere">
            <code>{fix.code}</code>
          </pre>
          <CopyButton text={fix.code} />
        </div>
      </div>
    </div>
  );
}
