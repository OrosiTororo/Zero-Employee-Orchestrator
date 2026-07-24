import { describe, expect, it } from "vitest"
import { getCommandPaletteShortcutLabel } from "./use-command-palette"

describe("getCommandPaletteShortcutLabel", () => {
  it("uses the Command symbol on Apple platforms", () => {
    expect(
      getCommandPaletteShortcutLabel(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/617.1",
      ),
    ).toBe("⌘K")
  })

  it("uses Ctrl on Windows and Linux platforms", () => {
    expect(
      getCommandPaletteShortcutLabel(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      ),
    ).toBe("Ctrl+K")
    expect(
      getCommandPaletteShortcutLabel(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
      ),
    ).toBe("Ctrl+K")
  })
})
