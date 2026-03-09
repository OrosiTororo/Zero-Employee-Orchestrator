import { Hono } from "hono";
import type { Bindings, Variables, TicketRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";

const tickets = new Hono<{ Bindings: Bindings; Variables: Variables }>();

tickets.use("*", authMiddleware);

/* GET /api/companies/:companyId/tickets */
tickets.get("/companies/:companyId/tickets", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<TicketRow>(c.env.DB, "tickets", companyId, limit, offset);
  return c.json({ data: results });
});

/* POST /api/companies/:companyId/tickets */
tickets.post("/companies/:companyId/tickets", async (c) => {
  const companyId = c.req.param("companyId");
  const userId = c.get("userId");
  const body = await c.req.json<{
    title: string;
    description?: string;
    priority?: string;
    source_type?: string;
  }>();

  if (!body.title) {
    return c.json({ error: "title is required" }, 400);
  }

  // Get next ticket_no for this company
  const maxRow = await c.env.DB.prepare(
    "SELECT COALESCE(MAX(ticket_no), 0) + 1 AS next_no FROM tickets WHERE company_id = ?",
  )
    .bind(companyId)
    .first<{ next_no: number }>();

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO tickets (id, company_id, ticket_no, title, description, priority, status, source_type, requester_user_id, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?)`,
  )
    .bind(
      id,
      companyId,
      maxRow?.next_no ?? 1,
      body.title,
      body.description ?? null,
      body.priority ?? "medium",
      body.source_type ?? "manual",
      userId,
      timestamp,
      timestamp,
    )
    .run();

  return c.json({ data: { id, ticket_no: maxRow?.next_no ?? 1 } }, 201);
});

/* GET /api/tickets/:id */
tickets.get("/tickets/:id", async (c) => {
  const ticket = await findById<TicketRow>(c.env.DB, "tickets", c.req.param("id"));
  if (!ticket) return c.json({ error: "Ticket not found" }, 404);
  return c.json({ data: ticket });
});

export default tickets;
