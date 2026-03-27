import { create } from "zustand"
import jaLocale from "./locales/ja.json"
import enLocale from "./locales/en.json"
import zhLocale from "./locales/zh.json"
import koLocale from "./locales/ko.json"
import ptLocale from "./locales/pt.json"
import trLocale from "./locales/tr.json"

export type Locale = "ja" | "en" | "zh" | "ko" | "pt" | "tr"

export const LOCALE_LABELS: Record<Locale, string> = {
  ja: "日本語",
  en: "English",
  zh: "中文",
  ko: "한국어",
  pt: "Português",
  tr: "Türkçe",
}

type Messages = typeof jaLocale

export const locales: Record<Locale, Messages> = {
  ja: jaLocale,
  en: enLocale as unknown as Messages,
  zh: zhLocale as unknown as Messages,
  ko: koLocale as unknown as Messages,
  pt: ptLocale as unknown as Messages,
  tr: trLocale as unknown as Messages,
}

interface I18nState {
  locale: Locale
  messages: Messages
  setLocale: (locale: Locale) => void
}

function getInitialLocale(): Locale {
  try {
    const stored = localStorage.getItem("locale")
    if (stored && stored in locales) return stored as Locale
  } catch {
    // localStorage unavailable (SSR or restricted context)
  }
  const browserLang = navigator.language.toLowerCase()
  if (browserLang.startsWith("ja")) return "ja"
  if (browserLang.startsWith("zh")) return "zh"
  if (browserLang.startsWith("ko")) return "ko"
  if (browserLang.startsWith("pt")) return "pt"
  if (browserLang.startsWith("tr")) return "tr"
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
