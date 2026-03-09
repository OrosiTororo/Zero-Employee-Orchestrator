import { Hono } from "hono";
import type { Bindings, Variables, ProjectRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";

const projects = new Hono<{ Bindings: Bindings; Variables: Variables }>();

projects.use("*", authMiddleware);

/* GET /api/companies/:companyId/projects */
projects.get("/companies/:companyId/projects", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<ProjectRow>(c.env.DB, "projects", companyId, limit, offset);
  return c.json({ data: results });
});

/* POST /api/companies/:companyId/projects */
projects.post("/companies/:companyId/projects", async (c) => {
  const companyId = c.req.param("companyId");
  const userId = c.get("userId");
  const body = await c.req.json<{
    name: string;
    goal?: string;
    description?: string;
    priority?: string;
    due_at?: string;
  }>();

  if (!body.name) {
    return c.json({ error: "name is required" }, 400);
  }

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO projects (id, company_id, name, goal, description, priority, status, owner_user_id, due_at, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)`,
  )
    .bind(
      id,
      companyId,
      body.name,
      body.goal ?? null,
      body.description ?? null,
      body.priority ?? "medium",
      userId,
      body.due_at ?? null,
      timestamp,
      timestamp,
    )
    .run();

  return c.json({ data: { id, name: body.name, status: "active" } }, 201);
});

/* GET /api/projects/:id */
projects.get("/projects/:id", async (c) => {
  const project = await findById<ProjectRow>(c.env.DB, "projects", c.req.param("id"));
  if (!project) return c.json({ error: "Project not found" }, 404);
  return c.json({ data: project });
});

export default projects;
