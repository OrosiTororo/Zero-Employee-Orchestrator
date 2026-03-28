import { useEffect, useState, useCallback } from "react"
import { waitForBackend } from "@/shared/api/client"
import { LogoMark } from "@/shared/ui/Logo"

/**
 * アプリ全体をラップし、バックエンド未接続時は「接続中」画面を表示する。
 * 接続確認後は children をレンダリングする。
 */
export function BackendGuard({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<"checking" | "connected" | "failed">(
    "checking",
  )
  const [attempt, setAttempt] = useState(0)

  const check = useCallback(async () => {
    setStatus("checking")
    const ok = await waitForBackend(15, 2000)
    setStatus(ok ? "connected" : "failed")
  }, [])

  useEffect(() => {
    check()
  }, [check, attempt])

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
              サーバーの起動を待っています
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
                ./start.sh
              </code>
            </div>
            <button
              onClick={() => setAttempt((a) => a + 1)}
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
