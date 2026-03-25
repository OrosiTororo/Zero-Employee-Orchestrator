"""自然言語コマンド API — GUI / CLI / TUI 共通の自然言語制御エンドポイント.

ユーザーの自然言語入力を受け取り、適切なアクションを実行して結果を返す。
フロントエンドのチャット UI、CLI のローカルモード、TUI から統一的に利用可能。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class NLCommandRequest(BaseModel):
    text: str = Field(..., description="自然言語のコマンドテキスト")
    language: str = Field(default="ja", description="言語コード (ja/en/zh)")
    context: dict = Field(default_factory=dict, description="追加コンテキスト")


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
async def execute_nl_command(req: NLCommandRequest):
    """自然言語コマンドを実行する.

    ユーザーの自然言語入力を解析し、設定変更・チケット作成・モデル管理等の
    操作を自動的に実行する。コマンドとして認識されない場合は LLM に委譲する。

    GUI のチャットバー、CLI の対話モード、TUI から統一的に利用可能。
    """
    from app.services.nl_command_service import nl_command_processor

    # 1. 自然言語を解析
    parsed = nl_command_processor.parse(req.text)

    # 2. コマンドを実行
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
async def list_capabilities():
    """自然言語コマンドで対応可能な操作一覧を返す.

    GUI / CLI / TUI のヘルプ画面で表示するための情報。
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
