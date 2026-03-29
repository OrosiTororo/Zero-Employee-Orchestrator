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

/** Phase labels mapped from the Rust sidecar's startup phases. */
const PHASE_ORDER = [
  "initializing",
  "finding_api",
  "preparing",
  "python",
  "starting",
  "health_check",
  "ready",
] as const

type Phase = (typeof PHASE_ORDER)[number]

/** Step number (1-based) for each phase, for "Step X of Y" display. */
const PHASE_STEP: Record<string, number> = {
  initializing: 1,
  finding_api: 1,
  preparing: 2,
  python: 3,
  starting: 4,
  health_check: 5,
  waiting: 5,
  ready: 5,
}
const TOTAL_STEPS = 5

/** Convert a phase string to a progress percentage (0-100). */
function phaseToProgress(phase: string): number {
  const idx = PHASE_ORDER.indexOf(phase as Phase)
  if (phase === "ready") return 100
  if (phase === "waiting") return 85
  if (idx < 0) return 10
  return Math.round(((idx + 1) / PHASE_ORDER.length) * 90)
}

/**
 * Check backend health via Tauri native command (bypasses CORS).
 * Returns true if the backend HTTP endpoint responds with 200.
 */
async function checkHealthViaTauri(): Promise<boolean> {
  try {
    const result = await tauriInvoke<string>("check_backend_health")
    return result === "ok"
  } catch {
    return false
  }
}

/**
 * Poll until the backend is ready, using the Tauri native command when available.
 * This avoids CORS issues that can cause fetch() to fail in the webview.
 */
async function waitForBackendSmart(
  maxAttempts: number,
  intervalMs: number,
): Promise<boolean> {
  if (!isTauri) {
    return waitForBackend(maxAttempts, intervalMs)
  }
  for (let i = 0; i < maxAttempts; i++) {
    if (await checkHealthViaTauri()) return true
    if (i < maxAttempts - 1) {
      await new Promise((r) => setTimeout(r, intervalMs))
    }
  }
  return false
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
  const [phase, setPhase] = useState("initializing")
  const [progress, setProgress] = useState(5)
  const [elapsedSec, setElapsedSec] = useState(0)
  const [errorDetail, setErrorDetail] = useState<string | null>(null)
  // Micro-progress: smoothly interpolate between phase progress targets
  const [targetProgress, setTargetProgress] = useState(5)
  const retryCount = useRef(0)
  const checkingRef = useRef(false)
  const maxAutoRetries = isTauri ? 5 : 0
  const startTimeRef = useRef(Date.now())

  // Elapsed time timer
  useEffect(() => {
    if (status !== "checking") return
    const timer = setInterval(() => {
      const sec = Math.floor((Date.now() - startTimeRef.current) / 1000)
      setElapsedSec(sec)
      // Non-Tauri: simulate smooth progress based on elapsed time (caps at 85%)
      if (!isTauri) {
        setProgress(Math.min(85, Math.round(10 + sec * 2.5)))
      }
    }, 1000)
    return () => clearInterval(timer)
  }, [status])

  // Smooth progress interpolation for Tauri mode:
  // Gradually increase progress toward targetProgress so it doesn't look frozen.
  useEffect(() => {
    if (!isTauri || status !== "checking") return
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= targetProgress) return prev
        // Move ~20% of remaining distance each tick (ease-out feel)
        const step = Math.max(1, Math.ceil((targetProgress - prev) * 0.2))
        return Math.min(targetProgress, prev + step)
      })
    }, 300)
    return () => clearInterval(timer)
  }, [targetProgress, status])

  // Poll startup phase from Tauri sidecar for progress display
  useEffect(() => {
    if (!isTauri || status !== "checking") return
    const timer = setInterval(async () => {
      try {
        const p = await tauriInvoke<string>("get_startup_phase")
        if (p) {
          setPhase(p)
          setTargetProgress(phaseToProgress(p))
        }
      } catch {
        // Tauri command not ready yet — ignore
      }
    }, 500)
    return () => clearInterval(timer)
  }, [status])

  /** Get a user-friendly message for the current phase. */
  const getPhaseMessage = useCallback(
    (p: string): string => {
      switch (p) {
        case "initializing":
        case "finding_api":
          return t.backend.startingBackend
        case "preparing":
          return t.backend.preparingEnv
        case "python":
          return t.backend.settingUpPython
        case "starting":
          return t.backend.launchingServer
        case "health_check":
          return t.backend.checkingHealth
        case "waiting":
          return t.backend.waitingForServer
        default:
          return t.backend.startingBackend
      }
    },
    [t],
  )

  const check = useCallback(async () => {
    // Prevent concurrent check() calls from racing
    if (checkingRef.current) return
    checkingRef.current = true
    startTimeRef.current = Date.now()

    try {
      setStatus("checking")
      setErrorDetail(null)
      setElapsedSec(0)

      // Initial wait: 60s (Tauri) or 30s (browser)
      const attempts = isTauri ? 30 : 15
      const interval = 2000
      const ok = await waitForBackendSmart(attempts, interval)

      if (ok) {
        setStatus("connected")
        setProgress(100)
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
          const retryOk = await waitForBackendSmart(10, 2000)
          if (retryOk) {
            setStatus("connected")
            setProgress(100)
            retryCount.current = 0
            return
          }
        } else {
          // Restart backend and wait 30s
          setPhase("starting")
          setTargetProgress(phaseToProgress("starting"))
          try {
            await tauriInvoke("restart_backend")
            setErrorDetail(null)
          } catch (e) {
            const msg = e instanceof Error ? e.message : String(e)
            setErrorDetail(msg)
            console.error("[BackendGuard] restart_backend failed:", msg)
          }
          const retryOk = await waitForBackendSmart(15, 2000)
          if (retryOk) {
            setStatus("connected")
            setProgress(100)
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
    setPhase("initializing")
    setProgress(5)
    setTargetProgress(5)
    await check()
  }, [check])

  if (status === "connected") {
    return <>{children}</>
  }

  const phaseMessage = getPhaseMessage(phase)
  const showFirstRunNote = isTauri && (phase === "python" || elapsedSec > 15)
  const currentStep = PHASE_STEP[phase] ?? 1
  const stepLabel = t.backend.stepOf
    .replace("{current}", String(currentStep))
    .replace("{total}", String(TOTAL_STEPS))
  const elapsedLabel = t.backend.elapsedTime.replace(
    "{seconds}",
    String(elapsedSec),
  )

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
              {phaseMessage}
            </p>
            {showFirstRunNote && (
              <p className="text-[11px] text-[var(--text-muted)]">
                {t.backend.firstRunNote}
              </p>
            )}
            {/* Progress bar with phase description */}
            <div className="w-56 flex flex-col items-center gap-1.5">
              <div className="w-full h-1.5 rounded-full bg-[var(--border)] overflow-hidden">
                <div
                  className="h-full bg-[var(--accent)] rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="w-full flex items-center justify-between">
                <p className="text-[10px] text-[var(--text-muted)] tabular-nums">
                  {isTauri ? stepLabel : `${progress}%`}
                </p>
                <p className="text-[10px] text-[var(--text-muted)] tabular-nums">
                  {elapsedSec > 0 ? elapsedLabel : `${progress}%`}
                </p>
              </div>
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
