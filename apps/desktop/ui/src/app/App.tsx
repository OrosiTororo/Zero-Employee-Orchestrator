import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/shared/hooks/use-auth'
import { Layout } from '@/shared/ui/Layout'

export function App() {
  const { authenticated, loading } = useAuthStore()

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#1e1e1e]">
        <div className="text-[#969696] text-sm">読み込み中...</div>
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
