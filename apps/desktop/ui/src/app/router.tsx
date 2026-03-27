import { createBrowserRouter } from 'react-router-dom'
import { App } from './App'
import { LoginPage } from '@/pages/LoginPage'
import { SetupPage } from '@/pages/SetupPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { OrgChartPage } from '@/pages/OrgChartPage'
import { SecretaryPage } from '@/pages/SecretaryPage'
import { TicketListPage } from '@/pages/TicketListPage'
import { TicketDetailPage } from '@/pages/TicketDetailPage'
import { InterviewPage } from '@/pages/InterviewPage'
import { SpecPlanPage } from '@/pages/SpecPlanPage'
import { ApprovalsPage } from '@/pages/ApprovalsPage'
import { ArtifactsPage } from '@/pages/ArtifactsPage'
import { HeartbeatsPage } from '@/pages/HeartbeatsPage'
import { CostsPage } from '@/pages/CostsPage'
import { AuditPage } from '@/pages/AuditPage'
import { SkillsPage } from '@/pages/SkillsPage'
import { SkillCreatePage } from '@/pages/SkillCreatePage'
import { SkillDetailPage } from '@/pages/SkillDetailPage'
import { PluginsPage } from '@/pages/PluginsPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { ReleasesPage } from '@/pages/ReleasesPage'
import { DownloadPage } from '@/pages/DownloadPage'
import { PermissionsPage } from '@/pages/PermissionsPage'
import { AgentMonitorPage } from '@/pages/AgentMonitorPage'
import BrainstormPage from '@/pages/BrainstormPage'

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
      { path: 'org-chart', element: <OrgChartPage /> },
      { path: 'secretary', element: <SecretaryPage /> },
      { path: 'tickets', element: <TicketListPage /> },
      { path: 'tickets/:id', element: <TicketDetailPage /> },
      { path: 'tickets/:id/interview', element: <InterviewPage /> },
      { path: 'tickets/:id/spec-plan', element: <SpecPlanPage /> },
      { path: 'approvals', element: <ApprovalsPage /> },
      { path: 'artifacts', element: <ArtifactsPage /> },
      { path: 'heartbeats', element: <HeartbeatsPage /> },
      { path: 'costs', element: <CostsPage /> },
      { path: 'audit', element: <AuditPage /> },
      { path: 'skills', element: <SkillsPage /> },
      { path: 'skills/:id', element: <SkillDetailPage /> },
      { path: 'skills/create', element: <SkillCreatePage /> },
      { path: 'plugins', element: <PluginsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'releases', element: <ReleasesPage /> },
      { path: 'download', element: <DownloadPage /> },
      { path: 'permissions', element: <PermissionsPage /> },
      { path: 'monitor', element: <AgentMonitorPage /> },
      { path: 'brainstorm', element: <BrainstormPage /> },
    ],
  },
])
