import { useEffect, useState, useCallback, useRef } from "react"
import { waitForBackend } from "@/shared/api/client"
import { LogoMark } from "@/shared/ui/Logo"

const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window

/**
 * Invoke a Tauri command via __TAURI_INTERNALS__ (no extra npm dependency needed).
 */
function tauriInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const internals = (window as any).__TAURI_INTERNALS__
  if (!internals?.invoke) {
    return Promise.reject(new Error("Tauri runtime not available"))
  }
  return internals.invoke(cmd, args)
}

/**
 * アプリ全体をラップし、バックエンド未接続時は「接続中」画面を表示する。
 * Tauri (Desktop App) 環境では自動セットアップ・再起動を行い、
 * コマンド操作不要で起動できるようにする。
 */
export function BackendGuard({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<"checking" | "connected" | "failed">(
    "checking",
  )
  const [setupMessage, setSetupMessage] = useState("")
  const retryCount = useRef(0)
  const maxAutoRetries = isTauri ? 3 : 0

  const check = useCallback(async () => {
    setStatus("checking")

    if (isTauri && retryCount.current === 0) {
      setSetupMessage("バックエンドを起動しています...")
    } else if (isTauri) {
      setSetupMessage("バックエンドを再起動しています...")
    }

    // In Tauri mode, wait longer for first-time setup (dependency install)
    const attempts = isTauri ? 30 : 15
    const interval = isTauri ? 2000 : 2000
    const ok = await waitForBackend(attempts, interval)

    if (ok) {
      setStatus("connected")
      retryCount.current = 0
      return
    }

    // In Tauri mode, try restarting the backend automatically
    if (isTauri && retryCount.current < maxAutoRetries) {
      retryCount.current += 1
      setSetupMessage(
        retryCount.current === 1
          ? "初回セットアップ中です。依存関係をインストールしています..."
          : `セットアップを再試行しています... (${retryCount.current}/${maxAutoRetries})`,
      )
      try {
        await tauriInvoke("restart_backend")
      } catch (e) {
        console.error("[BackendGuard] restart_backend failed:", e)
      }
      // Wait for the restarted backend
      const retryOk = await waitForBackend(30, 2000)
      if (retryOk) {
        setStatus("connected")
        retryCount.current = 0
        return
      }
    }

    setStatus("failed")
  }, [maxAutoRetries])

  useEffect(() => {
    check()
  }, [check])

  const handleRetry = useCallback(async () => {
    retryCount.current = 0
    check()
  }, [check])

  if (status === "connected") {
    return <>{children}</>
  }

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
      <div className="flex flex-col items-center gap-4 max-w-xs text-center">
        <LogoMark
          size={36}
          className={status === "checking" ? "animate-pulse" : ""}
        />
        {status === "checking" && (
          <>
            <p className="text-[14px] font-medium text-[var(--text-primary)]">
              バックエンドに接続中...
            </p>
            <p className="text-[12px] text-[var(--text-muted)]">
              {isTauri && setupMessage
                ? setupMessage
                : "サーバーの起動を待っています"}
            </p>
            <div className="w-32 h-1 rounded-full bg-[var(--border)] overflow-hidden">
              <div className="h-full bg-[var(--accent)] rounded-full animate-[loading_2s_ease-in-out_infinite]" />
            </div>
          </>
        )}
        {status === "failed" && (
          <>
            <p className="text-[14px] font-medium text-[var(--text-primary)]">
              サーバーに接続できません
            </p>
            {isTauri ? (
              <>
                <p className="text-[12px] text-[var(--text-muted)] leading-relaxed">
                  バックエンドの自動セットアップに失敗しました。
                  <br />
                  ネットワーク接続を確認して再接続してください。
                </p>
                <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                  初回起動時は必要なツールを自動でインストールします。
                  <br />
                  インターネット接続が必要です。
                </p>
              </>
            ) : (
              <>
                <p className="text-[12px] text-[var(--text-muted)] leading-relaxed">
                  バックエンド API (port 18234) が起動しているか確認してください。
                </p>
                <div className="text-[11px] text-[var(--text-muted)] leading-relaxed text-left bg-[var(--bg-surface)] rounded-md p-3 w-full">
                  <p className="mb-1.5 font-medium">初回セットアップ:</p>
                  <code className="block bg-[var(--bg-base)] px-2 py-1 rounded mb-1.5">
                    cd apps/api && uv venv --python 3.12 .venv && uv pip install -e .
                  </code>
                  <p className="mb-1.5 font-medium">サーバー起動:</p>
                  <code className="block bg-[var(--bg-base)] px-2 py-1 rounded">
                    zero-employee serve --reload
                  </code>
                </div>
              </>
            )}
            <button
              onClick={handleRetry}
              className="mt-2 px-5 py-2 rounded-md text-[13px] font-medium text-white"
              style={{
                background: "linear-gradient(135deg, #0078d4, #6d28d9)",
              }}
            >
              再接続
            </button>
          </>
        )}
      </div>
    </div>
  )
}
