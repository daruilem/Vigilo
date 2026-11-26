"use client";

import { useEffect, useState } from "react";

import { useI18n } from "@/i18n/client";

export function CopyButton({ text, label }: { text: string; label?: string }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(false), 2000);
    return () => window.clearTimeout(timer);
  }, [copied]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      // Clipboard access refused: the code stays selectable by hand.
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={copy}
        className="h-11 min-w-[76px] shrink-0 cursor-pointer border-t border-rule px-3.5 text-sm font-semibold md:border-t-0 md:border-s print:hidden"
      >
        {copied ? t.report.copied : (label ?? t.report.copy)}
      </button>
      <span role="status" className="sr-only">
        {copied ? t.report.copiedAnnouncement : ""}
      </span>
    </>
  );
}
