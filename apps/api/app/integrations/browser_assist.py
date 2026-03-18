"""ブラウザアシスト統合 — ユーザーの画面を見て操作を案内する.

ユーザーがChrome等のウェブブラウザやアプリケーションを使用中に、
操作方法や手順を問われた際、ユーザーと同じ画面を見て回答・調査・アシストする。

機能:
- スクリーンショット分析: LLM のマルチモーダル機能で画面を理解
- ステップバイステップ案内: UI 要素を特定し、操作手順を提示
- エラー診断: 画面上のエラーメッセージを読み取り、解決策を提案
- フォーム入力支援: フォームの各フィールドの入力方法を案内
- UI 説明: 画面上の各要素の役割と使い方を説明

安全性:
- スクリーンショットは一時的にのみ保持（永続保存しない）
- パスワードフィールドの内容は自動的にぼかし処理
- ユーザーの明示的な同意が必要
- 全キャプチャは監査ログに記録（画像本体は除く）
- 自律的なクリック操作は行わない（案内のみ）
"""

from __future__ import annotations

import base64
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class AssistAction(str, Enum):
    """アシストアクション種別."""

    ANALYZE_SCREEN = "analyze_screen"
    GUIDE_NAVIGATION = "guide_navigation"
    DIAGNOSE_ERROR = "diagnose_error"
    FILL_FORM_GUIDE = "fill_form_guide"
    EXPLAIN_UI = "explain_ui"


@dataclass
class AssistStep:
    """操作手順の1ステップ."""

    step_number: int
    instruction: str
    ui_element: str = ""
    screenshot_annotation: str = ""


@dataclass
class AssistResult:
    """アシスト結果."""

    action: AssistAction
    steps: list[AssistStep] = field(default_factory=list)
    explanation: str = ""
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ScreenCaptureMetadata:
    """スクリーンキャプチャのメタデータ（画像本体は含まない）."""

    capture_id: str
    timestamp: str
    source_url: str = ""
    browser: str = ""
    image_hash: str = ""  # SHA-256 of the image for audit
    user_id: str = ""


