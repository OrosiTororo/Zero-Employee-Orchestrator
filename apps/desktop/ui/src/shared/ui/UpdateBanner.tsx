/**
 * アプリ内アップデート通知バナー.
 *
 * 新しいバージョンが利用可能な場合、画面下部に通知を表示する。
 * 自動アップデートが有効な場合、ダウンロード＆インストールの進捗を表示する。
 */
import { Download, X, RefreshCw, CheckCircle } from "lucide-react"
import { useUpdater } from "@/shared/hooks/use-updater"
import { useT } from "@/shared/i18n"

export function UpdateBanner() {
  const t = useT()
  const {
    available,
    downloading,
    installing,
    progress,
    info,
    error,
    dismissed,
    downloadAndInstall,
    dismiss,
  } = useUpdater()

  // Show banner when: update available (not dismissed), downloading, installing, or error
  const showBanner =
    (available && !dismissed) || downloading || installing || (error && !dismissed)

  if (!showBanner) return null

  return (
    <div
      className="fixed bottom-8 right-8 z-50 max-w-sm rounded-lg border shadow-2xl"
      style={{
        background: "var(--bg-surface, #1e1e1e)",
        borderColor: "var(--border, #333)",
      }}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            {installing ? (
              <CheckCircle size={16} className="text-green-400 shrink-0" />
            ) : (
              <Download size={16} className="text-[var(--accent)] shrink-0" />
            )}
            <span className="text-[13px] font-medium text-[var(--text-primary,#fff)]">
              {error
                ? t.updater.checkFailed
                : installing
                  ? t.updater.installing
                  : downloading
                    ? t.updater.updating
                    : t.updater.available}
            </span>
          </div>
          {!downloading && !installing && (
            <button
              onClick={dismiss}
              className="text-[var(--text-muted,#888)] hover:text-[var(--text-primary,#fff)] transition-colors"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Body */}
        {error ? (
          <p className="mt-2 text-[12px] text-[var(--text-secondary,#aaa)]">
            {error}
          </p>
        ) : info ? (
          <>
            <p className="mt-2 text-[12px] text-[var(--text-secondary,#aaa)]">
              {installing
                ? t.updater.installingVersion.replace("{version}", info.version)
                : t.updater.versionAvailable.replace("{version}", info.version)}
              {info.body && !installing && (
                <span className="block mt-1 line-clamp-2">{info.body}</span>
              )}
            </p>

            {/* Progress bar */}
            {(downloading || installing) && (
              <div className="mt-3 h-1.5 rounded-full bg-[var(--border,#333)] overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${progress}%`,
                    background: installing ? "#4ade80" : "var(--accent)",
                  }}
                />
              </div>
            )}

            {/* Action */}
            <div className="mt-3 flex justify-end">
              {downloading ? (
                <span className="flex items-center gap-1.5 text-[12px] text-[var(--text-secondary,#aaa)]">
                  <RefreshCw size={12} className="animate-spin" />
                  {t.updater.downloading.replace("{progress}", String(progress))}
                </span>
              ) : installing ? (
                <span className="flex items-center gap-1.5 text-[12px] text-green-400">
                  <RefreshCw size={12} className="animate-spin" />
                  {t.updater.restarting}
                </span>
              ) : (
                <button
                  onClick={downloadAndInstall}
                  className="px-3 py-1.5 rounded text-[12px] font-medium text-white transition-colors"
                  style={{ background: "var(--accent)" }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--accent-hover)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = "var(--accent)")
                  }
                >
                  {t.updater.downloadRestart}
                </button>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
