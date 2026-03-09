import { Hono } from "hono";
import type { Bindings, Variables } from "./lib/types";
import { corsMiddleware } from "./middleware/cors";
import { auditMiddleware } from "./middleware/audit";
import auth from "./routes/auth";
import companies from "./routes/companies";
import tickets from "./routes/tickets";
import agents from "./routes/agents";
import tasks from "./routes/tasks";
import approvals from "./routes/approvals";
import health from "./routes/health";

const app = new Hono<{ Bindings: Bindings; Variables: Variables }>();

/* ------------------------------------------------------------------ */
/*  Global middleware                                                   */
/* ------------------------------------------------------------------ */
app.use("*", corsMiddleware);
app.use("/api/*", auditMiddleware);

/* ------------------------------------------------------------------ */
/*  Global error handler                                               */
/* ------------------------------------------------------------------ */
app.onError((err, c) => {
  console.error("Unhandled error:", err);
  return c.json(
    { error: "Internal Server Error", detail: err.message },
    500,
  );
});

/* ------------------------------------------------------------------ */
/*  Routes                                                             */
/* ------------------------------------------------------------------ */
app.route("/health", health);
app.route("/api/auth", auth);
app.route("/api/companies", companies);
app.route("/api", tickets);
app.route("/api", agents);
app.route("/api", tasks);
app.route("/api", approvals);

/* ------------------------------------------------------------------ */
/*  Fallback                                                           */
/* ------------------------------------------------------------------ */
app.all("*", (c) => c.json({ error: "Not Found" }, 404));

export default app;
