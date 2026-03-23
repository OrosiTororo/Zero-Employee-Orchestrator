/**
 * アプリ内アップデート通知バナー.
 *
 * 新しいバージョンが利用可能な場合、画面下部に通知を表示する。
 */
import { Download, X, RefreshCw } from "lucide-react"
import { useUpdater } from "@/shared/hooks/use-updater"

export function UpdateBanner() {
  const {
    available,
    downloading,
    progress,
    info,
    error,
    downloadAndInstall,
    dismiss,
  } = useUpdater()

  if (!available && !error) return null

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
            <Download size={16} className="text-[#0078d4] shrink-0" />
            <span className="text-[13px] font-medium text-[var(--text-primary,#fff)]">
              {error ? "Update check failed" : "Update available"}
            </span>
          </div>
          <button
            onClick={dismiss}
            className="text-[var(--text-muted,#888)] hover:text-[var(--text-primary,#fff)] transition-colors"
          >
            <X size={14} />
          </button>
        </div>

        {/* Body */}
        {error ? (
          <p className="mt-2 text-[12px] text-[var(--text-secondary,#aaa)]">
            {error}
          </p>
        ) : info ? (
          <>
            <p className="mt-2 text-[12px] text-[var(--text-secondary,#aaa)]">
              Version {info.version} is available.
              {info.body && (
                <span className="block mt-1 line-clamp-2">{info.body}</span>
              )}
            </p>

            {/* Progress bar */}
            {downloading && (
              <div className="mt-3 h-1.5 rounded-full bg-[var(--border,#333)] overflow-hidden">
                <div
                  className="h-full rounded-full bg-[#0078d4] transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            )}

            {/* Action */}
            <div className="mt-3 flex justify-end">
              {downloading ? (
                <span className="flex items-center gap-1.5 text-[12px] text-[var(--text-secondary,#aaa)]">
                  <RefreshCw size={12} className="animate-spin" />
                  Downloading... {progress}%
                </span>
              ) : (
                <button
                  onClick={downloadAndInstall}
                  className="px-3 py-1.5 rounded text-[12px] font-medium text-white transition-colors"
                  style={{ background: "#0078d4" }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "#006abc")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = "#0078d4")
                  }
                >
                  Download & Restart
                </button>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
