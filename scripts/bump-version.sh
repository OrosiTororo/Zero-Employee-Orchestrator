#!/bin/bash
# scripts/bump-version.sh — unified version sync script
#
# Usage:
#   ./scripts/bump-version.sh 0.2.0
#   ./scripts/bump-version.sh 1.0.0-rc1
#
# Updates version in all version-bearing files:
#   - pyproject.toml (root + apps/api)
#   - package.json (apps/desktop, apps/desktop/ui, apps/edge/proxy, apps/edge/full)
#   - tauri.conf.json (apps/desktop/src-tauri)
#   - Cargo.toml (apps/desktop/src-tauri)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ────────────────────────────────────────────
# Argument check
# ────────────────────────────────────────────
if [ $# -ne 1 ]; then
  echo "Usage: $0 <version>"
  echo "  e.g.: $0 0.2.0"
  echo "  e.g.: $0 1.0.0-rc1"
  exit 1
fi

NEW_VERSION="$1"

# Version format validation (PEP 440 compatible: X.Y.Z or X.Y.Z-suffix)
if ! echo "$NEW_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
  echo "Invalid version format: $NEW_VERSION"
  echo "   Valid formats: X.Y.Z or X.Y.Z-suffix (e.g., 0.2.0, 1.0.0-rc1)"
  exit 1
fi

# ────────────────────────────────────────────
# File lists
# ────────────────────────────────────────────
PYPROJECT_FILES=(
  "$REPO_ROOT/pyproject.toml"
  "$REPO_ROOT/apps/api/pyproject.toml"
)

PACKAGE_JSON_FILES=(
  "$REPO_ROOT/apps/desktop/package.json"
  "$REPO_ROOT/apps/desktop/ui/package.json"
  "$REPO_ROOT/apps/edge/proxy/package.json"
  "$REPO_ROOT/apps/edge/full/package.json"
)

CARGO_TOML="$REPO_ROOT/apps/desktop/src-tauri/Cargo.toml"
TAURI_CONF="$REPO_ROOT/apps/desktop/src-tauri/tauri.conf.json"

# i18n locale files (common.version = "vX.Y.Z")
LOCALE_DIR="$REPO_ROOT/apps/desktop/ui/src/shared/i18n/locales"
LOCALE_FILES=(
  "$LOCALE_DIR/en.json"
  "$LOCALE_DIR/ja.json"
  "$LOCALE_DIR/zh.json"
  "$LOCALE_DIR/ko.json"
  "$LOCALE_DIR/pt.json"
  "$LOCALE_DIR/tr.json"
)

# WhatsNew component (CURRENT_VERSION)
WHATS_NEW="$REPO_ROOT/apps/desktop/ui/src/shared/ui/WhatsNew.tsx"

# ────────────────────────────────────────────
# Helper functions
# ────────────────────────────────────────────
get_toml_version() {
  grep -m1 '^version = ' "$1" | sed 's/version = "\(.*\)"/\1/'
}

get_json_version() {
  grep -m1 '"version"' "$1" | sed 's/.*"version": *"\(.*\)".*/\1/'
}

update_toml_version() {
  local file="$1"
  sed -i "0,/^version = \".*\"/s//version = \"$NEW_VERSION\"/" "$file"
}

update_json_version() {
  local file="$1"
  sed -i "s/\"version\": *\"[^\"]*\"/\"version\": \"$NEW_VERSION\"/" "$file"
}

# ────────────────────────────────────────────
# Show current state
# ────────────────────────────────────────────
echo "=========================================="
echo " Zero-Employee Orchestrator Version Update"
echo "=========================================="
echo ""
echo "New version: $NEW_VERSION"
echo ""
echo "Current versions:"

for f in "${PYPROJECT_FILES[@]}"; do
  label="${f#$REPO_ROOT/}"
  echo "  $label: $(get_toml_version "$f")"
done
for f in "${PACKAGE_JSON_FILES[@]}"; do
  label="${f#$REPO_ROOT/}"
  echo "  $label: $(get_json_version "$f")"
done
echo "  apps/desktop/src-tauri/Cargo.toml: $(get_toml_version "$CARGO_TOML")"
echo "  apps/desktop/src-tauri/tauri.conf.json: $(get_json_version "$TAURI_CONF")"
echo ""

# ────────────────────────────────────────────
# Update all files
# ────────────────────────────────────────────
echo "Updating..."

for f in "${PYPROJECT_FILES[@]}"; do
  update_toml_version "$f"
  echo "  Updated ${f#$REPO_ROOT/}"
done

for f in "${PACKAGE_JSON_FILES[@]}"; do
  update_json_version "$f"
  echo "  Updated ${f#$REPO_ROOT/}"
done

update_toml_version "$CARGO_TOML"
echo "  Updated apps/desktop/src-tauri/Cargo.toml"

update_json_version "$TAURI_CONF"
echo "  Updated apps/desktop/src-tauri/tauri.conf.json"

# Update i18n locale files (common.version field only — first occurrence)
for f in "${LOCALE_FILES[@]}"; do
  if [ -f "$f" ]; then
    sed -i "0,/\"version\": *\"v[^\"]*\"/s//\"version\": \"v$NEW_VERSION\"/" "$f"
    echo "  Updated ${f#$REPO_ROOT/}"
  fi
done

# Update WhatsNew.tsx hardcoded version
if [ -f "$WHATS_NEW" ]; then
  sed -i "s/const CURRENT_VERSION = \"[^\"]*\"/const CURRENT_VERSION = \"$NEW_VERSION\"/" "$WHATS_NEW"
  echo "  Updated ${WHATS_NEW#$REPO_ROOT/}"
fi

# ────────────────────────────────────────────
# Post-update verification
# ────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Post-Update Verification"
echo "=========================================="

FAILED=0

for f in "${PYPROJECT_FILES[@]}"; do
  v=$(get_toml_version "$f")
  label="${f#$REPO_ROOT/}"
  if [ "$v" = "$NEW_VERSION" ]; then
    echo "  ✓ $label: $v"
  else
    echo "  ✗ $label: $v (expected $NEW_VERSION)"
    FAILED=1
  fi
done

for f in "${PACKAGE_JSON_FILES[@]}"; do
  v=$(get_json_version "$f")
  label="${f#$REPO_ROOT/}"
  if [ "$v" = "$NEW_VERSION" ]; then
    echo "  ✓ $label: $v"
  else
    echo "  ✗ $label: $v (expected $NEW_VERSION)"
    FAILED=1
  fi
done

v=$(get_toml_version "$CARGO_TOML")
if [ "$v" = "$NEW_VERSION" ]; then
  echo "  ✓ apps/desktop/src-tauri/Cargo.toml: $v"
else
  echo "  ✗ apps/desktop/src-tauri/Cargo.toml: $v (expected $NEW_VERSION)"
  FAILED=1
fi

v=$(get_json_version "$TAURI_CONF")
if [ "$v" = "$NEW_VERSION" ]; then
  echo "  ✓ apps/desktop/src-tauri/tauri.conf.json: $v"
else
  echo "  ✗ apps/desktop/src-tauri/tauri.conf.json: $v (expected $NEW_VERSION)"
  FAILED=1
fi

# Verify locale files
for f in "${LOCALE_FILES[@]}"; do
  if [ -f "$f" ]; then
    v=$(grep -m1 '"version": "v' "$f" | sed 's/.*"version": "v\(.*\)".*/\1/')
    label="${f#$REPO_ROOT/}"
    if [ "$v" = "$NEW_VERSION" ]; then
      echo "  ✓ $label: v$v"
    else
      echo "  ✗ $label: v$v (expected v$NEW_VERSION)"
      FAILED=1
    fi
  fi
done

# Verify WhatsNew.tsx
if [ -f "$WHATS_NEW" ]; then
  v=$(grep 'const CURRENT_VERSION' "$WHATS_NEW" | sed 's/.*"\(.*\)".*/\1/')
  label="${WHATS_NEW#$REPO_ROOT/}"
  if [ "$v" = "$NEW_VERSION" ]; then
    echo "  ✓ $label: $v"
  else
    echo "  ✗ $label: $v (expected $NEW_VERSION)"
    FAILED=1
  fi
fi

echo ""
if [ "$FAILED" -eq 0 ]; then
  echo "All version files updated to $NEW_VERSION"
  exit 0
else
  echo "Some files failed to update. Please check manually."
  exit 1
fi
