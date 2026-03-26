#!/bin/bash
# scripts/bump-version.sh — pyproject.toml version sync script
#
# Usage:
#   ./scripts/bump-version.sh 0.2.0
#   ./scripts/bump-version.sh 1.0.0-rc1
#
# Updates version in both root/pyproject.toml and apps/api/pyproject.toml,
# then verifies they match.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_TOML="$REPO_ROOT/pyproject.toml"
API_TOML="$REPO_ROOT/apps/api/pyproject.toml"

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
# Get current versions
# ────────────────────────────────────────────
get_version() {
  grep -m1 '^version = ' "$1" | sed 's/version = "\(.*\)"/\1/'
}

CURRENT_ROOT=$(get_version "$ROOT_TOML")
CURRENT_API=$(get_version "$API_TOML")

echo "=========================================="
echo " Zero-Employee Orchestrator Version Update"
echo "=========================================="
echo ""
echo "Current versions:"
echo "  root/pyproject.toml:     $CURRENT_ROOT"
echo "  apps/api/pyproject.toml: $CURRENT_API"
echo ""
echo "New version: $NEW_VERSION"
echo ""

if [ "$CURRENT_ROOT" != "$CURRENT_API" ]; then
  echo "Warning: Current versions do not match!"
  echo ""
fi

# ────────────────────────────────────────────
# Update versions
# ────────────────────────────────────────────
# Replace version = "X.Y.Z" with sed (first occurrence only)
update_version() {
  local file="$1"
  local label="$2"
  if sed -i "0,/^version = \".*\"/s//version = \"$NEW_VERSION\"/" "$file"; then
    echo "Updated $label"
  else
    echo "Failed to update $label"
    exit 1
  fi
}

update_version "$ROOT_TOML" "root/pyproject.toml"
update_version "$API_TOML"  "apps/api/pyproject.toml"

# ────────────────────────────────────────────
# Post-update verification
# ────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Post-Update Verification"
echo "=========================================="

UPDATED_ROOT=$(get_version "$ROOT_TOML")
UPDATED_API=$(get_version "$API_TOML")

echo "  root/pyproject.toml:     $UPDATED_ROOT"
echo "  apps/api/pyproject.toml: $UPDATED_API"
echo ""

if [ "$UPDATED_ROOT" = "$NEW_VERSION" ] && [ "$UPDATED_API" = "$NEW_VERSION" ]; then
  echo "Both files match: $NEW_VERSION"
  exit 0
else
  echo "Version update failed. Please check manually."
  exit 1
fi
