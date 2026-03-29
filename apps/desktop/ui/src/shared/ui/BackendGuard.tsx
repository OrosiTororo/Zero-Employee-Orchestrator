import { useEffect, useState, useCallback, useRef } from "react"
import { waitForBackend } from "@/shared/api/client"
import { LogoMark } from "@/shared/ui/Logo"
import { useT } from "@/shared/i18n"

const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window

function tauriInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const internals = (window as any).__TAURI_INTERNALS__
  if (!internals?.invoke) {
    return Promise.reject(new Error("Tauri runtime not available"))
  }
  return internals.invoke(cmd, args)
}

/**
 * Wraps the entire app and shows a "connecting" screen while the backend is unavailable.
 * In Tauri (Desktop App) mode, auto-setup and restart are handled automatically.
 */
export function BackendGuard({ children }: { children: React.ReactNode }) {
  const t = useT()
  const [status, setStatus] = useState<"checking" | "connected" | "failed">(
    "checking",
  )
  const [setupMessage, setSetupMessage] = useState("")
  const [errorDetail, setErrorDetail] = useState<string | null>(null)
  const retryCount = useRef(0)
  const checkingRef = useRef(false)
  const maxAutoRetries = isTauri ? 5 : 0

  const check = useCallback(async () => {
    // Prevent concurrent check() calls from racing
    if (checkingRef.current) return
    checkingRef.current = true

    try {
      setStatus("checking")
      setErrorDetail(null)

      if (isTauri) {
        setSetupMessage(
          retryCount.current === 0
            ? t.backend.startingBackend
            : t.backend.waitingForStartup,
        )
      }

      // Initial wait: 30s (Tauri) or 15s (browser)
      const attempts = isTauri ? 15 : 15
      const interval = 2000
      const ok = await waitForBackend(attempts, interval)

      if (ok) {
        setStatus("connected")
        retryCount.current = 0
        return
      }

      if (isTauri) {
        try {
          const err = await tauriInvoke<string | null>("get_backend_error")
          if (err) {
            setErrorDetail(err)
          }
        } catch {
          // ignore
        }
      }

      if (isTauri && retryCount.current < maxAutoRetries) {
        retryCount.current += 1
        const attempt = retryCount.current

        if (attempt <= 2) {
          // Extra wait: 20s per retry
          setSetupMessage(t.backend.takingLonger)
          const retryOk = await waitForBackend(10, 2000)
          if (retryOk) {
            setStatus("connected")
            retryCount.current = 0
            return
          }
        } else {
          // Restart backend and wait 30s
          setSetupMessage(t.backend.restartingBackend)
          try {
            await tauriInvoke("restart_backend")
            setErrorDetail(null)
          } catch (e) {
            const msg = e instanceof Error ? e.message : String(e)
            setErrorDetail(msg)
            console.error("[BackendGuard] restart_backend failed:", msg)
          }
          const retryOk = await waitForBackend(15, 2000)
          if (retryOk) {
            setStatus("connected")
            retryCount.current = 0
            return
          }
        }

        // Release lock before recursive retry
        checkingRef.current = false
        await check()
        return
      }

      setStatus("failed")
    } finally {
      checkingRef.current = false
    }
  }, [maxAutoRetries, t])

  useEffect(() => {
    check()
  }, [check])

  const handleRetry = useCallback(async () => {
    retryCount.current = 0
    await check()
  }, [check])

  if (status === "connected") {
    return <>{children}</>
  }

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
      <div className="flex flex-col items-center gap-4 max-w-sm text-center">
        <LogoMark
          size={36}
          className={status === "checking" ? "animate-pulse" : ""}
        />
        {status === "checking" && (
          <>
            <p className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.backend.connecting}
            </p>
            <p className="text-[12px] text-[var(--text-muted)]">
              {isTauri && setupMessage
                ? setupMessage
                : t.backend.waitingForServer}
            </p>
            {isTauri && retryCount.current > 0 && (
              <p className="text-[11px] text-[var(--text-muted)]">
                {t.backend.firstRunNote}
              </p>
            )}
            <div className="w-32 h-1 rounded-full bg-[var(--border)] overflow-hidden">
              <div className="h-full bg-[var(--accent)] rounded-full animate-[loading_2s_ease-in-out_infinite]" />
            </div>
          </>
        )}
        {status === "failed" && (
          <>
            <p className="text-[14px] font-medium text-[var(--text-primary)]">
              {t.backend.cannotConnect}
            </p>
            {isTauri ? (
              <>
                <p className="text-[12px] text-[var(--text-muted)] leading-relaxed">
                  {t.backend.startupFailed}
                </p>
                {errorDetail && (
                  <div className="text-[11px] text-[var(--text-muted)] leading-relaxed text-left bg-[var(--bg-surface)] rounded-md p-3 w-full max-h-32 overflow-y-auto">
                    <p className="mb-1 font-medium">{t.backend.errorDetail}</p>
                    <pre className="whitespace-pre-wrap break-all bg-[var(--bg-base)] px-2 py-1 rounded text-[10px]">
                      {errorDetail}
                    </pre>
                  </div>
                )}
              </>
            ) : (
              <>
                <p className="text-[12px] text-[var(--text-muted)] leading-relaxed">
                  {t.backend.checkBackend}
                </p>
                <div className="text-[11px] text-[var(--text-muted)] leading-relaxed text-left bg-[var(--bg-surface)] rounded-md p-3 w-full">
                  <p className="mb-1.5 font-medium">{t.backend.firstSetup}</p>
                  <code className="block bg-[var(--bg-base)] px-2 py-1 rounded mb-1.5">
                    cd apps/api && uv venv --python 3.12 .venv && uv pip install -e .
                  </code>
                  <p className="mb-1.5 font-medium">{t.backend.startServer}</p>
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
              {t.backend.retry}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
