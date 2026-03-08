import { createMiddleware } from "hono/factory";
import type { Bindings, Variables } from "../lib/types";

/**
 * Audit log middleware.
 * Logs every mutating request (POST / PUT / PATCH / DELETE) to the audit_logs table.
 */
export const auditMiddleware = createMiddleware<{
  Bindings: Bindings;
  Variables: Variables;
}>(async (c, next) => {
  await next();

  const method = c.req.method;
  if (method === "GET" || method === "OPTIONS" || method === "HEAD") {
    return;
  }

  const userId = c.get("userId") ?? null;
  const path = new URL(c.req.url).pathname;
  const now = new Date().toISOString();

  try {
    await c.env.DB.prepare(
      `INSERT INTO audit_logs (id, company_id, actor_type, actor_user_id, event_type, target_type, target_id, created_at)
       VALUES (lower(hex(randomblob(16))), '', 'user', ?, ?, ?, NULL, ?)`,
    )
      .bind(userId, `${method} ${path}`, path, now)
      .run();
  } catch {
    // Audit logging should not break the request
    console.error("Audit log write failed");
  }
});
