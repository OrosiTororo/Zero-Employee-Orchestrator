import { Hono } from "hono";
import type { Bindings, Variables, AgentRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";

const agents = new Hono<{ Bindings: Bindings; Variables: Variables }>();

agents.use("*", authMiddleware);

/* GET /api/companies/:companyId/agents */
agents.get("/companies/:companyId/agents", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<AgentRow>(c.env.DB, "agents", companyId, limit, offset);
  return c.json({ data: results });
});

/* POST /api/companies/:companyId/agents */
agents.post("/companies/:companyId/agents", async (c) => {
  const companyId = c.req.param("companyId");
  const body = await c.req.json<{
    name: string;
    title: string;
    description?: string;
    agent_type: string;
    runtime_type: string;
    provider_name: string;
    model_name?: string;
    autonomy_level: string;
  }>();

  if (!body.name || !body.title || !body.agent_type || !body.runtime_type || !body.provider_name || !body.autonomy_level) {
    return c.json({ error: "name, title, agent_type, runtime_type, provider_name, and autonomy_level are required" }, 400);
  }

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO agents (id, company_id, name, title, description, agent_type, runtime_type, provider_name, model_name, status, autonomy_level, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'provisioning', ?, ?, ?)`,
  )
    .bind(
      id,
      companyId,
      body.name,
      body.title,
      body.description ?? null,
      body.agent_type,
      body.runtime_type,
      body.provider_name,
      body.model_name ?? null,
      body.autonomy_level,
      timestamp,
      timestamp,
    )
    .run();

  return c.json({ data: { id, name: body.name, status: "provisioning" } }, 201);
});

/* POST /api/agents/:id/pause */
agents.post("/agents/:id/pause", async (c) => {
  const id = c.req.param("id");
  const agent = await findById<AgentRow>(c.env.DB, "agents", id);
  if (!agent) return c.json({ error: "Agent not found" }, 404);

  await c.env.DB.prepare(
    "UPDATE agents SET status = 'paused', updated_at = ? WHERE id = ?",
  )
    .bind(now(), id)
    .run();

  return c.json({ data: { id, status: "paused" } });
});

/* POST /api/agents/:id/resume */
agents.post("/agents/:id/resume", async (c) => {
  const id = c.req.param("id");
  const agent = await findById<AgentRow>(c.env.DB, "agents", id);
  if (!agent) return c.json({ error: "Agent not found" }, 404);

  await c.env.DB.prepare(
    "UPDATE agents SET status = 'active', updated_at = ? WHERE id = ?",
  )
    .bind(now(), id)
    .run();

  return c.json({ data: { id, status: "active" } });
});

export default agents;
