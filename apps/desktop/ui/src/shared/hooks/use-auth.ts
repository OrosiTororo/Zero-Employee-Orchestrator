import { create } from 'zustand'
import { api, waitForBackend } from '@/shared/api/client'

interface AuthState {
  authenticated: boolean
  loading: boolean
  token: string | null
  userId: string | null
  displayName: string | null
  isAnonymous: boolean
  setupCompleted: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  startAnonymous: () => Promise<void>
  linkAccount: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  setToken: (token: string) => void
  setSetupCompleted: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  authenticated: !!localStorage.getItem("auth_token"),
  loading: true,
  token: localStorage.getItem("auth_token"),
  userId: null,
  displayName: null,
  isAnonymous: localStorage.getItem("is_anonymous") === "true",
  setupCompleted: localStorage.getItem("setup_completed") === "true",

  login: async (email: string, password: string) => {
    const res = await api.post<{
      access_token: string
      user_id: string
      display_name: string
      setup_completed?: boolean
    }>("/auth/login", { email, password })
    localStorage.setItem("auth_token", res.access_token)
    localStorage.removeItem("is_anonymous")
    if (res.setup_completed) localStorage.setItem("setup_completed", "true")
    else localStorage.removeItem("setup_completed")
    set({
      authenticated: true,
      token: res.access_token,
      userId: res.user_id,
      displayName: res.display_name,
      isAnonymous: false,
      setupCompleted: !!res.setup_completed,
    })
  },

  register: async (email: string, password: string, displayName: string) => {
    const res = await api.post<{
      access_token: string
      user_id: string
      display_name: string
      setup_completed?: boolean
    }>("/auth/register", { email, password, display_name: displayName })
    localStorage.setItem("auth_token", res.access_token)
    localStorage.removeItem("is_anonymous")
    localStorage.removeItem("setup_completed")
    set({
      authenticated: true,
      token: res.access_token,
      userId: res.user_id,
      displayName: res.display_name,
      isAnonymous: false,
      setupCompleted: false,
    })
  },

  startAnonymous: async () => {
    const res = await api.post<{
      access_token: string
      user_id: string
      company_id: string
      display_name: string
      is_anonymous: boolean
      setup_completed?: boolean
    }>("/auth/anonymous-session")
    localStorage.setItem("auth_token", res.access_token)
    localStorage.setItem("company_id", res.company_id)
    localStorage.setItem("is_anonymous", "true")
    localStorage.removeItem("setup_completed")
    set({
      authenticated: true,
      token: res.access_token,
      userId: res.user_id,
      displayName: res.display_name,
      isAnonymous: true,
      setupCompleted: false,
    })
  },

  linkAccount: async (email: string, password: string, displayName: string) => {
    const res = await api.post<{
      access_token: string
      user_id: string
      display_name: string
      linked: boolean
    }>("/auth/link-account", { email, password, display_name: displayName })
    localStorage.setItem("auth_token", res.access_token)
    localStorage.removeItem("is_anonymous")
    set({
      authenticated: true,
      token: res.access_token,
      userId: res.user_id,
      displayName: res.display_name,
      isAnonymous: false,
    })
  },

  logout: () => {
    localStorage.removeItem("auth_token")
    localStorage.removeItem("is_anonymous")
    localStorage.removeItem("setup_completed")
    set({ authenticated: false, token: null, userId: null, displayName: null, isAnonymous: false, setupCompleted: false })
  },

  checkAuth: async () => {
    const token = localStorage.getItem("auth_token")
    if (!token) {
      set({ authenticated: false, loading: false })
      return
    }
    // Wait for backend to be ready (sidecar may still be starting)
    await waitForBackend(10, 1000)
    try {
      const res = await api.get<{ id: string; display_name: string; role: string }>("/auth/me")
      let setupDone = localStorage.getItem("setup_completed") === "true"
      try {
        const status = await api.get<{ setup_completed: boolean }>("/auth/setup-status")
        setupDone = status.setup_completed
        if (setupDone) localStorage.setItem("setup_completed", "true")
        else localStorage.removeItem("setup_completed")
      } catch {
        // setup-status endpoint may not be available yet
      }
      set({
        authenticated: true,
        loading: false,
        userId: res.id,
        displayName: res.display_name,
        isAnonymous: res.role === "anonymous",
        setupCompleted: setupDone,
      })
    } catch {
      localStorage.removeItem("auth_token")
      set({ authenticated: false, loading: false, token: null })
    }
  },

  setToken: (token: string) => {
    localStorage.setItem("auth_token", token)
    set({ authenticated: true, token })
  },

  setSetupCompleted: () => {
    localStorage.setItem("setup_completed", "true")
    set({ setupCompleted: true })
  },
}))

// Check auth on load
useAuthStore.getState().checkAuth()
