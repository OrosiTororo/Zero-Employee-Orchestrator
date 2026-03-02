const API_BASE = "http://localhost:18234";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// Auth
export const authLogin = () => request("/api/auth/login", { method: "POST" });
export const authStatus = () => request<{ authenticated: boolean }>("/api/auth/status");
export const authLogout = () => request("/api/auth/logout", { method: "POST" });
export const authConnect = (service: string) =>
  request(`/api/auth/connect/${service}`, { method: "POST" });
export const authConnections = () =>
  request<{ service: string; display_name: string; connected: boolean }[]>("/api/auth/connections");
export const authDisconnect = (service: string) =>
  request(`/api/auth/disconnect/${service}`, { method: "DELETE" });

// Interview
export const interviewStart = (input: string) =>
  request("/api/interview/start", { method: "POST", body: JSON.stringify({ input }) });
export const interviewRespond = (session_id: string, answers: Record<string, string>) =>
  request("/api/interview/respond", { method: "POST", body: JSON.stringify({ session_id, answers }) });
export const interviewFinalize = (session_id: string) =>
  request("/api/interview/finalize", { method: "POST", body: JSON.stringify({ session_id }) });

// Orchestrate
export const orchestrate = (input: string, quality_mode = "balanced") =>
  request("/api/orchestrate", { method: "POST", body: JSON.stringify({ input, quality_mode }) });
export const getOrchestration = (id: string) => request(`/api/orchestrate/${id}`);
export const approvePlan = (id: string) =>
  request(`/api/orchestrate/${id}/approve-plan`, { method: "POST" });
export const repropose = (id: string, feedback: string, mode = "plan_modify") =>
  request(`/api/orchestrate/${id}/repropose`, {
    method: "POST", body: JSON.stringify({ feedback, mode }),
  });
export const getCost = (id: string) => request(`/api/orchestrate/${id}/cost`);
export const getDiff = (id: string) => request(`/api/orchestrate/${id}/diff`);
export const selfHeal = (id: string) =>
  request(`/api/orchestrate/${id}/self-heal`, { method: "POST" });
export const getHealHistory = (id: string) => request(`/api/orchestrate/${id}/heal-history`);

// Chat & Judge
export const chat = (messages: { role: string; content: string }[], model_group = "fast") =>
  request<{ response: string }>("/api/chat", {
    method: "POST", body: JSON.stringify({ messages, model_group }),
  });
export const judge = (text: string, context = "") =>
  request("/api/judge", { method: "POST", body: JSON.stringify({ text, context }) });

// Tasks
export const createTask = (skill_name: string, input_data: Record<string, unknown>) =>
  request("/api/tasks", { method: "POST", body: JSON.stringify({ skill_name, input_data }) });
export const getTask = (id: string) => request(`/api/tasks/${id}`);
export const transitionTask = (id: string, trigger: string) =>
  request(`/api/tasks/${id}/transition`, { method: "POST", body: JSON.stringify({ trigger }) });

// Skills
export const listSkills = () => request<{ name: string; description: string }[]>("/api/skills");
export const executeSkill = (skill_name: string, input: Record<string, unknown>) =>
  request("/api/skills/execute", { method: "POST", body: JSON.stringify({ skill_name, input }) });
export const generateSkill = (description: string) =>
  request("/api/skills/generate", { method: "POST", body: JSON.stringify({ description }) });
export const getSkillGaps = () => request("/api/skills/gaps");

// Registry
export const registrySearch = (q: string) => request(`/api/registry/search?q=${encodeURIComponent(q)}`);
export const registryPublish = (skill_dir: string, author: string) =>
  request("/api/registry/publish", { method: "POST", body: JSON.stringify({ skill_dir, author }) });
export const registryInstall = (skill_name: string) =>
  request("/api/registry/install", { method: "POST", body: JSON.stringify({ skill_name }) });
export const registryPopular = () => request("/api/registry/popular");

// Settings
export const getSettings = () => request("/api/settings");
export const updateSettings = (settings: Record<string, unknown>) =>
  request("/api/settings", { method: "PUT", body: JSON.stringify(settings) });

// Webhooks
export const listWebhooks = () => request<WebhookConfig[]>("/api/webhooks");
export const createWebhook = (data: { name: string; url: string; events?: string[]; active?: boolean }) =>
  request<WebhookConfig>("/api/webhooks", { method: "POST", body: JSON.stringify(data) });
export const getWebhook = (id: string) => request<WebhookConfig>(`/api/webhooks/${id}`);
export const updateWebhook = (id: string, data: Record<string, unknown>) =>
  request<WebhookConfig>(`/api/webhooks/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteWebhook = (id: string) =>
  request(`/api/webhooks/${id}`, { method: "DELETE" });
export const testWebhook = (id: string) =>
  request(`/api/webhooks/${id}/test`, { method: "POST" });
export const getWebhookDeliveries = (id: string) =>
  request<WebhookDelivery[]>(`/api/webhooks/${id}/deliveries`);

export interface WebhookConfig {
  id: string;
  name: string;
  url: string;
  secret: string;
  events: string[];
  active: boolean;
  created_at: string;
  last_triggered: string | null;
  failure_count: number;
}

export interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event: string;
  payload: Record<string, unknown>;
  status_code: number | null;
  success: boolean;
  attempt: number;
  timestamp: string;
}

// Health
export const healthCheck = () => request<{ status: string; version: string }>("/api/health");
