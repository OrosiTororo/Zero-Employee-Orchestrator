import { Hono } from "hono";
import { cors } from "hono/cors";

type Bindings = {
  BACKEND_ORIGIN: string;
  RATE_LIMIT: KVNamespace;
};

const app = new Hono<{ Bindings: Bindings }>();

/* ------------------------------------------------------------------ */
/*  CORS                                                               */
/* ------------------------------------------------------------------ */
app.use(
  "*",
  cors({
    origin: "*",
    allowMethods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
    maxAge: 86400,
  }),
);

/* ------------------------------------------------------------------ */
/*  Rate Limiting (IP-based, KV-backed)                                */
/* ------------------------------------------------------------------ */
const RATE_LIMIT_WINDOW = 60; // seconds
const RATE_LIMIT_MAX = 120; // requests per window

app.use("/api/*", async (c, next) => {
  const ip = c.req.header("cf-connecting-ip") ?? "unknown";
  const key = `rl:${ip}`;

  const current = await c.env.RATE_LIMIT.get(key);
  const count = current ? parseInt(current, 10) : 0;

  if (count >= RATE_LIMIT_MAX) {
    return c.json({ error: "Rate limit exceeded" }, 429);
  }

  await c.env.RATE_LIMIT.put(key, String(count + 1), {
    expirationTtl: RATE_LIMIT_WINDOW,
  });

  await next();
});

/* ------------------------------------------------------------------ */
/*  Health check                                                       */
/* ------------------------------------------------------------------ */
app.get("/health", (c) =>
  c.json({ status: "ok", mode: "proxy", timestamp: new Date().toISOString() }),
);

/* ------------------------------------------------------------------ */
/*  Proxy — /api/* → Backend                                           */
/* ------------------------------------------------------------------ */
app.all("/api/*", async (c) => {
  const backend = c.env.BACKEND_ORIGIN.replace(/\/+$/, "");
  const url = new URL(c.req.url);
  const targetUrl = `${backend}${url.pathname}${url.search}`;

  const headers = new Headers(c.req.raw.headers);
  headers.delete("host");

  try {
    const cache = caches.default;
    const isGet = c.req.method === "GET";

    // Cache API — GET requests only
    if (isGet) {
      const cacheKey = new Request(targetUrl, { method: "GET" });
      const cached = await cache.match(cacheKey);
      if (cached) return cached;
    }

    const response = await fetch(targetUrl, {
      method: c.req.method,
      headers,
      body:
        c.req.method !== "GET" && c.req.method !== "HEAD"
          ? c.req.raw.body
          : undefined,
    });

    const proxyResponse = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });

    if (isGet && response.ok) {
      proxyResponse.headers.set("Cache-Control", "public, max-age=10");
      const ctx = c.executionCtx;
      ctx.waitUntil(cache.put(new Request(targetUrl, { method: "GET" }), proxyResponse.clone()));
    }

    return proxyResponse;
  } catch {
    return c.json(
      { error: "Backend unavailable", detail: "Could not reach the upstream server." },
      502,
    );
  }
});

/* ------------------------------------------------------------------ */
/*  Fallback — redirect to frontend                                    */
/* ------------------------------------------------------------------ */
app.all("*", (c) => c.json({ error: "Not Found" }, 404));

export default app;
