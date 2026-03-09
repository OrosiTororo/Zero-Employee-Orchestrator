import { Hono } from "hono";
import type { Bindings, Variables, HeartbeatPolicyRow, HeartbeatRunRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";

const heartbeats = new Hono<{ Bindings: Bindings; Variables: Variables }>();

heartbeats.use("*", authMiddleware);

/* GET /api/companies/:companyId/heartbeat-policies */
heartbeats.get("/companies/:companyId/heartbeat-policies", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<HeartbeatPolicyRow>(
    c.env.DB,
    "heartbeat_policies",
    companyId,
    limit,
    offset,
  );
  return c.json({ data: results });
});

/* POST /api/companies/:companyId/heartbeat-policies */
heartbeats.post("/companies/:companyId/heartbeat-policies", async (c) => {
  const companyId = c.req.param("companyId");
  const body = await c.req.json<{
    name: string;
    cron_expr: string;
    timezone?: string;
    enabled?: boolean;
    jitter_seconds?: number;
    max_parallel_runs?: number;
  }>();

  if (!body.name || !body.cron_expr) {
    return c.json({ error: "name and cron_expr are required" }, 400);
  }

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO heartbeat_policies (id, company_id, name, cron_expr, timezone, enabled, jitter_seconds, max_parallel_runs, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  )
    .bind(
      id,
      companyId,
      body.name,
      body.cron_expr,
      body.timezone ?? "UTC",
      body.enabled !== false ? 1 : 0,
      body.jitter_seconds ?? 0,
      body.max_parallel_runs ?? 1,
      timestamp,
      timestamp,
    )
    .run();

  return c.json({ data: { id, name: body.name } }, 201);
});

/* GET /api/companies/:companyId/heartbeat-runs */
heartbeats.get("/companies/:companyId/heartbeat-runs", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<HeartbeatRunRow>(
    c.env.DB,
    "heartbeat_runs",
    companyId,
    limit,
    offset,
  );
  return c.json({ data: results });
});

export default heartbeats;
