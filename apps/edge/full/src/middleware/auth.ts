import { createMiddleware } from "hono/factory";
import { verifyToken } from "../lib/jwt";
import type { Bindings, Variables } from "../lib/types";

/**
 * JWT authentication middleware.
 * Extracts the Bearer token, verifies it, and sets userId on context.
 */
export const authMiddleware = createMiddleware<{
  Bindings: Bindings;
  Variables: Variables;
}>(async (c, next) => {
  const header = c.req.header("Authorization");

  if (!header?.startsWith("Bearer ")) {
    return c.json({ error: "Missing or invalid Authorization header" }, 401);
  }

  const token = header.slice(7);
  const payload = await verifyToken(token, c.env.JWT_SECRET);

  if (!payload) {
    return c.json({ error: "Invalid or expired token" }, 401);
  }

  c.set("userId", payload.sub);
  await next();
});
