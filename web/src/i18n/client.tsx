"use client";

import { createContext, useContext, type ReactNode } from "react";

import { DEFAULT_LOCALE, MESSAGES, type Locale, type Messages } from "./index";

interface I18n {
  locale: Locale;
  t: Messages;
}

const I18nContext = createContext<I18n>({ locale: DEFAULT_LOCALE, t: MESSAGES[DEFAULT_LOCALE] });

/**
 * Gives client components the current language. Only the locale crosses the
 * server/client boundary: the dictionaries contain functions, so they are looked up here.
 */
export function I18nProvider({ locale, children }: { locale: Locale; children: ReactNode }) {
  return <I18nContext.Provider value={{ locale, t: MESSAGES[locale] }}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18n {
  return useContext(I18nContext);
}
