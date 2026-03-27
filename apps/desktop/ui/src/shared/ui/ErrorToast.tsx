import { useEffect, useState, useCallback } from 'react'
import { create } from 'zustand'

interface ToastMessage {
  id: number
  message: string
  type: 'error' | 'warning' | 'info'
}

interface ToastState {
  toasts: ToastMessage[]
  addToast: (message: string, type?: ToastMessage['type']) => void
  removeToast: (id: number) => void
}

let nextId = 0

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (message, type = 'error') => {
    const id = ++nextId
    set((state) => ({
      toasts: [...state.toasts.slice(-4), { id, message, type }],
    }))
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },
}))

function ToastItem({ toast, onDismiss }: { toast: ToastMessage; onDismiss: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 6000)
    return () => clearTimeout(timer)
  }, [onDismiss])

  const bgColor =
    toast.type === 'error'
      ? 'bg-red-600'
      : toast.type === 'warning'
        ? 'bg-amber-600'
        : 'bg-blue-600'

  return (
    <div
      className={`${bgColor} text-white text-[13px] px-4 py-3 rounded-lg shadow-lg max-w-sm animate-[slideIn_0.2s_ease-out]`}
      role="alert"
    >
      <div className="flex items-start gap-2">
        <span className="flex-1 break-words">{toast.message}</span>
        <button
          onClick={onDismiss}
          className="shrink-0 opacity-70 hover:opacity-100"
          aria-label="Dismiss"
        >
          &times;
        </button>
      </div>
    </div>
  )
}

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" aria-live="polite">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={() => removeToast(toast.id)} />
      ))}
    </div>
  )
}
