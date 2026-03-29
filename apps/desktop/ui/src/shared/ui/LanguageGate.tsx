import { useI18n, type Locale } from "@/shared/i18n"
import { LogoMark } from "@/shared/ui/Logo"

/**
 * Shows a full-screen language picker on first launch (before anything else).
 * Title and subtitle are shown in multiple languages so all users can understand.
 * Once the user picks a language it is persisted and this gate never appears again.
 */
export function LanguageGate({ children }: { children: React.ReactNode }) {
  const { localeChosen, setLocale } = useI18n()

  if (localeChosen) {
    return <>{children}</>
  }

  const languages: { locale: Locale; label: string; native: string }[] = [
    { locale: "en", label: "English", native: "English" },
    { locale: "ja", label: "Japanese", native: "日本語" },
    { locale: "zh", label: "Chinese", native: "中文" },
    { locale: "ko", label: "Korean", native: "한국어" },
    { locale: "pt", label: "Portuguese", native: "Português" },
    { locale: "tr", label: "Turkish", native: "Türkçe" },
  ]

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
      <div className="flex flex-col items-center gap-6 max-w-sm text-center">
        <LogoMark size={40} />
        <div>
          <h1 className="text-[18px] font-semibold text-[var(--text-primary)] leading-relaxed">
            Choose your language
          </h1>
          {/* Show the title in key languages so non-English speakers understand */}
          <p className="text-[13px] text-[var(--text-muted)] mt-1 leading-relaxed">
            言語を選択 / 选择语言 / 언어 선택
          </p>
          <p className="text-[12px] text-[var(--text-muted)] mt-2 opacity-75">
            You can change this later in Settings.
          </p>
        </div>
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
