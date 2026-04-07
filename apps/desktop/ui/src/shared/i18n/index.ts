import { create } from "zustand"
import jaLocale from "./locales/ja.json"
import enLocale from "./locales/en.json"
import zhLocale from "./locales/zh.json"
import koLocale from "./locales/ko.json"
import ptLocale from "./locales/pt.json"
import trLocale from "./locales/tr.json"

export type Locale = "ja" | "en" | "zh" | "ko" | "pt" | "tr"

/** Locale codes bundled with the application (changeable in Settings) */
export const BUNDLED_LOCALES: ReadonlySet<string> = new Set<string>(["en", "ja", "zh", "ko", "pt", "tr"])

export const LOCALE_LABELS: Record<string, string> = {
  ja: "日本語",
  en: "English",
  zh: "中文",
  ko: "한국어",
  pt: "Português",
  tr: "Türkçe",
}

type Messages = typeof jaLocale

export const locales: Record<string, Messages> = {
  ja: jaLocale,
  en: enLocale as unknown as Messages,
  zh: zhLocale as unknown as Messages,
  ko: koLocale as unknown as Messages,
  pt: ptLocale as unknown as Messages,
  tr: trLocale as unknown as Messages,
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
 * Set of locale codes currently visible to the user.
 * Starts with only the active (installer-selected or OS-detected) locale.
 * Additional languages are enabled via Settings → Extensions → Language Pack,
 * or by calling enableLocale() / loadLanguagePack().
 */
function getInitialAvailable(): Set<string> {
  // Restore previously enabled locales from localStorage
  try {
    const stored = localStorage.getItem("enabled_locales")
    if (stored) {
      const parsed = JSON.parse(stored) as string[]
      if (Array.isArray(parsed) && parsed.length > 0) {
        return new Set(parsed.filter(c => c in locales))
      }
    }
  } catch { /* noop */ }
  // Default: only the detected/saved locale
  try {
    const saved = localStorage.getItem("locale")
    if (saved && saved in locales) return new Set([saved])
  } catch { /* noop */ }
  const detected = detectLocaleFromOS()
  return new Set([detected])
}

export const availableLocales = getInitialAvailable()

/** Make a bundled locale visible in Settings. */
export function enableLocale(code: string): boolean {
  if (!(code in locales)) return false
  availableLocales.add(code)
  try {
    localStorage.setItem("enabled_locales", JSON.stringify([...availableLocales]))
  } catch { /* noop */ }
  return true
}

/** Remove a locale from the visible list (cannot remove the active locale). */
export function disableLocale(code: string): boolean {
  const current = useI18n.getState().locale
  if (code === current) return false
  availableLocales.delete(code)
  try {
    localStorage.setItem("enabled_locales", JSON.stringify([...availableLocales]))
  } catch { /* noop */ }
  return true
}

function isValidLocale(s: string): s is Locale {
  return s in locales
}

interface I18nState {
  locale: Locale
  messages: Messages
  setLocale: (locale: Locale) => void
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
  availableLocales.add(initial) // ensure active locale is always visible
  document.documentElement.lang = initial
  return {
    locale: initial,
    messages: locales[initial],
    setLocale: (locale: Locale) => {
      if (!(locale in locales)) {
        console.warn(`Locale "${locale}" is not available. Load it first with loadLanguagePack().`)
        return
      }
      // Ensure the locale is visible in Settings
      availableLocales.add(locale)
      try {
        localStorage.setItem("locale", locale)
        localStorage.setItem("enabled_locales", JSON.stringify([...availableLocales]))
      } catch { /* noop */ }
      document.documentElement.lang = locale
      set({ locale, messages: locales[locale] })
    },
  }
})

/**
 * Load a language pack from the API for a non-builtin language.
 *
 * Built-in locales (en, ja, zh, ko, pt, tr) are already bundled and do not
 * need loading. This function is for truly new languages added via extensions
 * or the marketplace.
 *
 * @param code - BCP 47 language code (e.g. "fr", "de", "es")
 * @param apiBase - Base URL for the API (defaults to current origin)
 * @returns true if the language pack was loaded successfully
 */
export async function loadLanguagePack(
  code: string,
  apiBase = "/api/v1",
): Promise<boolean> {
  // If it's a bundled locale, just enable it
  if (code in locales) {
    enableLocale(code)
    return true
  }

  if (availableLocales.has(code)) {
    return true
  }

  try {
    const resp = await fetch(`${apiBase}/language-packs/${code}/messages`)
    if (!resp.ok) {
      console.warn(`Failed to load language pack "${code}": ${resp.status}`)
      return false
    }
    const messages = (await resp.json()) as Messages
    locales[code] = messages
    availableLocales.add(code)
    LOCALE_LABELS[code] = messages.common?.appName ?? code
    return true
  } catch (err) {
    console.warn(`Failed to load language pack "${code}":`, err)
    return false
  }
}

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
    const internals = (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__ as
      | { invoke: (cmd: string) => Promise<string | null> }
      | undefined
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
