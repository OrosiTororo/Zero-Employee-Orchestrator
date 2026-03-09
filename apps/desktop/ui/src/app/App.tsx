import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/shared/hooks/use-auth'
import { Layout } from '@/shared/ui/Layout'
import { LogoMark } from '@/shared/ui/Logo'
import { useT } from '@/shared/i18n'

export function App() {
  const { authenticated, loading } = useAuthStore()
  const t = useT()

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-base)]">
        <div className="flex flex-col items-center gap-3">
          <LogoMark size={32} className="animate-pulse" />
          <span className="text-[13px] text-[var(--text-secondary)]">
            {t.common.loading}
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
