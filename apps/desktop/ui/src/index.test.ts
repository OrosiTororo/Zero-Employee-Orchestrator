/// <reference types="node" />

import { readFileSync } from "node:fs"
import { describe, expect, it } from "vitest"

const themeCss = readFileSync("src/index.css", "utf8")

function themeBlock(selector: string): string {
  const start = themeCss.indexOf(selector)
  if (start === -1) throw new Error(`Theme selector not found: ${selector}`)

  const openBrace = themeCss.indexOf("{", start)
  const closeBrace = themeCss.indexOf("\n}", openBrace)
  return themeCss.slice(openBrace + 1, closeBrace)
}

function hexToken(block: string, name: string): string {
  const match = block.match(new RegExp(`${name}:\\s*(#[0-9A-Fa-f]{6})`))
  if (!match?.[1]) throw new Error(`Hex token not found: ${name}`)
  return match[1]
}

function relativeLuminance(hex: string): number {
  const channels = [1, 3, 5].map((offset) => Number.parseInt(hex.slice(offset, offset + 2), 16) / 255)
  const [red, green, blue] = channels.map((channel) =>
    channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
  )
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue
}

function contrastRatio(first: string, second: string): number {
  const firstLuminance = relativeLuminance(first)
  const secondLuminance = relativeLuminance(second)
  const lighter = Math.max(firstLuminance, secondLuminance)
  const darker = Math.min(firstLuminance, secondLuminance)
  return (lighter + 0.05) / (darker + 0.05)
}

describe("theme contrast", () => {
  const dark = themeBlock('[data-theme="dark"]')
  const light = themeBlock('[data-theme="light"]')

  it("keeps dark-theme accent text and filled controls at WCAG AA contrast", () => {
    expect(
      contrastRatio(hexToken(dark, "--accent"), hexToken(dark, "--bg-overlay")),
    ).toBeGreaterThanOrEqual(4.5)
    expect(
      contrastRatio(hexToken(dark, "--accent"), hexToken(dark, "--accent-fg")),
    ).toBeGreaterThanOrEqual(4.5)
    expect(
      contrastRatio(hexToken(dark, "--accent-hover"), hexToken(dark, "--accent-fg")),
    ).toBeGreaterThanOrEqual(4.5)
  })

  it("keeps light-theme accent and status text at WCAG AA contrast", () => {
    const navigationSurface = hexToken(light, "--bg-nav-bar")
    expect(
      contrastRatio(hexToken(light, "--accent"), navigationSurface),
    ).toBeGreaterThanOrEqual(4.5)
    expect(
      contrastRatio(hexToken(light, "--accent"), hexToken(light, "--accent-fg")),
    ).toBeGreaterThanOrEqual(4.5)
    expect(
      contrastRatio(hexToken(light, "--accent-hover"), hexToken(light, "--accent-fg")),
    ).toBeGreaterThanOrEqual(4.5)
    expect(
      contrastRatio(hexToken(light, "--success-fg"), navigationSurface),
    ).toBeGreaterThanOrEqual(4.5)
    expect(
      contrastRatio(hexToken(light, "--info"), navigationSurface),
    ).toBeGreaterThanOrEqual(4.5)
  })
})
