import { Hono } from "hono";
import type { Bindings, Variables, ReviewRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";

const reviews = new Hono<{ Bindings: Bindings; Variables: Variables }>();

reviews.use("*", authMiddleware);

/* GET /api/companies/:companyId/reviews */
reviews.get("/companies/:companyId/reviews", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<ReviewRow>(
    c.env.DB,
    "reviews",
    companyId,
    limit,
    offset,
  );
  return c.json({ data: results });
});

/* POST /api/companies/:companyId/reviews */
reviews.post("/companies/:companyId/reviews", async (c) => {
  const companyId = c.req.param("companyId");
  const userId = c.get("userId");
  const body = await c.req.json<{
    ticket_id?: string;
    task_id?: string;
    status: string;
    score?: number;
    comments_markdown?: string;
  }>();

  if (!body.status) {
    return c.json({ error: "status is required" }, 400);
  }

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO reviews (id, company_id, ticket_id, task_id, reviewer_type, reviewer_user_id, status, score, comments_markdown, created_at)
     VALUES (?, ?, ?, ?, 'user', ?, ?, ?, ?, ?)`,
  )
    .bind(
      id,
      companyId,
      body.ticket_id ?? null,
      body.task_id ?? null,
      userId,
      body.status,
      body.score ?? null,
      body.comments_markdown ?? null,
      timestamp,
    )
    .run();

  return c.json({ data: { id, status: body.status } }, 201);
});

/* GET /api/reviews/:id */
reviews.get("/reviews/:id", async (c) => {
  const review = await findById<ReviewRow>(c.env.DB, "reviews", c.req.param("id"));
  if (!review) return c.json({ error: "Review not found" }, 404);
  return c.json({ data: review });
});

export default reviews;
