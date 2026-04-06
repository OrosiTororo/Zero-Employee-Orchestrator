// In Tauri (production build) use the full URL; in Vite dev server use relative path (proxied)
const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window
const isDev = import.meta.env.DEV
const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (isTauri && !isDev ? "http://127.0.0.1:18234/api/v1" : "/api/v1")

/** Base URL without the /api/v1 suffix, used for health checks. */
const SERVER_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1$/, "") ||
  (isTauri && !isDev ? "http://127.0.0.1:18234" : "")

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("auth_token")
  if (token) {
    return { Authorization: `Bearer ${token}` }
  }
  return {}
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "NetworkError"
  }
}

/**
 * Wait for the backend to become reachable (health check).
 * Returns true if the backend responded within the retry window.
 */
export async function waitForBackend(
  maxAttempts = 10,
  intervalMs = 1000,
): Promise<boolean> {
  const healthUrl = SERVER_BASE
    ? `${SERVER_BASE}/healthz`
    : "/healthz"

  for (let i = 0; i < maxAttempts; i++) {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000)
      const res = await fetch(healthUrl, {
        method: "GET",
        signal: controller.signal,
      })
      clearTimeout(timeout)
      if (res.ok) return true
    } catch {
      // Backend not yet reachable — retry
    }
    if (i < maxAttempts - 1) {
      await new Promise((r) => setTimeout(r, intervalMs))
    }
  }
  return false
}

/**
 * Try to refresh the current token. Returns true if successful.
 */
async function tryRefreshToken(): Promise<boolean> {
  const token = localStorage.getItem("auth_token")
  if (!token) return false
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    })
    if (res.ok) {
      const data = await res.json()
      if (data.access_token) {
        localStorage.setItem("auth_token", data.access_token)
        return true
      }
    }
  } catch {
    // refresh failed
  }
  return false
}

// Track if a refresh is in-flight to avoid duplicates
let refreshPromise: Promise<boolean> | null = null

export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  let res: Response
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 30000)
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
        ...options?.headers,
      },
      ...options,
      signal: options?.signal ?? controller.signal,
    })
  } catch {
    clearTimeout(timeout)
    // First attempt failed — the backend may still be starting (sidecar).
    // Wait for backend readiness and retry once.
    const ready = await waitForBackend(5, 1000)
    if (ready) {
      const retryController = new AbortController()
      const retryTimeout = setTimeout(() => retryController.abort(), 30000)
      try {
        res = await fetch(`${API_BASE}${path}`, {
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
            ...options?.headers,
          },
          ...options,
          signal: options?.signal ?? retryController.signal,
        })
        clearTimeout(retryTimeout)
      } catch {
        clearTimeout(retryTimeout)
        throw new NetworkError(
          "Cannot connect to server. Please check that the backend is running." +
            `\n(Target: ${API_BASE})`,
        )
      }
    } else {
      throw new NetworkError(
        "Cannot connect to server. Please check that the backend is running." +
          `\n(Target: ${API_BASE})`,
      )
    }
  }
  clearTimeout(timeout)

  // Handle 401 — attempt token refresh once, then retry the original request
  if (res.status === 401 && !path.startsWith("/auth/")) {
    if (!refreshPromise) {
      refreshPromise = tryRefreshToken().finally(() => { refreshPromise = null })
    }
    const refreshed = await refreshPromise
    if (refreshed) {
      // Retry with the new token
      const retryRes = await fetch(`${API_BASE}${path}`, {
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
          ...options?.headers,
        },
        ...options,
      })
      if (retryRes.ok) {
        return retryRes.json()
      }
      // If retry also fails, fall through to error handling
      const err = await retryRes.json().catch(() => ({ detail: retryRes.statusText }))
      throw new ApiError(err.detail || retryRes.statusText, retryRes.status)
    }
    // Refresh failed — throw 401 so the caller can handle logout
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(err.detail || res.statusText, res.status)
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(err.detail || res.statusText, res.status)
  }

  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string) =>
    request<T>(path, { method: "DELETE" }),
}
