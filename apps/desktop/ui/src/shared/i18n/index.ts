import { create } from "zustand"
import jaLocale from "./locales/ja.json"
import enLocale from "./locales/en.json"

export type Locale = "ja" | "en"

export const LOCALE_LABELS: Record<Locale, string> = {
  ja: "日本語",
  en: "English",
}

type Messages = typeof jaLocale

export const locales: Record<Locale, Messages> = {
  ja: jaLocale,
  en: enLocale as unknown as Messages,
}

interface I18nState {
  locale: Locale
  messages: Messages
  setLocale: (locale: Locale) => void
}

function getInitialLocale(): Locale {
  try {
    const stored = localStorage.getItem("locale")
    if (stored === "ja" || stored === "en") return stored
  } catch {
    // localStorage unavailable (SSR or restricted context)
  }
  const browserLang = navigator.language.toLowerCase()
  if (browserLang.startsWith("ja")) return "ja"
  return "en"
}

export const useI18n = create<I18nState>((set) => {
  const initial = getInitialLocale()
  return {
    locale: initial,
    messages: locales[initial],
    setLocale: (locale: Locale) => {
      try { localStorage.setItem("locale", locale) } catch { /* noop */ }
      document.documentElement.lang = locale
      set({ locale, messages: locales[locale] })
    },
  }
})

/** Convenience hook that returns only the messages object */
export function useT() {
  return useI18n((s) => s.messages)
}
