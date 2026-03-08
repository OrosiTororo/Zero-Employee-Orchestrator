"""Zero-Employee Orchestrator Worker — バックグラウンドタスク実行エンジン.

このワーカーは以下を担当する:
- Heartbeat ポリシーに基づく定期タスク実行
- タスクキューからのタスク取得と実行
- Provider 経由の LLM 呼び出し
- 実行結果の記録と状態遷移
- DAG 内の ready ノードの自動実行
- 失敗時の Self-Healing と Re-Propose
"""

import asyncio
import logging
import signal
import sys

from app.runners.task_runner import TaskRunner
from app.runners.heartbeat_runner import HeartbeatRunner
from app.dispatchers.event_dispatcher import EventDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Graceful shutdown
shutdown_event = asyncio.Event()


def handle_signal(sig, frame):
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_event.set()


async def main():
    """ワーカーのメインループ."""
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logger.info("Zero-Employee Orchestrator Worker starting...")

    task_runner = TaskRunner()
    heartbeat_runner = HeartbeatRunner()
    event_dispatcher = EventDispatcher()

    # Run all runners concurrently
    tasks = [
        asyncio.create_task(task_runner.run(shutdown_event)),
        asyncio.create_task(heartbeat_runner.run(shutdown_event)),
        asyncio.create_task(event_dispatcher.run(shutdown_event)),
    ]

    logger.info("All runners started. Waiting for tasks...")

    # Wait for shutdown signal
    await shutdown_event.wait()
    logger.info("Shutdown signal received, stopping runners...")

    for t in tasks:
        t.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
