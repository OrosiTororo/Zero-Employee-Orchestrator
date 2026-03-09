import { Hono } from "hono";
import type { Bindings, Variables, TaskRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, findById } from "../db/queries";

const tasks = new Hono<{ Bindings: Bindings; Variables: Variables }>();

tasks.use("*", authMiddleware);

/* POST /api/plans/:planId/tasks */
tasks.post("/plans/:planId/tasks", async (c) => {
  const planId = c.req.param("planId");
  const body = await c.req.json<{
    title: string;
    description?: string;
    task_type: string;
    sequence_no: number;
    ticket_id: string;
    company_id: string;
  }>();

  if (!body.title || !body.task_type || !body.ticket_id || !body.company_id) {
    return c.json(
      { error: "title, task_type, ticket_id, and company_id are required" },
      400,
    );
  }

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO tasks (id, company_id, ticket_id, plan_id, title, description, sequence_no, status, task_type, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)`,
  )
    .bind(
      id,
      body.company_id,
      body.ticket_id,
      planId,
      body.title,
      body.description ?? null,
      body.sequence_no ?? 0,
      body.task_type,
      timestamp,
      timestamp,
    )
    .run();

  return c.json({ data: { id, status: "pending" } }, 201);
});

/* POST /api/tasks/:id/start */
tasks.post("/tasks/:id/start", async (c) => {
  const id = c.req.param("id");
  const task = await findById<TaskRow>(c.env.DB, "tasks", id);
  if (!task) return c.json({ error: "Task not found" }, 404);

  const timestamp = now();
  await c.env.DB.prepare(
    "UPDATE tasks SET status = 'running', started_at = ?, updated_at = ? WHERE id = ?",
  )
    .bind(timestamp, timestamp, id)
    .run();

  return c.json({ data: { id, status: "running" } });
});

/* POST /api/tasks/:id/complete */
tasks.post("/tasks/:id/complete", async (c) => {
  const id = c.req.param("id");
  const task = await findById<TaskRow>(c.env.DB, "tasks", id);
  if (!task) return c.json({ error: "Task not found" }, 404);

  const timestamp = now();
  await c.env.DB.prepare(
    "UPDATE tasks SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?",
  )
    .bind(timestamp, timestamp, id)
    .run();

  return c.json({ data: { id, status: "completed" } });
});

export default tasks;
