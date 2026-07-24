import { create } from "zustand"

interface CommandPaletteState {
  open: boolean
  setOpen: (open: boolean) => void
  toggle: () => void
}

export function getCommandPaletteShortcutLabel(
  userAgent = typeof navigator === "undefined" ? "" : navigator.userAgent,
): string {
  return /Macintosh|Mac OS X|iPhone|iPad|iPod/.test(userAgent) ? "⌘K" : "Ctrl+K"
}

/**
 * Shared open/close state for the Command Palette so chrome elements
 * (title-bar search button) can summon it in addition to Ctrl/Cmd+K.
 */
export const useCommandPalette = create<CommandPaletteState>((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
  toggle: () => set((s) => ({ open: !s.open })),
}))
