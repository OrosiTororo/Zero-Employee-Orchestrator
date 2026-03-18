"""LLM レスポンスモッキング — テスト用の LLM 応答シミュレーション.

テスト・開発環境で LLM 呼び出しをモックし、固定レスポンスを返す。
パターンマッチによるルールベースの応答生成と、呼び出し履歴の
記録・アサーションをサポートする。

本番環境では無効化すること。
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MockRule:
    """モックルール — プロンプトパターンに対する固定レスポンス.

    Attributes
    ----------
    pattern: プロンプトにマッチする正規表現パターン
    response: マッチ時に返す固定レスポンス文字列
    latency_ms: 応答遅延（ミリ秒）。リアルなレイテンシをシミュレーション
    model_filter: 特定モデルにのみ適用するフィルター（None は全モデル対象）
    """

    pattern: str
    response: str
    latency_ms: int = 0
    model_filter: str | None = None


@dataclass
class MockCallRecord:
    """モック呼び出し記録."""

    prompt: str
    model: str
    response: dict[str, Any]
    matched_rule: MockRule | None
    timestamp: str = ""
    mock_id: str = ""


class LLMMockProvider:
    """LLM レスポンスモックプロバイダー.

    テスト時に LLM 呼び出しをインターセプトし、ルールベースの
    固定レスポンスを返す。呼び出し履歴を記録し、アサーションに利用できる。
    """

    def __init__(self) -> None:
        self._rules: list[MockRule] = []
        self._enabled: bool = False
        self._call_history: list[MockCallRecord] = []

    def add_rule(self, rule: MockRule) -> int:
        """モックルールを追加する.

        Returns
        -------
        int
            追加されたルールのインデックス
        """
        self._rules.append(rule)
        logger.info(
            "Mock rule added: pattern=%r, model_filter=%s",
            rule.pattern,
            rule.model_filter,
        )
        return len(self._rules) - 1

    def remove_rule(self, index: int) -> bool:
        """指定インデックスのモックルールを削除する."""
        if 0 <= index < len(self._rules):
            removed = self._rules.pop(index)
            logger.info("Mock rule removed: pattern=%r", removed.pattern)
            return True
        return False

    def clear_rules(self) -> None:
        """全モックルールをクリアする."""
        count = len(self._rules)
        self._rules.clear()
        logger.info("All mock rules cleared (%d rules)", count)

    def enable(self) -> None:
        """モックプロバイダーを有効化する."""
        self._enabled = True
        logger.info("LLM mock provider enabled")

    def disable(self) -> None:
        """モックプロバイダーを無効化する."""
        self._enabled = False
        logger.info("LLM mock provider disabled")

    def is_enabled(self) -> bool:
        """モックプロバイダーが有効かどうかを返す."""
        return self._enabled

    def match(self, prompt: str, model: str = "") -> MockRule | None:
        """プロンプトとモデルに一致するルールを検索する.

        ルールは登録順に評価され、最初にマッチしたものを返す。
        """
        for rule in self._rules:
            # モデルフィルターのチェック
            if rule.model_filter and model:
                if rule.model_filter not in model:
                    continue

            # パターンマッチ
            try:
                if re.search(rule.pattern, prompt, re.IGNORECASE | re.DOTALL):
                    return rule
            except re.error as exc:
                logger.warning(
                    "Invalid regex pattern in mock rule: %r — %s",
                    rule.pattern,
                    exc,
                )
                continue

        return None

    async def generate_mock_response(self, prompt: str, model: str = "") -> dict[str, Any]:
        """モック LLM レスポンスを生成する.

        マッチするルールがあればそのレスポンスを、なければデフォルトのモックを返す。
        返却形式は LiteLLM 互換の標準フォーマット。
        """
        rule = self.match(prompt, model)
        response_text = (
            rule.response if rule else f"[MOCK] No matching rule for prompt (model={model})"
        )

        # レイテンシのシミュレーション
        if rule and rule.latency_ms > 0:
            await asyncio.sleep(rule.latency_ms / 1000.0)

        mock_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        response = {
            "id": f"mock-{mock_id}",
            "object": "chat.completion",
            "created": int(datetime.now(UTC).timestamp()),
            "model": model or "mock-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split()),
            },
            "_mock": True,
            "_mock_id": mock_id,
            "_matched_rule": rule.pattern if rule else None,
        }

        # 呼び出し記録
        self.record_call(prompt, model, response, rule, now, mock_id)

        return response

    def record_call(
        self,
        prompt: str,
        model: str,
        response: dict[str, Any],
        matched_rule: MockRule | None = None,
        timestamp: str = "",
        mock_id: str = "",
    ) -> None:
        """呼び出しを履歴に記録する."""
        record = MockCallRecord(
            prompt=prompt,
            model=model,
            response=response,
            matched_rule=matched_rule,
            timestamp=timestamp or datetime.now(UTC).isoformat(),
            mock_id=mock_id or str(uuid.uuid4()),
        )
        self._call_history.append(record)

    def get_call_history(self, limit: int = 0) -> list[MockCallRecord]:
        """呼び出し履歴を返す.

        Parameters
        ----------
        limit: 返す件数の上限（0 = 全件）
        """
        if limit > 0:
            return self._call_history[-limit:]
        return list(self._call_history)

    def clear_history(self) -> None:
        """呼び出し履歴をクリアする."""
        self._call_history.clear()

    def assert_called_with(self, pattern: str) -> bool:
        """指定パターンに一致するプロンプトで呼び出されたかを検証する.

        テストのアサーションに使用する。
        """
        try:
            compiled = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        except re.error:
            logger.warning("Invalid assertion pattern: %r", pattern)
            return False

        return any(compiled.search(record.prompt) for record in self._call_history)

    def assert_call_count(self, expected: int) -> bool:
        """呼び出し回数が期待値と一致するかを検証する."""
        return len(self._call_history) == expected

    def assert_model_used(self, model: str) -> bool:
        """指定モデルが使用されたかを検証する."""
        return any(model in record.model for record in self._call_history)

    def get_summary(self) -> dict[str, Any]:
        """モックプロバイダーのサマリーを返す."""
        return {
            "enabled": self._enabled,
            "rules_count": len(self._rules),
            "call_count": len(self._call_history),
            "rules": [
                {
                    "pattern": r.pattern,
                    "response_preview": r.response[:80],
                    "latency_ms": r.latency_ms,
                    "model_filter": r.model_filter,
                }
                for r in self._rules
            ],
        }


# グローバルインスタンス
llm_mock = LLMMockProvider()
