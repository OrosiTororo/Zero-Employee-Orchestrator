#!/bin/bash
# バックエンド開発サーバー起動
cd "$(dirname "$0")/../../apps/api"
echo "Starting Zero-Employee Orchestrator API server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 18234
