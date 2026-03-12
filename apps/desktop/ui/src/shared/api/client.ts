// In Tauri (production build) use the full URL; in Vite dev server use relative path (proxied)
const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window
const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (isTauri ? "http://localhost:18234/api/v1" : "/api/v1")

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

export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
        ...options?.headers,
      },
      ...options,
    })
  } catch {
    throw new NetworkError(
      "サーバーに接続できません。バックエンドが起動しているか確認してください。" +
        `\n(接続先: ${API_BASE})`,
    )
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
