"""AI ツール統合 — このシステムから AI が操作可能な外部ツール一覧と管理.

ブラウザアシスト、メディア生成に加え、AI が操作可能な各種ツールを
統合管理する。

対応ツールカテゴリ:
1. コード関連: GitHub, GitLab, Bitbucket, コードレビュー
2. ドキュメント: Google Docs, Notion, Confluence, Obsidian
3. コミュニケーション: Slack, Discord, LINE, Email
4. プロジェクト管理: Jira, Linear, Asana, Trello
5. デザイン: Figma (MCP 経由)
6. データ分析: Google Sheets, Airtable
7. クラウド: AWS, GCP, Azure (CLI 経由)
8. 検索: Web Search, RAG, Knowledge Base
9. メディア生成: 画像・動画・音声 (media_generation.py)
10. ブラウザ操作: Browser Assist, Playwright

すべてのツール操作は:
- 承認ゲート経由
- 監査ログ記録
- データ保護ポリシー適用
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """ツールカテゴリ."""

    CODE = "code"
    DOCUMENT = "document"
    COMMUNICATION = "communication"
    PROJECT_MANAGEMENT = "project_management"
    DESIGN = "design"
    DATA = "data"
    CLOUD = "cloud"
    SEARCH = "search"
    MEDIA_GENERATION = "media_generation"
    BROWSER = "browser"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    AI_MODEL = "ai_model"


class ToolStatus(str, Enum):
    """ツールの状態."""

    AVAILABLE = "available"
    CONFIGURED = "configured"
    NOT_CONFIGURED = "not_configured"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class AIToolDefinition:
    """AI ツール定義."""

    id: str
    name: str
    category: ToolCategory
    description: str
    description_en: str
    status: ToolStatus = ToolStatus.NOT_CONFIGURED
    requires_api_key: bool = False
    env_key: str = ""
    requires_approval: bool = True
    capabilities: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)


# 全ツール定義
_AI_TOOLS: list[AIToolDefinition] = [
    # --- コード関連 ---
    AIToolDefinition(
        id="github",
        name="GitHub",
        category=ToolCategory.CODE,
        description="GitHub リポジトリ・Issue・PR の操作",
        description_en="GitHub repository, issue, and PR operations",
        requires_api_key=True,
        env_key="GITHUB_TOKEN",
        capabilities=["create_issue", "create_pr", "review_code", "manage_releases"],
    ),
    AIToolDefinition(
        id="gitlab",
        name="GitLab",
        category=ToolCategory.CODE,
        description="GitLab リポジトリ・MR の操作",
        description_en="GitLab repository and merge request operations",
        requires_api_key=True,
        env_key="GITLAB_TOKEN",
        capabilities=["create_issue", "create_mr", "review_code"],
    ),
    # --- ドキュメント ---
    AIToolDefinition(
        id="google_docs",
        name="Google Docs",
        category=ToolCategory.DOCUMENT,
        description="Google Docs の作成・編集",
        description_en="Create and edit Google Docs",
        requires_api_key=True,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["create_doc", "edit_doc", "share_doc"],
    ),
    AIToolDefinition(
        id="notion",
        name="Notion",
        category=ToolCategory.DOCUMENT,
        description="Notion ページ・データベースの操作",
        description_en="Notion page and database operations",
        requires_api_key=True,
        env_key="NOTION_API_KEY",
        capabilities=["create_page", "update_page", "query_database"],
    ),
    AIToolDefinition(
        id="obsidian",
        name="Obsidian",
        category=ToolCategory.DOCUMENT,
        description="Obsidian Vault との双方向同期",
        description_en="Bidirectional sync with Obsidian Vault",
        requires_api_key=False,
        capabilities=["import_notes", "export_notes", "link_notes"],
    ),
    # --- コミュニケーション ---
    AIToolDefinition(
        id="slack",
        name="Slack",
        category=ToolCategory.COMMUNICATION,
        description="Slack メッセージの送受信",
        description_en="Send and receive Slack messages",
        requires_api_key=True,
        env_key="SLACK_BOT_TOKEN",
        requires_approval=True,
        capabilities=["send_message", "read_channel", "manage_threads"],
    ),
    AIToolDefinition(
        id="discord",
        name="Discord",
        category=ToolCategory.COMMUNICATION,
        description="Discord メッセージの送受信",
        description_en="Send and receive Discord messages",
        requires_api_key=True,
        env_key="DISCORD_BOT_TOKEN",
        requires_approval=True,
        capabilities=["send_message", "read_channel"],
    ),
    AIToolDefinition(
        id="line",
        name="LINE",
        category=ToolCategory.COMMUNICATION,
        description="LINE メッセージの送受信",
        description_en="Send and receive LINE messages",
        requires_api_key=True,
        env_key="LINE_CHANNEL_TOKEN",
        requires_approval=True,
        capabilities=["send_message", "rich_menu"],
    ),
    AIToolDefinition(
        id="email",
        name="Email (SMTP)",
        category=ToolCategory.COMMUNICATION,
        description="メール送信",
        description_en="Send emails via SMTP",
        requires_api_key=True,
        env_key="SMTP_PASSWORD",
        requires_approval=True,
        capabilities=["send_email"],
    ),
    # --- プロジェクト管理 ---
    AIToolDefinition(
        id="jira",
        name="Jira",
        category=ToolCategory.PROJECT_MANAGEMENT,
        description="Jira チケットの作成・更新",
        description_en="Create and update Jira tickets",
        requires_api_key=True,
        env_key="JIRA_API_TOKEN",
        capabilities=["create_issue", "update_issue", "transition_issue"],
    ),
    AIToolDefinition(
        id="linear",
        name="Linear",
        category=ToolCategory.PROJECT_MANAGEMENT,
        description="Linear Issue の操作",
        description_en="Linear issue operations",
        requires_api_key=True,
        env_key="LINEAR_API_KEY",
        capabilities=["create_issue", "update_issue"],
    ),
    # --- デザイン ---
    AIToolDefinition(
        id="figma",
        name="Figma",
        category=ToolCategory.DESIGN,
        description="Figma デザインの取得・分析（MCP 経由）",
        description_en="Get and analyze Figma designs via MCP",
        requires_api_key=True,
        env_key="FIGMA_ACCESS_TOKEN",
        capabilities=["get_design", "get_screenshot", "code_connect"],
    ),
    # --- データ ---
    AIToolDefinition(
        id="google_sheets",
        name="Google Sheets",
        category=ToolCategory.DATA,
        description="Google Sheets の読み書き",
        description_en="Read and write Google Sheets",
        requires_api_key=True,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["read_sheet", "write_sheet", "create_sheet"],
    ),
    # --- クラウド ---
    AIToolDefinition(
        id="aws_cli",
        name="AWS CLI",
        category=ToolCategory.CLOUD,
        description="AWS サービスの操作",
        description_en="AWS service operations via CLI",
        requires_api_key=True,
        env_key="AWS_ACCESS_KEY_ID",
        requires_approval=True,
        capabilities=["s3", "lambda", "ec2", "iam"],
    ),
    AIToolDefinition(
        id="gcloud",
        name="Google Cloud CLI",
        category=ToolCategory.CLOUD,
        description="GCP サービスの操作",
        description_en="GCP service operations via CLI",
        requires_api_key=True,
        env_key="GOOGLE_APPLICATION_CREDENTIALS",
        requires_approval=True,
        capabilities=["compute", "storage", "functions"],
    ),
    # --- 検索 ---
    AIToolDefinition(
        id="web_search",
        name="Web Search",
        category=ToolCategory.SEARCH,
        description="ウェブ検索（Google, Bing, DuckDuckGo）",
        description_en="Web search via Google, Bing, or DuckDuckGo",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["search", "scrape"],
    ),
    AIToolDefinition(
        id="local_rag",
        name="Local RAG",
        category=ToolCategory.SEARCH,
        description="ローカルファイルの RAG 検索",
        description_en="Local file RAG search",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["index", "search", "similarity"],
    ),
    # --- メディア生成 ---
    AIToolDefinition(
        id="image_generation",
        name="Image Generation",
        category=ToolCategory.MEDIA_GENERATION,
        description="画像生成（DALL-E, Stable Diffusion, Flux）",
        description_en="Image generation via DALL-E, Stable Diffusion, Flux",
        requires_api_key=True,
        env_key="OPENAI_API_KEY",
        requires_approval=True,
        capabilities=["generate_image", "edit_image", "variation"],
    ),
    AIToolDefinition(
        id="video_generation",
        name="Video Generation",
        category=ToolCategory.MEDIA_GENERATION,
        description="動画生成（Runway ML, Pika, Replicate）",
        description_en="Video generation via Runway ML, Pika, Replicate",
        requires_api_key=True,
        env_key="RUNWAY_API_KEY",
        requires_approval=True,
        capabilities=["generate_video", "img2video"],
    ),
    AIToolDefinition(
        id="audio_generation",
        name="Audio/TTS Generation",
        category=ToolCategory.MEDIA_GENERATION,
        description="音声・TTS 生成（OpenAI TTS, ElevenLabs）",
        description_en="Audio/TTS generation via OpenAI TTS, ElevenLabs",
        requires_api_key=True,
        env_key="OPENAI_API_KEY",
        requires_approval=True,
        capabilities=["text_to_speech", "voice_clone"],
    ),
    AIToolDefinition(
        id="music_generation",
        name="Music Generation",
        category=ToolCategory.MEDIA_GENERATION,
        description="音楽生成（Suno, Udio）",
        description_en="Music generation via Suno, Udio",
        requires_api_key=True,
        env_key="SUNO_API_KEY",
        requires_approval=True,
        capabilities=["generate_music", "extend_music"],
    ),
    # --- ブラウザ ---
    AIToolDefinition(
        id="browser_assist",
        name="Browser Assist",
        category=ToolCategory.BROWSER,
        description="ブラウザ画面の分析・操作案内",
        description_en="Browser screen analysis and operation guidance",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["analyze_screen", "guide_navigation", "diagnose_error"],
    ),
    AIToolDefinition(
        id="playwright",
        name="Playwright (Browser Automation)",
        category=ToolCategory.BROWSER,
        description="ブラウザ自動操作（スクレイピング・テスト）",
        description_en="Browser automation via Playwright",
        requires_api_key=False,
        requires_approval=True,
        capabilities=["navigate", "click", "fill_form", "screenshot", "scrape"],
    ),
    # --- ファイルシステム ---
    AIToolDefinition(
        id="file_system",
        name="File System",
        category=ToolCategory.FILE_SYSTEM,
        description="ファイルの読み書き（サンドボックス内）",
        description_en="File read/write within sandbox",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["read", "write", "list", "search"],
    ),
    # --- データベース ---
    AIToolDefinition(
        id="database",
        name="Database (Read-only)",
        category=ToolCategory.DATABASE,
        description="データベースの読み取り専用アクセス",
        description_en="Read-only database access",
        requires_api_key=False,
        requires_approval=False,
        capabilities=["query", "search"],
    ),
]


class AIToolRegistry:
    """AI ツールレジストリ.

    利用可能なツールの管理と状態確認を行う。
    """

    def __init__(self) -> None:
        self._tools: dict[str, AIToolDefinition] = {t.id: t for t in _AI_TOOLS}
        self._disabled_tools: set[str] = set()

    def get_all_tools(self) -> list[AIToolDefinition]:
        """全ツール一覧を返す."""
        return list(self._tools.values())

    def get_tool(self, tool_id: str) -> AIToolDefinition | None:
        """ツールを取得する."""
        return self._tools.get(tool_id)

    def get_tools_by_category(self, category: ToolCategory) -> list[AIToolDefinition]:
        """カテゴリ別のツール一覧を返す."""
        return [t for t in self._tools.values() if t.category == category]

    def get_available_tools(self) -> list[AIToolDefinition]:
        """利用可能な（設定済みの）ツール一覧を返す."""
        import os

        available = []
        for tool in self._tools.values():
            if tool.id in self._disabled_tools:
                continue
            if tool.requires_api_key:
                if os.environ.get(tool.env_key):
                    tool.status = ToolStatus.CONFIGURED
                    available.append(tool)
                else:
                    tool.status = ToolStatus.NOT_CONFIGURED
            else:
                tool.status = ToolStatus.AVAILABLE
                available.append(tool)
        return available

    def disable_tool(self, tool_id: str) -> bool:
        """ツールを無効化する."""
        if tool_id in self._tools:
            self._disabled_tools.add(tool_id)
            self._tools[tool_id].status = ToolStatus.DISABLED
            logger.info("AI tool disabled: %s", tool_id)
            return True
        return False

    def enable_tool(self, tool_id: str) -> bool:
        """ツールを有効化する."""
        self._disabled_tools.discard(tool_id)
        if tool_id in self._tools:
            self._tools[tool_id].status = ToolStatus.NOT_CONFIGURED
            logger.info("AI tool enabled: %s", tool_id)
            return True
        return False

    def get_summary(self) -> dict:
        """ツール概要を返す."""
        all_tools = self.get_all_tools()
        available = self.get_available_tools()
        return {
            "total": len(all_tools),
            "available": len(available),
            "disabled": len(self._disabled_tools),
            "categories": {cat.value: len(self.get_tools_by_category(cat)) for cat in ToolCategory},
        }


# グローバルインスタンス
ai_tool_registry = AIToolRegistry()
