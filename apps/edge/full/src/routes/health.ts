import { Hono } from "hono";
import type { Bindings, Variables } from "../lib/types";

const health = new Hono<{ Bindings: Bindings; Variables: Variables }>();

/* GET /health */
health.get("/", (c) =>
  c.json({
    status: "ok",
    mode: "full",
    timestamp: new Date().toISOString(),
  }),
);

export default health;
