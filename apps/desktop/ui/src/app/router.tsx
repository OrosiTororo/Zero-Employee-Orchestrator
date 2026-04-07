import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { App } from './App'
import { LogoMark } from '@/shared/ui/Logo'

/* Eagerly loaded — critical path */
import { LoginPage } from '@/pages/LoginPage'
import { SetupPage } from '@/pages/SetupPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

/* Lazily loaded — code split for smaller initial bundle */
const OrgChartPage = lazy(() => import('@/pages/OrgChartPage').then(m => ({ default: m.OrgChartPage })))
const SecretaryPage = lazy(() => import('@/pages/SecretaryPage').then(m => ({ default: m.SecretaryPage })))
const TicketListPage = lazy(() => import('@/pages/TicketListPage').then(m => ({ default: m.TicketListPage })))
const TicketDetailPage = lazy(() => import('@/pages/TicketDetailPage').then(m => ({ default: m.TicketDetailPage })))
const InterviewPage = lazy(() => import('@/pages/InterviewPage').then(m => ({ default: m.InterviewPage })))
const SpecPlanPage = lazy(() => import('@/pages/SpecPlanPage').then(m => ({ default: m.SpecPlanPage })))
const ApprovalsPage = lazy(() => import('@/pages/ApprovalsPage').then(m => ({ default: m.ApprovalsPage })))
const ArtifactsPage = lazy(() => import('@/pages/ArtifactsPage').then(m => ({ default: m.ArtifactsPage })))
const HeartbeatsPage = lazy(() => import('@/pages/HeartbeatsPage').then(m => ({ default: m.HeartbeatsPage })))
const CostsPage = lazy(() => import('@/pages/CostsPage').then(m => ({ default: m.CostsPage })))
const AuditPage = lazy(() => import('@/pages/AuditPage').then(m => ({ default: m.AuditPage })))
const SkillsPage = lazy(() => import('@/pages/SkillsPage').then(m => ({ default: m.SkillsPage })))
const SkillCreatePage = lazy(() => import('@/pages/SkillCreatePage').then(m => ({ default: m.SkillCreatePage })))
const SkillDetailPage = lazy(() => import('@/pages/SkillDetailPage').then(m => ({ default: m.SkillDetailPage })))
const PluginsPage = lazy(() => import('@/pages/PluginsPage').then(m => ({ default: m.PluginsPage })))
const ExtensionsPage = lazy(() => import('@/pages/ExtensionsPage').then(m => ({ default: m.ExtensionsPage })))
const MarketplacePage = lazy(() => import('@/pages/MarketplacePage').then(m => ({ default: m.MarketplacePage })))
const SettingsPage = lazy(() => import('@/pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const PermissionsPage = lazy(() => import('@/pages/PermissionsPage').then(m => ({ default: m.PermissionsPage })))
const AgentMonitorPage = lazy(() => import('@/pages/AgentMonitorPage').then(m => ({ default: m.AgentMonitorPage })))
const BrainstormPage = lazy(() => import('@/pages/BrainstormPage'))
const DispatchPage = lazy(() => import('@/pages/DispatchPage').then(m => ({ default: m.DispatchPage })))
const OperatorProfilePage = lazy(() => import('@/pages/OperatorProfilePage').then(m => ({ default: m.OperatorProfilePage })))

function PageLoader() {
  return (
    <div className="h-full flex items-center justify-center">
      <LogoMark size={24} className="animate-pulse" />
    </div>
  )
}

function L({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/setup',
    element: <SetupPage />,
  },
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'org-chart', element: <L><OrgChartPage /></L> },
      { path: 'secretary', element: <L><SecretaryPage /></L> },
      { path: 'tickets', element: <L><TicketListPage /></L> },
      { path: 'tickets/:id', element: <L><TicketDetailPage /></L> },
      { path: 'tickets/:id/interview', element: <L><InterviewPage /></L> },
      { path: 'tickets/:id/spec-plan', element: <L><SpecPlanPage /></L> },
      { path: 'approvals', element: <L><ApprovalsPage /></L> },
      { path: 'artifacts', element: <L><ArtifactsPage /></L> },
      { path: 'heartbeats', element: <L><HeartbeatsPage /></L> },
      { path: 'costs', element: <L><CostsPage /></L> },
      { path: 'audit', element: <L><AuditPage /></L> },
      { path: 'skills', element: <L><SkillsPage /></L> },
      { path: 'skills/create', element: <L><SkillCreatePage /></L> },
      { path: 'skills/:id', element: <L><SkillDetailPage /></L> },
      { path: 'plugins', element: <L><PluginsPage /></L> },
      { path: 'extensions', element: <L><ExtensionsPage /></L> },
      { path: 'marketplace', element: <L><MarketplacePage /></L> },
      { path: 'settings', element: <L><SettingsPage /></L> },
      { path: 'permissions', element: <L><PermissionsPage /></L> },
      { path: 'monitor', element: <L><AgentMonitorPage /></L> },
      { path: 'brainstorm', element: <L><BrainstormPage /></L> },
      { path: 'dispatch', element: <L><DispatchPage /></L> },
      { path: 'operator-profile', element: <L><OperatorProfilePage /></L> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])
