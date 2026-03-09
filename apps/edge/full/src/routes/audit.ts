import { Hono } from "hono";
import type { Bindings, Variables, AuditLogRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { pagination, listByCompany } from "../db/queries";

const audit = new Hono<{ Bindings: Bindings; Variables: Variables }>();

audit.use("*", authMiddleware);

/* GET /api/companies/:companyId/audit-logs */
audit.get("/companies/:companyId/audit-logs", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const eventType = params.get("event_type");
  const actorType = params.get("actor_type");

  if (eventType || actorType) {
    let query = "SELECT * FROM audit_logs WHERE company_id = ?";
    const binds: (string | number)[] = [companyId];

    if (eventType) {
      query += " AND event_type = ?";
      binds.push(eventType);
    }
    if (actorType) {
      query += " AND actor_type = ?";
      binds.push(actorType);
    }

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?";
    binds.push(limit, offset);

    const { results } = await c.env.DB.prepare(query)
      .bind(...binds)
      .all<AuditLogRow>();
    return c.json({ data: results });
  }

  const results = await listByCompany<AuditLogRow>(
    c.env.DB,
    "audit_logs",
    companyId,
    limit,
    offset,
  );
  return c.json({ data: results });
});

export default audit;
