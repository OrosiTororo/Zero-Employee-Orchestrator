import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/shared/hooks/use-auth'
import { Layout } from '@/shared/ui/Layout'
import { LogoMark } from '@/shared/ui/Logo'

export function App() {
  const { authenticated, loading } = useAuthStore()

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
        <div className="flex flex-col items-center gap-3">
          <LogoMark size={32} className="animate-pulse" />
          <span className="text-[13px] text-[var(--text-secondary)]">
            読み込み中...
          </span>
        </div>
      </div>
    )
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <Layout>
      <Outlet />
    </Layout>
  )
}
