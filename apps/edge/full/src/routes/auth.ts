import { Hono } from "hono";
import type { Bindings, Variables } from "../lib/types";
import { signToken, verifyToken } from "../lib/jwt";
import { newId, now } from "../db/queries";

const auth = new Hono<{ Bindings: Bindings; Variables: Variables }>();

/* POST /api/auth/register */
auth.post("/register", async (c) => {
  const body = await c.req.json<{
    email: string;
    display_name: string;
    password: string;
  }>();

  if (!body.email || !body.password || !body.display_name) {
    return c.json({ error: "email, display_name, and password are required" }, 400);
  }

  const existing = await c.env.DB.prepare(
    "SELECT id FROM users WHERE email = ?",
  )
    .bind(body.email)
    .first();

  if (existing) {
    return c.json({ error: "Email already registered" }, 409);
  }

  // Hash password using PBKDF2 with Web Crypto API
  const salt = crypto.randomUUID();
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    encoder.encode(body.password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );
  const hashBuffer = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: encoder.encode(salt), iterations: 100000, hash: "SHA-256" },
    keyMaterial,
    256,
  );
  const hashHex = Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  const passwordHash = `pbkdf2:${salt}:${hashHex}`;

  const id = newId();
  const timestamp = now();

  await c.env.DB.prepare(
    `INSERT INTO users (id, email, display_name, role, status, password_hash, created_at, updated_at)
     VALUES (?, ?, ?, 'user', 'active', ?, ?, ?)`,
  )
    .bind(id, body.email, body.display_name, passwordHash, timestamp, timestamp)
    .run();

  const token = await signToken(
    { sub: id, email: body.email, role: "user" },
    c.env.JWT_SECRET,
  );

  return c.json({ data: { id, email: body.email, token } }, 201);
});

/* POST /api/auth/login */
auth.post("/login", async (c) => {
  const body = await c.req.json<{ email: string; password: string }>();

  if (!body.email || !body.password) {
    return c.json({ error: "email and password are required" }, 400);
  }

  const user = await c.env.DB.prepare(
    "SELECT id, email, display_name, role, status, password_hash FROM users WHERE email = ?",
  )
    .bind(body.email)
    .first<{
      id: string;
      email: string;
      display_name: string;
      role: string;
      status: string;
      password_hash: string | null;
    }>();

  if (!user || !user.password_hash) {
    return c.json({ error: "Invalid credentials" }, 401);
  }

  // Verify password using PBKDF2
  const parts = user.password_hash.split(":");
  if (parts.length !== 3 || parts[0] !== "pbkdf2") {
    return c.json({ error: "Invalid credentials" }, 401);
  }
  const [, salt, storedHash] = parts;
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    encoder.encode(body.password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );
  const hashBuffer = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: encoder.encode(salt), iterations: 100000, hash: "SHA-256" },
    keyMaterial,
    256,
  );
  const hashHex = Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  if (hashHex !== storedHash) {
    return c.json({ error: "Invalid credentials" }, 401);
  }

  // Update last_login_at
  await c.env.DB.prepare(
    "UPDATE users SET last_login_at = ? WHERE id = ?",
  )
    .bind(now(), user.id)
    .run();

  const token = await signToken(
    { sub: user.id, email: user.email, role: user.role },
    c.env.JWT_SECRET,
  );

  return c.json({
    data: {
      id: user.id,
      email: user.email,
      display_name: user.display_name,
      role: user.role,
      token,
    },
  });
});

/* GET /api/auth/me */
auth.get("/me", async (c) => {
  const header = c.req.header("Authorization");
  if (!header?.startsWith("Bearer ")) {
    return c.json({ error: "Unauthorized" }, 401);
  }

  const payload = await verifyToken(header.slice(7), c.env.JWT_SECRET);
  if (!payload) {
    return c.json({ error: "Invalid token" }, 401);
  }

  const user = await c.env.DB.prepare(
    "SELECT id, email, display_name, role, status, created_at FROM users WHERE id = ?",
  )
    .bind(payload.sub)
    .first();

  if (!user) {
    return c.json({ error: "User not found" }, 404);
  }

  return c.json({ data: user });
});

export default auth;
