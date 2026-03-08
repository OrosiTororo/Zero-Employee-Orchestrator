import { Hono } from "hono";
import type { Bindings, Variables } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";
import type { CompanyRow } from "../lib/types";

const companies = new Hono<{ Bindings: Bindings; Variables: Variables }>();

companies.use("*", authMiddleware);

/* GET /api/companies */
companies.get("/", async (c) => {
  const userId = c.get("userId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const { results } = await c.env.DB.prepare(
    `SELECT c.* FROM companies c
     JOIN company_members cm ON cm.company_id = c.id
     WHERE cm.user_id = ?
     ORDER BY c.created_at DESC
     LIMIT ? OFFSET ?`,
  )
    .bind(userId, limit, offset)
    .all<CompanyRow>();

  return c.json({ data: results });
});

/* POST /api/companies */
companies.post("/", async (c) => {
  const userId = c.get("userId");
  const body = await c.req.json<{
    name: string;
    slug: string;
    mission?: string;
    description?: string;
  }>();

  if (!body.name || !body.slug) {
    return c.json({ error: "name and slug are required" }, 400);
  }

  const existing = await c.env.DB.prepare(
    "SELECT id FROM companies WHERE slug = ?",
  )
    .bind(body.slug)
    .first();

  if (existing) {
    return c.json({ error: "Slug already in use" }, 409);
  }

  const id = newId();
  const timestamp = now();

  await c.env.DB.batch([
    c.env.DB.prepare(
      `INSERT INTO companies (id, slug, name, mission, description, status, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, 'active', ?, ?)`,
    ).bind(id, body.slug, body.name, body.mission ?? null, body.description ?? null, timestamp, timestamp),
    c.env.DB.prepare(
      `INSERT INTO company_members (id, company_id, user_id, company_role, status, joined_at, created_at, updated_at)
       VALUES (?, ?, ?, 'owner', 'active', ?, ?, ?)`,
    ).bind(newId(), id, userId, timestamp, timestamp, timestamp),
  ]);

  return c.json({ data: { id, slug: body.slug, name: body.name } }, 201);
});

/* GET /api/companies/:id */
companies.get("/:id", async (c) => {
  const company = await findById<CompanyRow>(c.env.DB, "companies", c.req.param("id"));
  if (!company) return c.json({ error: "Company not found" }, 404);
  return c.json({ data: company });
});

/* GET /api/companies/:id/dashboard */
companies.get("/:id/dashboard", async (c) => {
  const companyId = c.req.param("id");
  const company = await findById<CompanyRow>(c.env.DB, "companies", companyId);
  if (!company) return c.json({ error: "Company not found" }, 404);

  const [agents, tickets, tasks, approvals] = await c.env.DB.batch([
    c.env.DB.prepare("SELECT COUNT(*) as count FROM agents WHERE company_id = ?").bind(companyId),
    c.env.DB.prepare("SELECT COUNT(*) as count FROM tickets WHERE company_id = ?").bind(companyId),
    c.env.DB.prepare("SELECT COUNT(*) as count FROM tasks WHERE company_id = ?").bind(companyId),
    c.env.DB.prepare("SELECT COUNT(*) as count FROM approval_requests WHERE company_id = ? AND status = 'requested'").bind(companyId),
  ]);

  return c.json({
    data: {
      company,
      counts: {
        agents: (agents.results[0] as Record<string, unknown>)?.count ?? 0,
        tickets: (tickets.results[0] as Record<string, unknown>)?.count ?? 0,
        tasks: (tasks.results[0] as Record<string, unknown>)?.count ?? 0,
        pending_approvals: (approvals.results[0] as Record<string, unknown>)?.count ?? 0,
      },
    },
  });
});

export default companies;
