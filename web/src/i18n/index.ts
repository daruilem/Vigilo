import { ar } from "./ar";
import { de } from "./de";
import { en, type Messages } from "./en";
import { fr } from "./fr";

export const LOCALES = ["en", "fr", "de", "ar"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";

export const MESSAGES: Record<Locale, Messages> = { en, fr, de, ar };

/** Each language written in its own name, as shown in the language switcher. */
export const LANGUAGE_NAMES: Record<Locale, string> = {
  en: "English",
  fr: "Français",
  de: "Deutsch",
  ar: "العربية",
};

/** Locale used for dates. Arabic keeps Western digits, as used in the Maghreb. */
export const DATE_LOCALES: Record<Locale, string> = {
  en: "en-GB",
  fr: "fr-FR",
  de: "de-DE",
  ar: "ar-u-nu-latn",
};

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

export function direction(locale: Locale): "ltr" | "rtl" {
  return locale === "ar" ? "rtl" : "ltr";
}

export function getMessages(locale: Locale): Messages {
  return MESSAGES[locale];
}

export type { Messages };
