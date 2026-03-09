import { Hono } from "hono";
import type { Bindings, Variables, BudgetPolicyRow, CostLedgerRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";

const budgets = new Hono<{ Bindings: Bindings; Variables: Variables }>();

budgets.use("*", authMiddleware);

/* GET /api/companies/:companyId/budgets */
budgets.get("/companies/:companyId/budgets", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<BudgetPolicyRow>(
    c.env.DB,
    "budget_policies",
    companyId,
    limit,
    offset,
  );
  return c.json({ data: results });
});

/* POST /api/companies/:companyId/budgets */
budgets.post("/companies/:companyId/budgets", async (c) => {
  const companyId = c.req.param("companyId");
  const body = await c.req.json<{
    name: string;
    scope_type: string;
    scope_id?: string;
    period_type: string;
    limit_usd: number;
    warn_threshold_pct?: number;
    stop_threshold_pct?: number;
  }>();

  if (!body.name || !body.scope_type || !body.period_type || body.limit_usd == null) {
    return c.json(
      { error: "name, scope_type, period_type, and limit_usd are required" },
      400,
    );
  }

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO budget_policies (id, company_id, name, scope_type, scope_id, period_type, limit_usd, warn_threshold_pct, stop_threshold_pct, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  )
    .bind(
      id,
      companyId,
      body.name,
      body.scope_type,
      body.scope_id ?? null,
      body.period_type,
      body.limit_usd,
      body.warn_threshold_pct ?? 80,
      body.stop_threshold_pct ?? 100,
      timestamp,
      timestamp,
    )
    .run();

  return c.json({ data: { id, name: body.name } }, 201);
});

/* GET /api/companies/:companyId/costs */
budgets.get("/companies/:companyId/costs", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<CostLedgerRow>(
    c.env.DB,
    "cost_ledger",
    companyId,
    limit,
    offset,
  );
  return c.json({ data: results });
});

/* GET /api/budgets/:id */
budgets.get("/budgets/:id", async (c) => {
  const budget = await findById<BudgetPolicyRow>(c.env.DB, "budget_policies", c.req.param("id"));
  if (!budget) return c.json({ error: "Budget policy not found" }, 404);
  return c.json({ data: budget });
});

export default budgets;
