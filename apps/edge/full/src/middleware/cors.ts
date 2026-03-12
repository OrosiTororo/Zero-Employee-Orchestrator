import { cors } from "hono/cors";

/**
 * CORS middleware configured for the ZEO API.
 *
 * In production, set the CORS_ORIGINS environment variable to restrict
 * allowed origins: e.g. "https://your-app.example.com"
 */
export const createCorsMiddleware = (allowedOrigins?: string) => {
  const origins = allowedOrigins
    ? allowedOrigins.split(",").map((o) => o.trim())
    : ["http://localhost:5173", "http://localhost:1420"];

  return cors({
    origin: origins,
    allowMethods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
    maxAge: 86400,
  });
};
