import { Hono } from "hono";
import type { Bindings, Variables, ArtifactRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { newId, now, pagination, findById, listByCompany } from "../db/queries";

const artifacts = new Hono<{ Bindings: Bindings; Variables: Variables }>();

artifacts.use("*", authMiddleware);

/* GET /api/companies/:companyId/artifacts */
artifacts.get("/companies/:companyId/artifacts", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const results = await listByCompany<ArtifactRow>(
    c.env.DB,
    "artifacts",
    companyId,
    limit,
    offset,
  );
  return c.json({ data: results });
});

/* POST /api/tasks/:taskId/artifacts */
artifacts.post("/tasks/:taskId/artifacts", async (c) => {
  const taskId = c.req.param("taskId");
  const userId = c.get("userId");
  const body = await c.req.json<{
    company_id: string;
    ticket_id?: string;
    artifact_type: string;
    title: string;
    storage_type: string;
    path_or_uri?: string;
    mime_type?: string;
    summary?: string;
    meta_json?: string;
  }>();

  if (!body.company_id || !body.artifact_type || !body.title || !body.storage_type) {
    return c.json(
      { error: "company_id, artifact_type, title, and storage_type are required" },
      400,
    );
  }

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO artifacts (id, company_id, ticket_id, task_id, artifact_type, title, storage_type, path_or_uri, mime_type, version_no, summary, meta_json, created_by_type, created_by_user_id, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 'user', ?, ?)`,
  )
    .bind(
      id,
      body.company_id,
      body.ticket_id ?? null,
      taskId,
      body.artifact_type,
      body.title,
      body.storage_type,
      body.path_or_uri ?? null,
      body.mime_type ?? null,
      body.summary ?? null,
      body.meta_json ?? null,
      userId,
      timestamp,
    )
    .run();

  return c.json({ data: { id, title: body.title } }, 201);
});

/* GET /api/artifacts/:id */
artifacts.get("/artifacts/:id", async (c) => {
  const artifact = await findById<ArtifactRow>(c.env.DB, "artifacts", c.req.param("id"));
  if (!artifact) return c.json({ error: "Artifact not found" }, 404);
  return c.json({ data: artifact });
});

export default artifacts;
