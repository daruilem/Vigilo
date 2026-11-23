"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { LANGUAGE_NAMES, LOCALES } from "@/i18n";
import { useI18n } from "@/i18n/client";

/** Links to the same page in every language. The current one is marked, not linked. */
export function LanguageSwitcher() {
  const { locale, t } = useI18n();
  const pathname = usePathname() ?? `/${locale}`;
  const rest = pathname.split("/").slice(2).join("/");

  return (
    <nav aria-label={t.nav.language} className="print:hidden">
      <ul className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        {LOCALES.map((code) => (
          <li key={code}>
            {code === locale ? (
              <span aria-current="true" lang={code} className="font-semibold underline decoration-2 underline-offset-4">
                {LANGUAGE_NAMES[code]}
              </span>
            ) : (
              <Link href={`/${code}${rest ? `/${rest}` : ""}`} lang={code} hrefLang={code} className="no-underline hover:underline">
                {LANGUAGE_NAMES[code]}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}
