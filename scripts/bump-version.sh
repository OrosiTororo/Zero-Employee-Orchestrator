#!/bin/bash
# scripts/bump-version.sh — pyproject.toml バージョン同期スクリプト
#
# 使い方:
#   ./scripts/bump-version.sh 0.2.0
#   ./scripts/bump-version.sh 1.0.0-rc1
#
# root/pyproject.toml と apps/api/pyproject.toml の両方のバージョンを更新し、
# 更新後に一致を確認する。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_TOML="$REPO_ROOT/pyproject.toml"
API_TOML="$REPO_ROOT/apps/api/pyproject.toml"

# ────────────────────────────────────────────
# 引数チェック
# ────────────────────────────────────────────
if [ $# -ne 1 ]; then
  echo "Usage: $0 <version>"
  echo "  例: $0 0.2.0"
  echo "  例: $0 1.0.0-rc1"
  exit 1
fi

NEW_VERSION="$1"

# バージョン形式の検証 (PEP 440 互換: X.Y.Z or X.Y.Z-suffix)
if ! echo "$NEW_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
  echo "❌ 無効なバージョン形式: $NEW_VERSION"
  echo "   有効な形式: X.Y.Z または X.Y.Z-suffix (例: 0.2.0, 1.0.0-rc1)"
  exit 1
fi

# ────────────────────────────────────────────
# 現在のバージョンを取得
# ────────────────────────────────────────────
get_version() {
  grep -m1 '^version = ' "$1" | sed 's/version = "\(.*\)"/\1/'
}

CURRENT_ROOT=$(get_version "$ROOT_TOML")
CURRENT_API=$(get_version "$API_TOML")

echo "=========================================="
echo " Zero-Employee Orchestrator バージョン更新"
echo "=========================================="
echo ""
echo "現在のバージョン:"
echo "  root/pyproject.toml:     $CURRENT_ROOT"
echo "  apps/api/pyproject.toml: $CURRENT_API"
echo ""
echo "新しいバージョン: $NEW_VERSION"
echo ""

if [ "$CURRENT_ROOT" != "$CURRENT_API" ]; then
  echo "⚠️  警告: 現在のバージョンが一致していません！"
  echo ""
fi

# ────────────────────────────────────────────
# バージョンを更新
# ────────────────────────────────────────────
# sed で version = "X.Y.Z" を置換（最初の出現のみ）
update_version() {
  local file="$1"
  local label="$2"
  if sed -i "0,/^version = \".*\"/s//version = \"$NEW_VERSION\"/" "$file"; then
    echo "✅ $label を更新しました"
  else
    echo "❌ $label の更新に失敗しました"
    exit 1
  fi
}

update_version "$ROOT_TOML" "root/pyproject.toml"
update_version "$API_TOML"  "apps/api/pyproject.toml"

# ────────────────────────────────────────────
# 更新後の確認
# ────────────────────────────────────────────
echo ""
echo "=========================================="
echo " 更新後の確認"
echo "=========================================="

UPDATED_ROOT=$(get_version "$ROOT_TOML")
UPDATED_API=$(get_version "$API_TOML")

echo "  root/pyproject.toml:     $UPDATED_ROOT"
echo "  apps/api/pyproject.toml: $UPDATED_API"
echo ""

if [ "$UPDATED_ROOT" = "$NEW_VERSION" ] && [ "$UPDATED_API" = "$NEW_VERSION" ]; then
  echo "✅ 両ファイルのバージョンが一致しています: $NEW_VERSION"
  exit 0
else
  echo "❌ バージョンの更新に問題があります。手動で確認してください。"
  exit 1
fi
