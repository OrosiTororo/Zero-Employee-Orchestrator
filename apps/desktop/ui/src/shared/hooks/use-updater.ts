/**
 * Tauri auto-updater hook.
 *
 * アプリ起動時にバックグラウンドで更新チェックを実行し、
 * 新しいバージョンがあればユーザーに通知する。
 */
import { useState, useEffect, useCallback } from "react"

interface UpdateInfo {
  version: string
  date?: string
  body?: string
}

interface UpdaterState {
  checking: boolean
  available: boolean
  downloading: boolean
  progress: number
  info: UpdateInfo | null
  error: string | null
}

const initialState: UpdaterState = {
  checking: false,
  available: false,
  downloading: false,
  progress: 0,
  info: null,
  error: null,
}

/**
 * Tauri の window.__TAURI__ が利用可能かチェックする。
 * ブラウザ (dev server) では利用不可。
 */
function isTauriEnv(): boolean {
  return typeof window !== "undefined" && "__TAURI__" in window
}

export function useUpdater() {
  const [state, setState] = useState<UpdaterState>(initialState)

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
          setState((s) => ({ ...s, progress: 100 }))
        }
      })

      // relaunch after install
      const { relaunch } = await import("@tauri-apps/plugin-process")
      await relaunch()
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setState((s) => ({
        ...s,
        downloading: false,
        error: message,
      }))
    }
  }, [])

  const dismiss = useCallback(() => {
    setState(initialState)
  }, [])

  // 起動時に自動チェック (30秒後、ネットワーク安定待ち)
  useEffect(() => {
    if (!isTauriEnv()) return
    const timer = setTimeout(() => {
      checkForUpdate()
    }, 30_000)
    return () => clearTimeout(timer)
  }, [checkForUpdate])

  return {
    ...state,
    checkForUpdate,
    downloadAndInstall,
    dismiss,
  }
}
