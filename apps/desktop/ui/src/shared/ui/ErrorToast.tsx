import { useEffect } from 'react'
import { create } from 'zustand'
import { CircleAlert, TriangleAlert, Info, X } from 'lucide-react'

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

  const Icon =
    toast.type === 'error' ? CircleAlert : toast.type === 'warning' ? TriangleAlert : Info
  const iconColor =
    toast.type === 'error'
      ? 'var(--error)'
      : toast.type === 'warning'
        ? 'var(--warning-fg)'
        : 'var(--info)'

  return (
    <div
      className="menu-surface max-w-sm rounded-lg px-3.5 py-3 text-[13px] text-[var(--text-primary)] animate-slide-up"
      role="alert"
    >
      <div className="flex items-start gap-2.5">
        <Icon size={16} className="mt-px shrink-0" style={{ color: iconColor }} />
        <span className="flex-1 break-words">{toast.message}</span>
        <button
          onClick={onDismiss}
          className="shrink-0 flex items-center justify-center w-5 h-5 rounded-full text-[var(--text-muted)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
          aria-label="Dismiss"
        >
          <X size={13} />
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
