import { useEffect, useRef, useCallback } from 'react'
import { create } from 'zustand'

// In Tauri use absolute URL; in Vite dev server use relative (proxied via vite.config.ts)
const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window
const WS_BASE = isTauri
  ? "ws://localhost:18234"
  : `ws://${window.location.host}`

interface WSEvent {
  event_type: string
  target_type?: string
  target_id?: string
  data?: Record<string, unknown>
}

interface WSState {
  connected: boolean
  lastEvent: WSEvent | null
  listeners: Map<string, Set<(event: WSEvent) => void>>
  setConnected: (v: boolean) => void
  setLastEvent: (e: WSEvent) => void
  subscribe: (eventType: string, handler: (event: WSEvent) => void) => () => void
}

export const useWSStore = create<WSState>((set, get) => ({
  connected: false,
  lastEvent: null,
  listeners: new Map(),

  setConnected: (v) => set({ connected: v }),
  setLastEvent: (e) => {
    set({ lastEvent: e })
    const listeners = get().listeners.get(e.event_type)
    if (listeners) {
      listeners.forEach((handler) => handler(e))
    }
    // Also notify wildcard listeners
    const wildcardListeners = get().listeners.get("*")
    if (wildcardListeners) {
      wildcardListeners.forEach((handler) => handler(e))
    }
  },

  subscribe: (eventType, handler) => {
    const listeners = get().listeners
    if (!listeners.has(eventType)) {
      listeners.set(eventType, new Set())
    }
    listeners.get(eventType)!.add(handler)
    return () => {
      listeners.get(eventType)?.delete(handler)
    }
  },
}))

export function useWebSocket(companyId?: string) {
  const wsRef = useRef<WebSocket | null>(null)
  const { setConnected, setLastEvent } = useWSStore()

  useEffect(() => {
    if (!companyId) return

    const url = `${WS_BASE}/ws/events?company_id=${companyId}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      // Reconnect after delay
      setTimeout(() => {
        if (wsRef.current === ws) {
          wsRef.current = null
        }
      }, 3000)
    }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSEvent
        setLastEvent(data)
      } catch {
        // ignore non-JSON messages
      }
    }

    // Ping every 30s to keep alive
    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }))
      }
    }, 30000)

    return () => {
      clearInterval(interval)
      ws.close()
    }
  }, [companyId, setConnected, setLastEvent])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  return { send }
}