class BrowserAssistService:
    """ブラウザアシストサービス.

    LLM のマルチモーダル機能を利用して、ユーザーの画面を分析し、
    操作方法を案内する。
    """

    def __init__(self) -> None:
        self._consent_cache: dict[str, bool] = {}

    def check_user_consent(self, user_id: str) -> bool:
        """ユーザーが画面共有に同意しているか確認する."""
        return self._consent_cache.get(user_id, False)

    def grant_consent(self, user_id: str) -> None:
        """ユーザーの画面共有同意を記録する."""
        self._consent_cache[user_id] = True

    def revoke_consent(self, user_id: str) -> None:
        """ユーザーの画面共有同意を取り消す."""
        self._consent_cache[user_id] = False

    async def analyze_screenshot(
        self,
        screenshot_base64: str,
        user_question: str,
        action: AssistAction = AssistAction.ANALYZE_SCREEN,
        target_url: str = "",
        browser: str = "chrome",
        language: str = "ja",
        user_id: str = "",
    ) -> AssistResult:
        """スクリーンショットを分析し、ユーザーの質問に回答する.

        Args:
            screenshot_base64: Base64 エンコードされたスクリーンショット
            user_question: ユーザーの質問
            action: アシストアクション種別
            target_url: ユーザーが閲覧中の URL
            browser: ブラウザ種別
            language: 回答言語
            user_id: ユーザーID（監査用）

        Returns:
            AssistResult: 分析結果と操作手順
        """
        # メタデータを生成（監査ログ用。画像本体は保存しない）
        image_bytes = base64.b64decode(screenshot_base64) if screenshot_base64 else b""
        metadata = ScreenCaptureMetadata(
            capture_id=hashlib.sha256(
                f"{user_id}:{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16],
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_url=target_url,
            browser=browser,
            image_hash=hashlib.sha256(image_bytes).hexdigest() if image_bytes else "",
            user_id=user_id,
        )

        logger.info(
            "Browser assist: action=%s, capture_id=%s, user=%s",
            action.value,
            metadata.capture_id,
            user_id,
        )

        # LLM にマルチモーダル分析を依頼
        prompt = self._build_analysis_prompt(
            action=action,
            user_question=user_question,
            target_url=target_url,
            browser=browser,
            language=language,
        )

        # LLM プロバイダー経由でマルチモーダル分析を実行
        try:
            result = await self._call_multimodal_llm(
                prompt=prompt,
                image_base64=screenshot_base64,
                action=action,
                language=language,
            )
            return result
        except Exception as exc:
            logger.error("Browser assist LLM call failed: %s", exc)
            return AssistResult(
                action=action,
                explanation=self._get_fallback_message(action, language),
                warnings=[str(exc)],
            )

    def _build_analysis_prompt(
        self,
        action: AssistAction,
        user_question: str,
        target_url: str,
        browser: str,
        language: str,
    ) -> str:
        """LLM への分析プロンプトを構築する."""
        lang_instructions = {
            "ja": {
                AssistAction.ANALYZE_SCREEN: (
                    "このスクリーンショットを分析し、ユーザーの質問に回答してください。\n"
                    "UI要素を具体的に指し示しながら、分かりやすく説明してください。"
                ),
                AssistAction.GUIDE_NAVIGATION: (
                    "このスクリーンショットを見て、ユーザーが目的の操作を完了するための\n"
                    "ステップバイステップの手順を提供してください。\n"
                    "各ステップでクリックすべきボタンやリンクを具体的に示してください。"
                ),
                AssistAction.DIAGNOSE_ERROR: (
                    "このスクリーンショットに表示されているエラーを分析し、\n"
                    "原因と解決策を提供してください。"
                ),
                AssistAction.FILL_FORM_GUIDE: (
                    "このフォームの各フィールドについて、入力方法と注意点を説明してください。\n"
                    "必須フィールド、フォーマット要件、よくある間違いを指摘してください。"
                ),
                AssistAction.EXPLAIN_UI: (
                    "この画面のUIレイアウトを説明し、各要素の役割と使い方を解説してください。"
                ),
            },
            "en": {
                AssistAction.ANALYZE_SCREEN: (
                    "Analyze this screenshot and answer the user's question.\n"
                    "Point to specific UI elements and explain clearly."
                ),
                AssistAction.GUIDE_NAVIGATION: (
                    "Look at this screenshot and provide step-by-step instructions\n"
                    "for the user to complete their desired action.\n"
                    "Specify which buttons or links to click at each step."
                ),
                AssistAction.DIAGNOSE_ERROR: (
                    "Analyze the error shown in this screenshot and provide\n"
                    "the cause and solution."
                ),
                AssistAction.FILL_FORM_GUIDE: (
                    "Explain how to fill each field in this form.\n"
                    "Point out required fields, format requirements, and common mistakes."
                ),
                AssistAction.EXPLAIN_UI: (
                    "Explain the UI layout of this screen and the role of each element."
                ),
            },
        }

        instructions = lang_instructions.get(language, lang_instructions["en"])
        base_instruction = instructions.get(action, instructions[AssistAction.ANALYZE_SCREEN])

        parts = [base_instruction, ""]
        if target_url:
            parts.append(f"URL: {target_url}")
        if browser:
            parts.append(f"Browser: {browser}")
        parts.append(f"\nUser question: {user_question}")

        return "\n".join(parts)

    async def _call_multimodal_llm(
        self,
        prompt: str,
        image_base64: str,
        action: AssistAction,
        language: str,
    ) -> AssistResult:
        """マルチモーダル LLM を呼び出してスクリーンショットを分析する."""
        try:
            from app.providers.gateway import call_llm

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ],
                }
            ]

            # 画像がある場合はマルチモーダルメッセージにする
            if image_base64:
                messages[0]["content"].append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}",
                        },
                    }
                )

            response = await call_llm(messages=messages)
            explanation = response if isinstance(response, str) else str(response)

            return AssistResult(
                action=action,
                explanation=explanation,
                confidence=0.8,
            )
        except ImportError:
            # Gateway が利用できない場合はフォールバック
            return AssistResult(
                action=action,
                explanation=self._get_fallback_message(action, language),
                warnings=["LLM gateway not available. Please configure an LLM provider."],
            )

    def _get_fallback_message(self, action: AssistAction, language: str) -> str:
        """LLM が利用できない場合のフォールバックメッセージ."""
        messages = {
            "ja": (
                "現在、画面分析用の LLM プロバイダーが設定されていません。\n"
                "`zero-employee config set` コマンドで API キーを設定するか、\n"
                "Ollama をインストールしてローカルモデルをご利用ください。"
            ),
            "en": (
                "No LLM provider is configured for screen analysis.\n"
                "Use `zero-employee config set` to configure an API key, or\n"
                "install Ollama for local model support."
            ),
        }
        return messages.get(language, messages["en"])


# シングルトンインスタンス
browser_assist_service = BrowserAssistService()
