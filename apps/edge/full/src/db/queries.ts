/* ------------------------------------------------------------------ */
/*  D1 Query Helpers                                                   */
/* ------------------------------------------------------------------ */

/** Generate a random hex UUID (D1/SQLite compatible). */
export function newId(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/** Current ISO-8601 timestamp string. */
export function now(): string {
  return new Date().toISOString();
}

/** Pagination helper — returns { limit, offset } from query string. */
export function pagination(
  params: URLSearchParams,
  defaults = { limit: 50, maxLimit: 200 },
): { limit: number; offset: number } {
  let limit = parseInt(params.get("limit") ?? String(defaults.limit), 10);
  if (Number.isNaN(limit) || limit < 1) limit = defaults.limit;
  if (limit > defaults.maxLimit) limit = defaults.maxLimit;

  let offset = parseInt(params.get("offset") ?? "0", 10);
  if (Number.isNaN(offset) || offset < 0) offset = 0;

  return { limit, offset };
}

/* ------------------------------------------------------------------ */
/*  Generic CRUD helpers                                               */
/* ------------------------------------------------------------------ */

/** Fetch a single row by ID. */
export async function findById<T>(
  db: D1Database,
  table: string,
  id: string,
): Promise<T | null> {
  const result = await db
    .prepare(`SELECT * FROM ${table} WHERE id = ?`)
    .bind(id)
    .first<T>();
  return result ?? null;
}

/** Fetch multiple rows filtered by company_id with pagination. */
export async function listByCompany<T>(
  db: D1Database,
  table: string,
  companyId: string,
  limit: number,
  offset: number,
): Promise<T[]> {
  const { results } = await db
    .prepare(
      `SELECT * FROM ${table} WHERE company_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?`,
    )
    .bind(companyId, limit, offset)
    .all<T>();
  return results;
}
