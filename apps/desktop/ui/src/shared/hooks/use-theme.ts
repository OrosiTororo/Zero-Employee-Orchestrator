import { create } from "zustand"

export type Theme = "dark" | "light" | "high-contrast"

export const THEME_LABELS: Record<Theme, string> = {
  dark: "Dark",
  light: "Light",
  "high-contrast": "High Contrast",
}

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
}

function getInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem("theme")
    if (stored && (stored === "dark" || stored === "light" || stored === "high-contrast")) {
      return stored
    }
  } catch {
    // ignore
  }
  return "dark"
}

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme)
}

export const useTheme = create<ThemeState>((set) => {
  const initial = getInitialTheme()
  applyTheme(initial)
  return {
    theme: initial,
    setTheme: (theme: Theme) => {
      try {
        localStorage.setItem("theme", theme)
      } catch {
        // ignore
      }
      applyTheme(theme)
      set({ theme })
    },
  }
})
