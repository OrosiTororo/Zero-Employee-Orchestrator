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
import specs from "./routes/specs";
import audit from "./routes/audit";
import budgets from "./routes/budgets";
import projects from "./routes/projects";
import registry from "./routes/registry";
import artifacts from "./routes/artifacts";
import heartbeats from "./routes/heartbeats";
import reviews from "./routes/reviews";
import health from "./routes/health";

const INSECURE_DEFAULTS = new Set([
  "change-me-in-production",
  "CHANGE-ME-in-production",
  "change-this-to-a-random-secret-key",
]);

const app = new Hono<{ Bindings: Bindings; Variables: Variables }>();

/* ------------------------------------------------------------------ */
/*  Global middleware                                                   */
/* ------------------------------------------------------------------ */
app.use("*", corsMiddleware);

/* Block API requests when JWT_SECRET is still the insecure default. */
app.use("/api/*", async (c, next) => {
  if (INSECURE_DEFAULTS.has(c.env.JWT_SECRET)) {
    return c.json(
      {
        error: "Insecure configuration",
        detail:
          "JWT_SECRET is set to an insecure default value. " +
          "Run: wrangler secret put JWT_SECRET",
      },
      503,
    );
  }
  await next();
});

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
app.route("/api", specs);
app.route("/api", audit);
app.route("/api", budgets);
app.route("/api", projects);
app.route("/api", registry);
app.route("/api", artifacts);
app.route("/api", heartbeats);
app.route("/api", reviews);

/* ------------------------------------------------------------------ */
/*  Fallback                                                           */
/* ------------------------------------------------------------------ */
app.all("*", (c) => c.json({ error: "Not Found" }, 404));

export default app;
