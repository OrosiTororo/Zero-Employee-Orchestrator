"""Natural language command API — unified NL control endpoint for GUI / CLI / TUI.

Receives natural language input from users, executes appropriate actions, and returns results.
Accessible from the frontend chat UI, CLI local mode, and TUI in a unified manner.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection

logger = logging.getLogger(__name__)

router = APIRouter()


class NLCommandRequest(BaseModel):
    text: str = Field(..., description="Natural language command text")
    language: str = Field(default="ja", description="Language code (ja/en/zh)")
    context: dict = Field(default_factory=dict, description="Additional context")


class NLCommandResponse(BaseModel):
    success: bool
    message: str
    category: str = ""
    action: str = ""
    confidence: float = 0.0
    data: dict = Field(default_factory=dict)
    suggestions: list[str] = Field(default_factory=list)
    delegate_to_llm: bool = False


@router.post("/command", response_model=NLCommandResponse)
@limiter.limit("30/minute")
async def execute_nl_command(
    request: Request, req: NLCommandRequest, user: User = Depends(get_current_user)
):
    """Execute a natural language command.

    Parses user natural language input and automatically executes operations such as
    configuration changes, ticket creation, and model management. Delegates to LLM
    if the input is not recognized as a command.

    Accessible from GUI chat bar, CLI interactive mode, and TUI.
    """
    # Prompt injection check
    guard_result = scan_prompt_injection(req.text)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected.",
        )

    # PII detection and masking
    pii_result = detect_and_mask_pii(req.text)
    if pii_result.detected_count > 0:
        logger.warning(
            "PII detected in NL command: types=%s, count=%d",
            pii_result.detected_types,
            pii_result.detected_count,
        )
    safe_text = pii_result.masked_text

    from app.services.nl_command_service import nl_command_processor

    parsed = nl_command_processor.parse(safe_text)
    result = await nl_command_processor.execute(parsed)

    return NLCommandResponse(
        success=result.success,
        message=result.message,
        category=parsed.category.value,
        action=parsed.action.value,
        confidence=parsed.confidence,
        data=result.data,
        suggestions=result.suggestions,
        delegate_to_llm=result.data.get("delegate_to_llm", False),
    )


@router.get("/command/capabilities")
async def list_capabilities(user: User = Depends(get_current_user)):
    """List available natural language command capabilities.

    Returns information for display in GUI / CLI / TUI help screens.
    """
    return {
        "categories": [
            {
                "id": "config",
                "name": {"ja": "設定変更", "en": "Configuration", "zh": "配置变更"},
                "examples": {
                    "ja": [
                        "Geminiを使うように設定して",
                        "実行モードをfreeに変更して",
                        "言語を英語に変更して",
                        "設定を見せて",
                    ],
                    "en": [
                        "Set up to use Gemini",
                        "Change execution mode to free",
                        "Change language to Japanese",
                        "Show settings",
                    ],
                    "zh": [
                        "设置使用Gemini",
                        "将执行模式更改为free",
                        "将语言更改为日语",
                        "显示设置",
                    ],
                },
            },
            {
                "id": "ticket",
                "name": {"ja": "業務依頼", "en": "Task Requests", "zh": "任务请求"},
                "examples": {
                    "ja": ["競合分析レポートを作成して", "チケット一覧を見せて"],
                    "en": ["Create a competitive analysis report", "Show ticket list"],
                    "zh": ["创建竞争分析报告", "显示工单列表"],
                },
            },
            {
                "id": "model",
                "name": {"ja": "モデル管理", "en": "Model Management", "zh": "模型管理"},
                "examples": {
                    "ja": [
                        "利用可能なモデルを見せて",
                        "モデルを更新して",
                        "qwen3:8bをダウンロードして",
                    ],
                    "en": [
                        "Show available models",
                        "Update models",
                        "Download qwen3:8b",
                    ],
                    "zh": ["显示可用模型", "更新模型", "下载qwen3:8b"],
                },
            },
            {
                "id": "skill",
                "name": {"ja": "スキル・プラグイン", "en": "Skills & Plugins", "zh": "技能与插件"},
                "examples": {
                    "ja": [
                        "スキル一覧を見せて",
                        "browser-useを追加して",
                        "Webスクレイピングスキルを生成して",
                    ],
                    "en": [
                        "Show skill list",
                        "Add browser-use",
                        "Generate a web scraping skill",
                    ],
                    "zh": ["显示技能列表", "添加browser-use", "生成网页抓取技能"],
                },
            },
            {
                "id": "security",
                "name": {"ja": "セキュリティ", "en": "Security", "zh": "安全"},
                "examples": {
                    "ja": ["セキュリティ設定を確認して", "サンドボックスをmoderateに変更して"],
                    "en": ["Check security settings", "Change sandbox to moderate"],
                    "zh": ["检查安全设置", "将沙箱更改为moderate"],
                },
            },
            {
                "id": "approval",
                "name": {"ja": "承認管理", "en": "Approvals", "zh": "审批管理"},
                "examples": {
                    "ja": ["承認待ちを見せて"],
                    "en": ["Show pending approvals"],
                    "zh": ["显示待审批项"],
                },
            },
            {
                "id": "media",
                "name": {"ja": "メディア生成", "en": "Media Generation", "zh": "媒体生成"},
                "examples": {
                    "ja": ["オフィスの画像を生成して"],
                    "en": ["Generate an office image"],
                    "zh": ["生成办公室图片"],
                },
            },
            {
                "id": "system",
                "name": {"ja": "システム", "en": "System", "zh": "系统"},
                "examples": {
                    "ja": ["ヘルスチェックして", "何ができるか教えて"],
                    "en": ["Run health check", "What can you do?"],
                    "zh": ["运行健康检查", "你能做什么？"],
                },
            },
        ],
    }
