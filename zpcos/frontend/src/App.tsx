import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { Layout } from "@/components/Layout";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { InterviewPage } from "@/pages/InterviewPage";
import { OrchestrationPage } from "@/pages/OrchestrationPage";
import { SkillsPage } from "@/pages/SkillsPage";
import { SkillCreatePage } from "@/pages/SkillCreatePage";
import { SettingsPage } from "@/pages/SettingsPage";
import { WebhooksPage } from "@/pages/WebhooksPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { authenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center" style={{ background: '#1e1e1e' }}>
        <div className="text-[#969696] text-sm">Loading...</div>
      </div>
    );
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/interview" element={<InterviewPage />} />
                  <Route path="/orchestrate/:id" element={<OrchestrationPage />} />
                  <Route path="/skills" element={<SkillsPage />} />
                  <Route path="/skills/create" element={<SkillCreatePage />} />
                  <Route path="/webhooks" element={<WebhooksPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
