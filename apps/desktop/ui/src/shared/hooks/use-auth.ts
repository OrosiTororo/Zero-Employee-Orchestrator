import { create } from 'zustand'
import { api } from '@/shared/api/client'

interface AuthState {
  authenticated: boolean
  loading: boolean
  token: string | null
  login: (email: string, provider?: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  setToken: (token: string) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  authenticated: false,
  loading: true,
  token: localStorage.getItem("auth_token"),

  login: async (email: string, provider?: string) => {
    try {
      const res = await api.post<{ token: string }>("/auth/login", {
        email,
        provider: provider ?? "openrouter",
      })
      localStorage.setItem("auth_token", res.token)
      set({ authenticated: true, token: res.token })
    } catch (e) {
      console.error("Login failed:", e)
      throw e
    }
  },

  logout: () => {
    localStorage.removeItem("auth_token")
    set({ authenticated: false, token: null })
  },

  checkAuth: async () => {
    try {
      const res = await api.get<{ authenticated: boolean }>("/auth/status")
      set({ authenticated: res.authenticated, loading: false })
    } catch {
      set({ authenticated: false, loading: false })
    }
  },

  setToken: (token: string) => {
    localStorage.setItem("auth_token", token)
    set({ authenticated: true, token })
  },
}))

// Check auth on load
useAuthStore.getState().checkAuth()
