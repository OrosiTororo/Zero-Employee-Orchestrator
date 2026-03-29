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

/** All known locale codes for validation */
const KNOWN_LOCALES = new Set<string>(Object.keys(locales))

function isValidLocale(s: string): s is Locale {
  return KNOWN_LOCALES.has(s)
}

interface I18nState {
  locale: Locale
  messages: Messages
  setLocale: (locale: Locale) => void
}

function detectLocaleFromOS(): Locale {
  const browserLang = navigator.language.toLowerCase()
  if (browserLang.startsWith("ja")) return "ja"
  if (browserLang.startsWith("zh")) return "zh"
  if (browserLang.startsWith("ko")) return "ko"
  if (browserLang.startsWith("pt")) return "pt"
  if (browserLang.startsWith("tr")) return "tr"
  return "en"
}

/**
 * Determine initial locale. Priority:
 * 1. User preference saved in localStorage (from Settings)
 * 2. OS language detection (matches installer language on first launch)
 */
function getInitialLocale(): Locale {
  try {
    const stored = localStorage.getItem("locale")
    if (stored && isValidLocale(stored)) return stored
  } catch {
    // localStorage unavailable
  }
  return detectLocaleFromOS()
}

export const useI18n = create<I18nState>((set) => {
  const initial = getInitialLocale()
  document.documentElement.lang = initial
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

/**
 * On Tauri (desktop), try to read the installer-selected locale and apply it
 * if the user hasn't already set a preference via Settings.
 * This runs once at startup and is a no-op on non-Tauri environments.
 */
export async function applyInstallerLocale(): Promise<void> {
  // Skip if user already has a saved preference
  try {
    if (localStorage.getItem("locale")) return
  } catch {
    return
  }

  const isTauri =
    typeof window !== "undefined" && "__TAURI_INTERNALS__" in window
  if (!isTauri) return

  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const internals = (window as any).__TAURI_INTERNALS__
    if (!internals?.invoke) return
    const installerLocale = await internals.invoke("get_installer_locale")
    if (installerLocale && isValidLocale(installerLocale)) {
      useI18n.getState().setLocale(installerLocale)
    }
  } catch {
    // Not critical — OS detection already applied
  }
}

/** Convenience hook that returns only the messages object */
export function useT() {
  return useI18n((s) => s.messages)
}
