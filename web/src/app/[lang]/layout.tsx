import type { Metadata } from "next";
import {
  IBM_Plex_Mono,
  IBM_Plex_Sans,
  IBM_Plex_Sans_Arabic,
  Noto_Naskh_Arabic,
  Source_Serif_4,
} from "next/font/google";
import Link from "next/link";
import { notFound } from "next/navigation";
import { connection } from "next/server";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { LOCALES, direction, getMessages, isLocale } from "@/i18n";
import { I18nProvider } from "@/i18n/client";

import "../globals.css";

// Fonts are self-hosted at build time: visitors' browsers never contact Google.
const serif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
  weight: ["600", "700"],
});
const sans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "600"],
});
const mono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});
// Arabic glyphs fall back to these. Not preloaded: only Arabic pages download them.
const sansArabic = IBM_Plex_Sans_Arabic({
  variable: "--font-plex-arabic",
  subsets: ["arabic"],
  weight: ["400", "600"],
  preload: false,
});
const serifArabic = Noto_Naskh_Arabic({
  variable: "--font-naskh-arabic",
  subsets: ["arabic"],
  weight: ["600", "700"],
  preload: false,
});

const FONT_VARIABLES = [serif, sans, mono, sansArabic, serifArabic].map((f) => f.variable).join(" ");
const SOURCE_URL = process.env.NEXT_PUBLIC_VIGILO_SOURCE_URL ?? "https://github.com/";

export async function generateMetadata({ params }: LayoutProps<"/[lang]">): Promise<Metadata> {
  const { lang } = await params;
  if (!isLocale(lang)) return {};
  const t = getMessages(lang);
  return {
    title: t.meta.title,
    description: t.meta.description,
    alternates: {
      languages: Object.fromEntries(LOCALES.map((code) => [code, `/${code}`])),
    },
  };
}

export default async function RootLayout({ children, params }: LayoutProps<"/[lang]">) {
  // Render per request: the CSP nonce set in proxy.ts must reach every script tag.
  await connection();
  const { lang } = await params;
  if (!isLocale(lang)) notFound();
  const t = getMessages(lang);

  return (
    <html lang={lang} dir={direction(lang)} className={FONT_VARIABLES}>
      <body className="flex min-h-screen flex-col">
        <I18nProvider locale={lang}>
          <header className="border-b-2 border-ink print:border-b">
            <div className="mx-auto flex min-h-16 max-w-[1120px] flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-3 md:px-20 print:px-0">
              <Link
                href={`/${lang}`}
                dir="ltr"
                className="font-serif text-[22px] font-bold tracking-[0.02em] no-underline"
              >
                Vigilo
              </Link>
              <div className="flex flex-wrap items-center gap-x-8 gap-y-2">
                <nav aria-label={t.nav.label} className="flex gap-6 text-sm print:hidden">
                  <Link href={`/${lang}`}>{t.nav.newCheck}</Link>
                  <Link href={`/${lang}/method`}>{t.nav.method}</Link>
                </nav>
                <LanguageSwitcher />
              </div>
            </div>
          </header>

          <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 pb-16 md:px-20 print:px-0">
            {children}
          </main>

          <footer className="mx-auto w-full max-w-[1120px] px-4 pb-10 md:px-20 print:hidden">
            <div className="grid grid-cols-1 gap-y-2 border-t-2 border-ink pt-5 text-sm md:grid-cols-[160px_minmax(0,1fr)] md:gap-x-12">
              <span dir="ltr" className="font-serif font-bold">
                Vigilo
              </span>
              <div className="flex flex-wrap justify-between gap-x-6 gap-y-2 text-muted">
                <span>{t.footer.note}</span>
                <span className="flex gap-5">
                  <Link href={`/${lang}/method`}>{t.nav.method}</Link>
                  <a href={SOURCE_URL}>{t.nav.source}</a>
                </span>
              </div>
            </div>
          </footer>
        </I18nProvider>
      </body>
    </html>
  );
}
