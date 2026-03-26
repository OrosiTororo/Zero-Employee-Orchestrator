#!/bin/bash
# Start frontend development server
cd "$(dirname "$0")/../../apps/desktop/ui"
echo "Starting Zero-Employee Orchestrator UI..."
pnpm dev
