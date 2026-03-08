#!/bin/bash
# フロントエンド開発サーバー起動
cd "$(dirname "$0")/../../apps/desktop/ui"
echo "Starting Zero-Employee Orchestrator UI..."
pnpm dev
