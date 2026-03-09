import { Hono } from "hono";
import type { Bindings, Variables, SkillRow, PluginRow, ExtensionRow } from "../lib/types";
import { authMiddleware } from "../middleware/auth";
import { pagination } from "../db/queries";

const registry = new Hono<{ Bindings: Bindings; Variables: Variables }>();

registry.use("*", authMiddleware);

/* GET /api/companies/:companyId/skills */
registry.get("/companies/:companyId/skills", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const { results } = await c.env.DB.prepare(
    `SELECT * FROM skills WHERE company_id = ? OR company_id IS NULL
     ORDER BY created_at DESC LIMIT ? OFFSET ?`,
  )
    .bind(companyId, limit, offset)
    .all<SkillRow>();

  return c.json({ data: results });
});

/* GET /api/companies/:companyId/plugins */
registry.get("/companies/:companyId/plugins", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const { results } = await c.env.DB.prepare(
    `SELECT * FROM plugins WHERE company_id = ? OR company_id IS NULL
     ORDER BY created_at DESC LIMIT ? OFFSET ?`,
  )
    .bind(companyId, limit, offset)
    .all<PluginRow>();

  return c.json({ data: results });
});

/* GET /api/companies/:companyId/extensions */
registry.get("/companies/:companyId/extensions", async (c) => {
  const companyId = c.req.param("companyId");
  const params = new URL(c.req.url).searchParams;
  const { limit, offset } = pagination(params);

  const { results } = await c.env.DB.prepare(
    `SELECT * FROM extensions WHERE company_id = ? OR company_id IS NULL
     ORDER BY created_at DESC LIMIT ? OFFSET ?`,
  )
    .bind(companyId, limit, offset)
    .all<ExtensionRow>();

  return c.json({ data: results });
});

/* GET /api/registry/search */
registry.get("/registry/search", async (c) => {
  const params = new URL(c.req.url).searchParams;
  const query = params.get("q") ?? "";
  const type = params.get("type"); // "skill" | "plugin" | "extension"
  const { limit, offset } = pagination(params);

  if (type === "plugin") {
    const { results } = await c.env.DB.prepare(
      `SELECT * FROM plugins WHERE name LIKE ? OR description LIKE ?
       ORDER BY created_at DESC LIMIT ? OFFSET ?`,
    )
      .bind(`%${query}%`, `%${query}%`, limit, offset)
      .all<PluginRow>();
    return c.json({ data: results, type: "plugin" });
  }

  if (type === "extension") {
    const { results } = await c.env.DB.prepare(
      `SELECT * FROM extensions WHERE name LIKE ? OR description LIKE ?
       ORDER BY created_at DESC LIMIT ? OFFSET ?`,
    )
      .bind(`%${query}%`, `%${query}%`, limit, offset)
      .all<ExtensionRow>();
    return c.json({ data: results, type: "extension" });
  }

  // Default: search skills
  const { results } = await c.env.DB.prepare(
    `SELECT * FROM skills WHERE name LIKE ? OR description LIKE ?
     ORDER BY created_at DESC LIMIT ? OFFSET ?`,
  )
    .bind(`%${query}%`, `%${query}%`, limit, offset)
    .all<SkillRow>();
  return c.json({ data: results, type: "skill" });
});

export default registry;
