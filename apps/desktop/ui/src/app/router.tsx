import { createBrowserRouter } from 'react-router-dom'
import { App } from './App'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { OrgChartPage } from '@/pages/OrgChartPage'
import { TicketListPage } from '@/pages/TicketListPage'
import { TicketDetailPage } from '@/pages/TicketDetailPage'
import { SpecPlanPage } from '@/pages/SpecPlanPage'
import { ApprovalsPage } from '@/pages/ApprovalsPage'
import { ArtifactsPage } from '@/pages/ArtifactsPage'
import { HeartbeatsPage } from '@/pages/HeartbeatsPage'
import { CostsPage } from '@/pages/CostsPage'
import { AuditPage } from '@/pages/AuditPage'
import { SkillsPage } from '@/pages/SkillsPage'
import { SkillCreatePage } from '@/pages/SkillCreatePage'
import { PluginsPage } from '@/pages/PluginsPage'
import { SettingsPage } from '@/pages/SettingsPage'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'org-chart', element: <OrgChartPage /> },
      { path: 'tickets', element: <TicketListPage /> },
      { path: 'tickets/:id', element: <TicketDetailPage /> },
      { path: 'tickets/:id/spec-plan', element: <SpecPlanPage /> },
      { path: 'approvals', element: <ApprovalsPage /> },
      { path: 'artifacts', element: <ArtifactsPage /> },
      { path: 'heartbeats', element: <HeartbeatsPage /> },
      { path: 'costs', element: <CostsPage /> },
      { path: 'audit', element: <AuditPage /> },
      { path: 'skills', element: <SkillsPage /> },
      { path: 'skills/create', element: <SkillCreatePage /> },
      { path: 'plugins', element: <PluginsPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
])
