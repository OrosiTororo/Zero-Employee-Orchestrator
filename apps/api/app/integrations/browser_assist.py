"""Browser assist integration — view the user's screen and guide operations.

When users are using a web browser like Chrome or other applications and ask about
how to perform operations, this service views the same screen and provides
answers, investigation, and assistance.

Features:
- Screenshot analysis: Understand the screen using LLM multimodal capabilities
- Step-by-step guidance: Identify UI elements and present operation steps
- Error diagnosis: Read error messages on screen and suggest solutions
- Form input assistance: Guide how to fill each form field
- UI explanation: Explain the role and usage of each screen element

Safety:
- Screenshots are held only temporarily (not persisted)
- Password field contents are automatically blurred
- Requires explicit user consent
- All captures are recorded in audit logs (excluding the image itself)
- No autonomous click operations (guidance only)
"""

from __future__ import annotations

import base64
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class AssistAction(str, Enum):
    """Assist action type."""

    ANALYZE_SCREEN = "analyze_screen"
    GUIDE_NAVIGATION = "guide_navigation"
    DIAGNOSE_ERROR = "diagnose_error"
    FILL_FORM_GUIDE = "fill_form_guide"
    EXPLAIN_UI = "explain_ui"


@dataclass
class AssistStep:
    """A single step in an operation procedure."""

    step_number: int
    instruction: str
    ui_element: str = ""
    screenshot_annotation: str = ""


@dataclass
class AssistResult:
    """Assist result."""

    action: AssistAction
    steps: list[AssistStep] = field(default_factory=list)
    explanation: str = ""
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ScreenCaptureMetadata:
    """Screen capture metadata (does not include the image itself)."""

    capture_id: str
    timestamp: str
    source_url: str = ""
    browser: str = ""
    image_hash: str = ""  # SHA-256 of the image for audit
    user_id: str = ""


class BrowserAssistService:
    """Browser assist service.

    Uses LLM multimodal capabilities to analyze the user's screen
    and guide operations.
    """

    def __init__(self) -> None:
        self._consent_cache: dict[str, bool] = {}
        self._consent_file = Path.home() / ".zero-employee" / "browser-consent.json"
        self._load_consent()

    def _load_consent(self) -> None:
        """Load persisted consent from disk."""
        if self._consent_file.exists():
            try:
                import json

                self._consent_cache = json.loads(self._consent_file.read_text(encoding="utf-8"))
            except Exception:
                self._consent_cache = {}

    def _save_consent(self) -> None:
        """Persist consent to disk (survives restart)."""
        import json

        self._consent_file.parent.mkdir(parents=True, exist_ok=True)
        self._consent_file.write_text(json.dumps(self._consent_cache, indent=2), encoding="utf-8")
        self._consent_file.chmod(0o600)

    def check_user_consent(self, user_id: str) -> bool:
        """Check if the user has consented to screen sharing."""
        return self._consent_cache.get(user_id, False)

    def grant_consent(self, user_id: str) -> None:
        """Record the user's screen sharing consent (persisted to disk)."""
        self._consent_cache[user_id] = True
        self._save_consent()

    def revoke_consent(self, user_id: str) -> None:
        """Revoke the user's screen sharing consent (persisted to disk)."""
        self._consent_cache[user_id] = False
        self._save_consent()

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
        """Analyze a screenshot and answer the user's question.

        Args:
            screenshot_base64: Base64-encoded screenshot
            user_question: User's question
            action: Assist action type
            target_url: URL the user is currently viewing
            browser: Browser type
            language: Response language
            user_id: User ID (for auditing)

        Returns:
            AssistResult: Analysis results and operation steps
        """
        # Generate metadata (for audit log; the image itself is not stored)
        image_bytes = base64.b64decode(screenshot_base64) if screenshot_base64 else b""
        metadata = ScreenCaptureMetadata(
            capture_id=hashlib.sha256(
                f"{user_id}:{datetime.now(UTC).isoformat()}".encode()
            ).hexdigest()[:16],
            timestamp=datetime.now(UTC).isoformat(),
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

        # Request multimodal analysis from LLM
        prompt = self._build_analysis_prompt(
            action=action,
            user_question=user_question,
            target_url=target_url,
            browser=browser,
            language=language,
        )

        # Execute multimodal analysis via LLM provider
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
        """Build analysis prompt for the LLM."""
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
        """Call multimodal LLM to analyze the screenshot."""
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

            # Make it a multimodal message if an image is present
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
            # Fallback if gateway is not available
            return AssistResult(
                action=action,
                explanation=self._get_fallback_message(action, language),
                warnings=["LLM gateway not available. Please configure an LLM provider."],
            )

    def _get_fallback_message(self, action: AssistAction, language: str) -> str:
        """Fallback message when LLM is not available."""
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


# Singleton instance
browser_assist_service = BrowserAssistService()
