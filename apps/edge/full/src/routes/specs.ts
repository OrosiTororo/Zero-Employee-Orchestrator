import { Hono } from "hono";
import type { Bindings, Variables, SpecRow, PlanRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";

const specs = new Hono<{ Bindings: Bindings; Variables: Variables }>();

specs.use("*", authMiddleware);

/* GET /api/companies/:companyId/specs */
specs.get("/companies/:companyId/specs", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<SpecRow>(c.env.DB, "specs", companyId, limit, offset);
  return c.json({ data: results });
});

/* POST /api/tickets/:ticketId/specs */
specs.post("/tickets/:ticketId/specs", async (c) => {
  const ticketId = c.req.param("ticketId");
  const userId = c.get("userId");
  const body = await c.req.json<{
    company_id: string;
    objective?: string;
    constraints_json?: string;
    acceptance_criteria_json?: string;
    risk_notes?: string;
  }>();

  if (!body.company_id) {
    return c.json({ error: "company_id is required" }, 400);
  }

  // Get next version_no for this ticket
  const maxRow = await c.env.DB.prepare(
    "SELECT COALESCE(MAX(version_no), 0) + 1 AS next_no FROM specs WHERE ticket_id = ?",
  )
    .bind(ticketId)
    .first<{ next_no: number }>();

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO specs (id, company_id, ticket_id, version_no, status, objective, constraints_json, acceptance_criteria_json, risk_notes, created_by_type, created_by_user_id, created_at, updated_at)
     VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?, 'user', ?, ?, ?)`,
  )
    .bind(
      id,
      body.company_id,
      ticketId,
      maxRow?.next_no ?? 1,
      body.objective ?? null,
      body.constraints_json ?? null,
      body.acceptance_criteria_json ?? null,
      body.risk_notes ?? null,
      userId,
      timestamp,
      timestamp,
    )
    .run();

  return c.json({ data: { id, version_no: maxRow?.next_no ?? 1, status: "draft" } }, 201);
});

/* GET /api/specs/:id */
specs.get("/specs/:id", async (c) => {
  const spec = await findById<SpecRow>(c.env.DB, "specs", c.req.param("id"));
  if (!spec) return c.json({ error: "Spec not found" }, 404);
  return c.json({ data: spec });
});

/* POST /api/specs/:specId/plans */
specs.post("/specs/:specId/plans", async (c) => {
  const specId = c.req.param("specId");
  const body = await c.req.json<{
    company_id: string;
    ticket_id: string;
    summary?: string;
    estimated_cost_usd?: number;
    estimated_minutes?: number;
    risk_level?: string;
    plan_json?: string;
  }>();

  if (!body.company_id || !body.ticket_id) {
    return c.json({ error: "company_id and ticket_id are required" }, 400);
  }

  const maxRow = await c.env.DB.prepare(
    "SELECT COALESCE(MAX(version_no), 0) + 1 AS next_no FROM plans WHERE spec_id = ?",
  )
    .bind(specId)
    .first<{ next_no: number }>();

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO plans (id, company_id, ticket_id, spec_id, version_no, status, summary, estimated_cost_usd, estimated_minutes, approval_required, risk_level, plan_json, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, 0, ?, ?, ?, ?)`,
  )
    .bind(
      id,
      body.company_id,
      body.ticket_id,
      specId,
      maxRow?.next_no ?? 1,
      body.summary ?? null,
      body.estimated_cost_usd ?? null,
      body.estimated_minutes ?? null,
      body.risk_level ?? "low",
      body.plan_json ?? null,
      timestamp,
      timestamp,
    )
    .run();

  return c.json({ data: { id, version_no: maxRow?.next_no ?? 1, status: "draft" } }, 201);
});

/* GET /api/plans/:id */
specs.get("/plans/:id", async (c) => {
  const plan = await findById<PlanRow>(c.env.DB, "plans", c.req.param("id"));
  if (!plan) return c.json({ error: "Plan not found" }, 404);
  return c.json({ data: plan });
});

/* POST /api/plans/:id/approve */
specs.post("/plans/:id/approve", async (c) => {
  const id = c.req.param("id");
  const plan = await findById<PlanRow>(c.env.DB, "plans", id);
  if (!plan) return c.json({ error: "Plan not found" }, 404);

  if (plan.status !== "draft" && plan.status !== "proposed") {
    return c.json({ error: "Plan cannot be approved in current status" }, 409);
  }

  const timestamp = now();
  await c.env.DB.prepare(
    "UPDATE plans SET status = 'approved', updated_at = ? WHERE id = ?",
  )
    .bind(timestamp, id)
    .run();

  return c.json({ data: { id, status: "approved" } });
});

export default specs;
