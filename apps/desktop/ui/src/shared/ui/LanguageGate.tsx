import { useI18n, LOCALE_LABELS, type Locale } from "@/shared/i18n"
import { LogoMark } from "@/shared/ui/Logo"

/**
 * Full-screen language picker component.
 * Not used in the main startup flow (language is auto-detected from OS/installer).
 * Available for use in Settings or other contexts where manual language selection is needed.
 */
export function LanguageGate() {
  const { setLocale } = useI18n()

  const languages: { locale: Locale; native: string }[] = (
    Object.entries(LOCALE_LABELS) as [Locale, string][]
  ).map(([locale, native]) => ({ locale, native }))

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
      <div className="flex flex-col items-center gap-6 max-w-sm text-center">
        <LogoMark size={40} />
        <div className="grid grid-cols-2 gap-2 w-full">
          {languages.map(({ locale, native }) => (
            <button
              key={locale}
              onClick={() => setLocale(locale)}
              className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-[14px] font-medium border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-primary)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors"
            >
              {native}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
