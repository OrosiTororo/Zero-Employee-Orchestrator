/**
 * Tauri auto-updater hook.
 *
 * アプリ起動時にバックグラウンドで更新チェックを実行し、
 * 新しいバージョンがあれば自動的にダウンロード・インストールする。
 * ユーザーが手動で dismiss した場合も、次回チェック時に再表示する。
 */
import { useState, useEffect, useCallback, useRef } from "react"

interface UpdateInfo {
  version: string
  date?: string
  body?: string
}

interface UpdaterState {
  checking: boolean
  available: boolean
  downloading: boolean
  installing: boolean
  progress: number
  info: UpdateInfo | null
  error: string | null
  dismissed: boolean
}

const initialState: UpdaterState = {
  checking: false,
  available: false,
  downloading: false,
  installing: false,
  progress: 0,
  info: null,
  error: null,
  dismissed: false,
}

/**
 * Tauri の window.__TAURI__ が利用可能かチェックする。
 * ブラウザ (dev server) では利用不可。
 */
function isTauriEnv(): boolean {
  return typeof window !== "undefined" && "__TAURI__" in window
}

/** localStorage key for auto-update preference */
const AUTO_UPDATE_KEY = "zeo-auto-update"

function getAutoUpdatePref(): boolean {
  try {
    const val = localStorage.getItem(AUTO_UPDATE_KEY)
    // Default to true (auto-update enabled)
    return val !== "false"
  } catch {
    return true
  }
}

export function useUpdater() {
  const [state, setState] = useState<UpdaterState>(initialState)
  const autoInstallTriggered = useRef(false)

  const checkForUpdate = useCallback(async () => {
    if (!isTauriEnv()) return

    setState((s) => ({ ...s, checking: true, error: null }))

    try {
      const { check } = await import("@tauri-apps/plugin-updater")
      const update = await check()

      if (update) {
        setState((s) => ({
          ...s,
          checking: false,
          available: true,
          dismissed: false,
          info: {
            version: update.version,
            date: update.date ?? undefined,
            body: update.body ?? undefined,
          },
        }))
      } else {
        setState((s) => ({ ...s, checking: false, available: false }))
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      console.error("[updater] check failed:", message)
      setState((s) => ({
        ...s,
        checking: false,
        error: message,
      }))
    }
  }, [])

  const downloadAndInstall = useCallback(async () => {
    if (!isTauriEnv()) return

    setState((s) => ({ ...s, downloading: true, error: null, progress: 0 }))

    try {
      const { check } = await import("@tauri-apps/plugin-updater")
      const update = await check()

      if (!update) {
        setState((s) => ({ ...s, downloading: false }))
        return
      }

      let totalLen = 0
      let downloaded = 0

      await update.downloadAndInstall((event) => {
        if (event.event === "Started") {
          totalLen = event.data.contentLength ?? 0
        } else if (event.event === "Progress") {
          downloaded += event.data.chunkLength
          const pct = totalLen > 0 ? Math.round((downloaded / totalLen) * 100) : 0
          setState((s) => ({ ...s, progress: pct }))
        } else if (event.event === "Finished") {
          setState((s) => ({ ...s, progress: 100, downloading: false, installing: true }))
        }
      })

      // relaunch after install
      const { relaunch } = await import("@tauri-apps/plugin-process")
      await relaunch()
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      console.error("[updater] download/install failed:", message)
      setState((s) => ({
        ...s,
        downloading: false,
        installing: false,
        error: message,
      }))
    }
  }, [])

  const dismiss = useCallback(() => {
    setState((s) => ({ ...s, dismissed: true }))
  }, [])

  // Auto-install when update is found and auto-update is enabled
  useEffect(() => {
    if (
      state.available &&
      !state.downloading &&
      !state.installing &&
      !autoInstallTriggered.current &&
      getAutoUpdatePref()
    ) {
      autoInstallTriggered.current = true
      downloadAndInstall()
    }
  }, [state.available, state.downloading, state.installing, downloadAndInstall])

  // 起動時に自動チェック (5秒後)
  // + 1時間ごとに定期再チェック
  // + ウィンドウフォーカス時にもチェック
  useEffect(() => {
    if (!isTauriEnv()) return

    const INITIAL_DELAY = 5_000 // 5s
    const RECHECK_INTERVAL = 60 * 60 * 1000 // 1h

    const initialTimer = setTimeout(() => {
      checkForUpdate()
    }, INITIAL_DELAY)

    const intervalTimer = setInterval(() => {
      setState((s) => {
        if (!s.available && !s.downloading && !s.installing) {
          checkForUpdate()
        }
        return s
      })
    }, RECHECK_INTERVAL)

    // ウィンドウフォーカス時にチェック (最低5分間隔)
    let lastFocusCheck = 0
    const FOCUS_MIN_INTERVAL = 5 * 60 * 1000 // 5m
    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        const now = Date.now()
        if (now - lastFocusCheck > FOCUS_MIN_INTERVAL) {
          lastFocusCheck = now
          setState((s) => {
            if (!s.available && !s.downloading && !s.installing) {
              checkForUpdate()
            }
            return s
          })
        }
      }
    }
    document.addEventListener("visibilitychange", handleVisibility)

    return () => {
      clearTimeout(initialTimer)
      clearInterval(intervalTimer)
      document.removeEventListener("visibilitychange", handleVisibility)
    }
  }, [checkForUpdate])

  return {
    ...state,
    checkForUpdate,
    downloadAndInstall,
    dismiss,
  }
}
