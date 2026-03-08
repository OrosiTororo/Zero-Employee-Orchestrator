import { Hono } from "hono";
import type { Bindings, Variables, ApprovalRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { now, pagination, findById, listByCompany } from "../db/queries";

const approvals = new Hono<{ Bindings: Bindings; Variables: Variables }>();

approvals.use("*", authMiddleware);

/* GET /api/companies/:companyId/approvals */
approvals.get("/companies/:companyId/approvals", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<ApprovalRow>(
    c.env.DB,
    "approval_requests",
    companyId,
    limit,
    offset,
  );
  return c.json({ data: results });
});

/* POST /api/approvals/:id/approve */
approvals.post("/approvals/:id/approve", async (c) => {
  const id = c.req.param("id");
  const userId = c.get("userId");

  const approval = await findById<ApprovalRow>(c.env.DB, "approval_requests", id);
  if (!approval) return c.json({ error: "Approval request not found" }, 404);

  if (approval.status !== "requested") {
    return c.json({ error: "Approval already decided" }, 409);
  }

  const timestamp = now();
  await c.env.DB.prepare(
    "UPDATE approval_requests SET status = 'approved', approver_user_id = ?, decided_at = ? WHERE id = ?",
  )
    .bind(userId, timestamp, id)
    .run();

  return c.json({ data: { id, status: "approved" } });
});

/* POST /api/approvals/:id/reject */
approvals.post("/approvals/:id/reject", async (c) => {
  const id = c.req.param("id");
  const userId = c.get("userId");
  const body = await c.req.json<{ reason?: string }>().catch(() => ({}));

  const approval = await findById<ApprovalRow>(c.env.DB, "approval_requests", id);
  if (!approval) return c.json({ error: "Approval request not found" }, 404);

  if (approval.status !== "requested") {
    return c.json({ error: "Approval already decided" }, 409);
  }

  const timestamp = now();
  await c.env.DB.prepare(
    "UPDATE approval_requests SET status = 'rejected', approver_user_id = ?, reason = COALESCE(?, reason), decided_at = ? WHERE id = ?",
  )
    .bind(userId, (body as { reason?: string }).reason ?? null, timestamp, id)
    .run();

  return c.json({ data: { id, status: "rejected" } });
});

export default approvals;
