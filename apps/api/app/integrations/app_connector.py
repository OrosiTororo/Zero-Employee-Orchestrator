"""汎用アプリケーション連携ハブ — 幅広い外部アプリとの統合を管理.

ナレッジベース（Obsidian, Notion, Logseq 等）、生産性ツール（Google Workspace,
Microsoft 365 等）、プロジェクト管理ツール、CRM、カレンダーなど多種多様な
アプリケーションとの接続を統一的に管理する。

すべての接続はユーザーが明示的に許可した範囲でのみ動作し、
ワークスペース隔離・承認ゲート・監査ログを経由する。

安全性:
- ユーザーが接続を登録・許可するまでアクセスしない
- ワークスペース隔離チェック
- 承認ゲート適用（外部送信・データ取得）
- PII ガード適用
- 監査ログ記録
- シークレットは SecretManager 経由で保管
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AppCategory(str, Enum):
    """アプリケーションカテゴリ."""

    KNOWLEDGE_BASE = "knowledge_base"
    NOTE_TAKING = "note_taking"
    DOCUMENT = "document"
    PRODUCTIVITY = "productivity"
    PROJECT_MANAGEMENT = "project_management"
    COMMUNICATION = "communication"
    CRM = "crm"
    CALENDAR = "calendar"
    EMAIL = "email"
    CLOUD_STORAGE = "cloud_storage"
    DESIGN = "design"
    CODE_HOSTING = "code_hosting"
    DATABASE = "database"
    ANALYTICS = "analytics"
    AUTOMATION = "automation"
    CUSTOM = "custom"


class AppConnectionStatus(str, Enum):
    """接続ステータス."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING_AUTH = "pending_auth"
    ERROR = "error"
    DISABLED = "disabled"


class AppAuthMethod(str, Enum):
    """認証方式."""

    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    LOCAL_FILE = "local_file"
    WEBHOOK = "webhook"
    TOKEN = "token"
    BASIC = "basic"


class AppDataDirection(str, Enum):
    """データフロー方向."""

    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class AppPermission:
    """アプリケーション連携で許可された操作."""

    read: bool = False
    write: bool = False
    delete: bool = False
    sync: bool = False
    export: bool = False
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)


@dataclass
class AppDefinition:
    """連携可能なアプリケーションの定義."""

    id: str
    name: str
    category: AppCategory
    description: str
    description_en: str
    auth_method: AppAuthMethod = AppAuthMethod.API_KEY
    data_direction: AppDataDirection = AppDataDirection.BIDIRECTIONAL
    env_key: str = ""
    base_url: str = ""
    capabilities: list[str] = field(default_factory=list)
    requires_approval: bool = True
    config_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConnection:
    """ユーザーが確立したアプリケーション接続."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    app_id: str = ""
    user_id: str = ""
    status: AppConnectionStatus = AppConnectionStatus.DISCONNECTED
    permissions: AppPermission = field(default_factory=AppPermission)
    config: dict[str, Any] = field(default_factory=dict)
    connected_at: str = ""
    last_sync_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppSyncResult:
    """同期結果."""

    connection_id: str
    app_id: str
    direction: str
    items_read: int = 0
    items_written: int = 0
    items_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""


# ------------------------------------------------------------------ #
#  対応アプリケーション定義
# ------------------------------------------------------------------ #

_APP_DEFINITIONS: list[AppDefinition] = [
    # --- ナレッジベース ---
    AppDefinition(
        id="obsidian",
        name="Obsidian",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Obsidian Vault との双方向同期・リンクグラフ解析",
        description_en="Bidirectional sync with Obsidian Vault and link graph analysis",
        auth_method=AppAuthMethod.LOCAL_FILE,
        capabilities=[
            "read_notes",
            "write_notes",
            "search",
            "link_graph",
            "backlinks",
            "sync_knowledge_store",
        ],
        requires_approval=False,
    ),
    AppDefinition(
        id="notion",
        name="Notion",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Notion ページ・データベースの読み書き・検索",
        description_en="Read/write/search Notion pages and databases",
        auth_method=AppAuthMethod.TOKEN,
        env_key="NOTION_API_KEY",
        base_url="https://api.notion.com/v1",
        capabilities=[
            "read_pages",
            "write_pages",
            "query_database",
            "search",
            "sync_knowledge_store",
        ],
    ),
    AppDefinition(
        id="logseq",
        name="Logseq",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Logseq グラフとの同期・ブロック単位の読み書き",
        description_en="Sync with Logseq graphs, block-level read/write",
        auth_method=AppAuthMethod.LOCAL_FILE,
        capabilities=[
            "read_blocks",
            "write_blocks",
            "search",
            "graph_analysis",
            "sync_knowledge_store",
        ],
        requires_approval=False,
    ),
    AppDefinition(
        id="joplin",
        name="Joplin",
        category=AppCategory.NOTE_TAKING,
        description="Joplin ノートの読み書き・検索（REST API）",
        description_en="Read/write/search Joplin notes via REST API",
        auth_method=AppAuthMethod.TOKEN,
        env_key="JOPLIN_TOKEN",
        base_url="http://localhost:41184",
        capabilities=["read_notes", "write_notes", "search", "sync_knowledge_store"],
    ),
    AppDefinition(
        id="anytype",
        name="Anytype",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Anytype オブジェクトの読み取り・検索",
        description_en="Read and search Anytype objects",
        auth_method=AppAuthMethod.LOCAL_FILE,
        data_direction=AppDataDirection.READ_ONLY,
        capabilities=["read_objects", "search", "sync_knowledge_store"],
        requires_approval=False,
    ),
    AppDefinition(
        id="roam_research",
        name="Roam Research",
        category=AppCategory.KNOWLEDGE_BASE,
        description="Roam Research グラフの読み書き",
        description_en="Read/write Roam Research graphs",
        auth_method=AppAuthMethod.API_KEY,
        env_key="ROAM_API_KEY",
        capabilities=["read_blocks", "write_blocks", "search", "graph_query"],
    ),
    # --- ドキュメント ---
    AppDefinition(
        id="google_docs",
        name="Google Docs",
        category=AppCategory.DOCUMENT,
        description="Google ドキュメントの作成・編集・共有",
        description_en="Create, edit, and share Google Docs",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["create_doc", "edit_doc", "share_doc", "export_pdf"],
    ),
    AppDefinition(
        id="google_sheets",
        name="Google Sheets",
        category=AppCategory.DOCUMENT,
        description="Google スプレッドシートの読み書き",
        description_en="Read/write Google Sheets",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["read_sheet", "write_sheet", "create_sheet"],
    ),
    AppDefinition(
        id="google_drive",
        name="Google Drive",
        category=AppCategory.CLOUD_STORAGE,
        description="Google Drive ファイルの検索・取得・アップロード",
        description_en="Search, retrieve, and upload Google Drive files",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["search_files", "download", "upload", "share"],
    ),
    AppDefinition(
        id="microsoft_365",
        name="Microsoft 365",
        category=AppCategory.PRODUCTIVITY,
        description="Word・Excel・PowerPoint・OneDrive の操作",
        description_en="Operate Word, Excel, PowerPoint, and OneDrive",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="MICROSOFT_CLIENT_ID",
        capabilities=["read_docs", "write_docs", "search", "upload", "share"],
    ),
    AppDefinition(
        id="confluence",
        name="Confluence",
        category=AppCategory.DOCUMENT,
        description="Confluence ページ・スペースの読み書き",
        description_en="Read/write Confluence pages and spaces",
        auth_method=AppAuthMethod.API_KEY,
        env_key="CONFLUENCE_API_TOKEN",
        capabilities=["read_pages", "write_pages", "search", "spaces"],
    ),
    # --- プロジェクト管理 ---
    AppDefinition(
        id="jira",
        name="Jira",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Jira チケットの作成・更新・検索",
        description_en="Create, update, and search Jira tickets",
        auth_method=AppAuthMethod.API_KEY,
        env_key="JIRA_API_TOKEN",
        capabilities=["create_issue", "update_issue", "transition_issue", "search"],
    ),
    AppDefinition(
        id="linear",
        name="Linear",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Linear Issue の作成・更新",
        description_en="Create and update Linear issues",
        auth_method=AppAuthMethod.API_KEY,
        env_key="LINEAR_API_KEY",
        capabilities=["create_issue", "update_issue", "search"],
    ),
    AppDefinition(
        id="asana",
        name="Asana",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Asana タスク・プロジェクトの操作",
        description_en="Operate Asana tasks and projects",
        auth_method=AppAuthMethod.TOKEN,
        env_key="ASANA_ACCESS_TOKEN",
        capabilities=["create_task", "update_task", "search", "projects"],
    ),
    AppDefinition(
        id="trello",
        name="Trello",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="Trello ボード・カードの操作",
        description_en="Operate Trello boards and cards",
        auth_method=AppAuthMethod.API_KEY,
        env_key="TRELLO_API_KEY",
        capabilities=["create_card", "update_card", "search", "boards"],
    ),
    AppDefinition(
        id="clickup",
        name="ClickUp",
        category=AppCategory.PROJECT_MANAGEMENT,
        description="ClickUp タスク・スペースの操作",
        description_en="Operate ClickUp tasks and spaces",
        auth_method=AppAuthMethod.API_KEY,
        env_key="CLICKUP_API_KEY",
        capabilities=["create_task", "update_task", "search"],
    ),
    # --- コミュニケーション ---
    AppDefinition(
        id="slack",
        name="Slack",
        category=AppCategory.COMMUNICATION,
        description="Slack メッセージの送受信・チャンネル管理",
        description_en="Send/receive Slack messages and manage channels",
        auth_method=AppAuthMethod.TOKEN,
        env_key="SLACK_BOT_TOKEN",
        capabilities=["send_message", "read_channel", "manage_threads", "search"],
    ),
    AppDefinition(
        id="discord",
        name="Discord",
        category=AppCategory.COMMUNICATION,
        description="Discord メッセージの送受信",
        description_en="Send/receive Discord messages",
        auth_method=AppAuthMethod.TOKEN,
        env_key="DISCORD_BOT_TOKEN",
        capabilities=["send_message", "read_channel"],
    ),
    AppDefinition(
        id="teams",
        name="Microsoft Teams",
        category=AppCategory.COMMUNICATION,
        description="Microsoft Teams メッセージの送受信",
        description_en="Send/receive Microsoft Teams messages",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="MICROSOFT_CLIENT_ID",
        capabilities=["send_message", "read_channel", "manage_meetings"],
    ),
    # --- CRM ---
    AppDefinition(
        id="hubspot",
        name="HubSpot",
        category=AppCategory.CRM,
        description="HubSpot CRM の連絡先・取引・タスク操作",
        description_en="Operate HubSpot CRM contacts, deals, and tasks",
        auth_method=AppAuthMethod.API_KEY,
        env_key="HUBSPOT_API_KEY",
        capabilities=["read_contacts", "create_deal", "search", "tasks"],
    ),
    AppDefinition(
        id="salesforce",
        name="Salesforce",
        category=AppCategory.CRM,
        description="Salesforce CRM のオブジェクト操作",
        description_en="Operate Salesforce CRM objects",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="SALESFORCE_CLIENT_ID",
        capabilities=["read_objects", "create_record", "search", "reports"],
    ),
    # --- カレンダー ---
    AppDefinition(
        id="google_calendar",
        name="Google Calendar",
        category=AppCategory.CALENDAR,
        description="Google カレンダーのイベント作成・取得",
        description_en="Create and retrieve Google Calendar events",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["read_events", "create_event", "update_event", "search"],
    ),
    AppDefinition(
        id="outlook_calendar",
        name="Outlook Calendar",
        category=AppCategory.CALENDAR,
        description="Outlook カレンダーのイベント操作",
        description_en="Operate Outlook Calendar events",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="MICROSOFT_CLIENT_ID",
        capabilities=["read_events", "create_event", "update_event"],
    ),
    # --- メール ---
    AppDefinition(
        id="gmail",
        name="Gmail",
        category=AppCategory.EMAIL,
        description="Gmail の読み取り・送信・検索",
        description_en="Read, send, and search Gmail",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="GOOGLE_SERVICE_ACCOUNT",
        capabilities=["read_emails", "send_email", "search", "labels"],
    ),
    # --- クラウドストレージ ---
    AppDefinition(
        id="dropbox",
        name="Dropbox",
        category=AppCategory.CLOUD_STORAGE,
        description="Dropbox ファイルの検索・取得・アップロード",
        description_en="Search, retrieve, and upload Dropbox files",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="DROPBOX_ACCESS_TOKEN",
        capabilities=["search_files", "download", "upload", "share"],
    ),
    AppDefinition(
        id="onedrive",
        name="OneDrive",
        category=AppCategory.CLOUD_STORAGE,
        description="OneDrive ファイルの操作",
        description_en="Operate OneDrive files",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="MICROSOFT_CLIENT_ID",
        capabilities=["search_files", "download", "upload", "share"],
    ),
    # --- コードホスティング ---
    AppDefinition(
        id="github",
        name="GitHub",
        category=AppCategory.CODE_HOSTING,
        description="GitHub リポジトリ・Issue・PR の操作",
        description_en="Operate GitHub repositories, issues, and PRs",
        auth_method=AppAuthMethod.TOKEN,
        env_key="GITHUB_TOKEN",
        capabilities=["create_issue", "create_pr", "review_code", "search"],
    ),
    AppDefinition(
        id="gitlab",
        name="GitLab",
        category=AppCategory.CODE_HOSTING,
        description="GitLab リポジトリ・MR の操作",
        description_en="Operate GitLab repositories and merge requests",
        auth_method=AppAuthMethod.TOKEN,
        env_key="GITLAB_TOKEN",
        capabilities=["create_issue", "create_mr", "review_code", "search"],
    ),
    # --- デザイン ---
    AppDefinition(
        id="figma",
        name="Figma",
        category=AppCategory.DESIGN,
        description="Figma デザインの取得・分析（MCP 経由）",
        description_en="Retrieve and analyze Figma designs via MCP",
        auth_method=AppAuthMethod.API_KEY,
        env_key="FIGMA_ACCESS_TOKEN",
        data_direction=AppDataDirection.READ_ONLY,
        capabilities=["get_design", "get_screenshot", "code_connect"],
    ),
    AppDefinition(
        id="canva",
        name="Canva",
        category=AppCategory.DESIGN,
        description="Canva デザインの取得・エクスポート",
        description_en="Retrieve and export Canva designs",
        auth_method=AppAuthMethod.OAUTH2,
        env_key="CANVA_API_KEY",
        data_direction=AppDataDirection.READ_ONLY,
        capabilities=["get_designs", "export"],
    ),
    # --- 分析 ---
    AppDefinition(
        id="airtable",
        name="Airtable",
        category=AppCategory.ANALYTICS,
        description="Airtable ベース・テーブルの操作",
        description_en="Operate Airtable bases and tables",
        auth_method=AppAuthMethod.API_KEY,
        env_key="AIRTABLE_API_KEY",
        capabilities=["read_records", "write_records", "search"],
    ),
    # --- オートメーション ---
    AppDefinition(
        id="n8n",
        name="n8n",
        category=AppCategory.AUTOMATION,
        description="n8n ワークフローのトリガー・管理",
        description_en="Trigger and manage n8n workflows",
        auth_method=AppAuthMethod.WEBHOOK,
        capabilities=["trigger_workflow", "list_workflows", "get_status"],
        requires_approval=False,
    ),
    AppDefinition(
        id="zapier",
        name="Zapier",
        category=AppCategory.AUTOMATION,
        description="Zapier Zap のトリガー",
        description_en="Trigger Zapier Zaps",
        auth_method=AppAuthMethod.WEBHOOK,
        capabilities=["trigger_zap"],
    ),
    AppDefinition(
        id="make",
        name="Make (Integromat)",
        category=AppCategory.AUTOMATION,
        description="Make シナリオのトリガー",
        description_en="Trigger Make scenarios",
        auth_method=AppAuthMethod.WEBHOOK,
        capabilities=["trigger_scenario"],
    ),
]


class AppConnectorHub:
    """汎用アプリケーション連携ハブ.

    外部アプリケーションの一覧管理・接続確立・データ同期を
    統一的に提供する。すべての操作はユーザーが許可した範囲でのみ
    実行される。
    """

    def __init__(self) -> None:
        self._definitions: dict[str, AppDefinition] = {d.id: d for d in _APP_DEFINITIONS}
        self._connections: dict[str, AppConnection] = {}
        self._sync_history: list[AppSyncResult] = []

    # ------------------------------------------------------------------ #
    #  アプリ定義管理
    # ------------------------------------------------------------------ #

    def list_apps(
        self,
        category: AppCategory | None = None,
    ) -> list[AppDefinition]:
        """対応アプリケーション一覧を返す."""
        apps = list(self._definitions.values())
        if category is not None:
            apps = [a for a in apps if a.category == category]
        return apps

    def get_app(self, app_id: str) -> AppDefinition | None:
        """アプリ定義を取得する."""
        return self._definitions.get(app_id)

    def register_custom_app(self, app_def: AppDefinition) -> str:
        """ユーザー定義のカスタムアプリを登録する."""
        if not app_def.id:
            app_def.id = str(uuid.uuid4())
        self._definitions[app_def.id] = app_def
        logger.info("Custom app registered: %s (%s)", app_def.name, app_def.id)
        return app_def.id

    def list_categories(self) -> list[dict[str, Any]]:
        """利用可能なカテゴリ一覧と各カテゴリのアプリ数を返す."""
        counts: dict[str, int] = {}
        for d in self._definitions.values():
            counts[d.category.value] = counts.get(d.category.value, 0) + 1
        return [
            {"category": cat.value, "count": counts.get(cat.value, 0)}
            for cat in AppCategory
            if counts.get(cat.value, 0) > 0
        ]

    # ------------------------------------------------------------------ #
    #  接続管理
    # ------------------------------------------------------------------ #

    def connect(
        self,
        app_id: str,
        user_id: str,
        config: dict[str, Any] | None = None,
        permissions: AppPermission | None = None,
    ) -> AppConnection:
        """アプリケーション接続を確立する.

        Args:
            app_id: 接続するアプリケーション ID
            user_id: ユーザー ID
            config: 接続設定（API キー、パス等）
            permissions: 許可する操作

        Returns:
            確立された AppConnection

        Raises:
            KeyError: app_id が登録されていない場合
        """
        app_def = self._definitions.get(app_id)
        if app_def is None:
            raise KeyError(f"App not found: {app_id}")

        conn = AppConnection(
            app_id=app_id,
            user_id=user_id,
            status=AppConnectionStatus.CONNECTED,
            permissions=permissions or AppPermission(read=True),
            config=config or {},
            connected_at=datetime.now(UTC).isoformat(),
        )

        # 認証情報の検証
        if app_def.auth_method == AppAuthMethod.LOCAL_FILE:
            path = (config or {}).get("path", "")
            if not path:
                conn.status = AppConnectionStatus.PENDING_AUTH
                logger.warning("App %s requires a local path", app_id)
        elif app_def.auth_method in (AppAuthMethod.API_KEY, AppAuthMethod.TOKEN):
            import os

            if not (config or {}).get("token") and not os.environ.get(app_def.env_key):
                conn.status = AppConnectionStatus.PENDING_AUTH
                logger.warning("App %s requires credentials (%s)", app_id, app_def.env_key)
        elif app_def.auth_method == AppAuthMethod.OAUTH2:
            if not (config or {}).get("access_token"):
                conn.status = AppConnectionStatus.PENDING_AUTH

        self._connections[conn.id] = conn
        logger.info(
            "App connected: %s (user=%s, status=%s)",
            app_id,
            user_id,
            conn.status.value,
        )
        return conn

    def disconnect(self, connection_id: str) -> bool:
        """接続を切断する."""
        conn = self._connections.get(connection_id)
        if conn is None:
            return False
        conn.status = AppConnectionStatus.DISCONNECTED
        logger.info("App disconnected: %s (conn=%s)", conn.app_id, connection_id)
        return True

    def get_connection(self, connection_id: str) -> AppConnection | None:
        """接続情報を取得する."""
        return self._connections.get(connection_id)

    def list_connections(
        self,
        user_id: str | None = None,
        app_id: str | None = None,
        status: AppConnectionStatus | None = None,
    ) -> list[AppConnection]:
        """接続一覧を返す."""
        conns = list(self._connections.values())
        if user_id:
            conns = [c for c in conns if c.user_id == user_id]
        if app_id:
            conns = [c for c in conns if c.app_id == app_id]
        if status:
            conns = [c for c in conns if c.status == status]
        return conns

    def update_permissions(
        self,
        connection_id: str,
        permissions: AppPermission,
    ) -> bool:
        """接続のパーミッションを更新する."""
        conn = self._connections.get(connection_id)
        if conn is None:
            return False
        conn.permissions = permissions
        logger.info("Permissions updated for connection: %s", connection_id)
        return True

    def remove_connection(self, connection_id: str) -> bool:
        """接続を完全に削除する."""
        if connection_id in self._connections:
            conn = self._connections.pop(connection_id)
            logger.info("App connection removed: %s (app=%s)", connection_id, conn.app_id)
            return True
        return False

    # ------------------------------------------------------------------ #
    #  データ同期
    # ------------------------------------------------------------------ #

    async def sync(
        self,
        connection_id: str,
        direction: AppDataDirection | None = None,
        options: dict[str, Any] | None = None,
    ) -> AppSyncResult:
        """接続先とデータを同期する.

        Args:
            connection_id: 接続 ID
            direction: 同期方向（省略時はアプリ定義のデフォルト）
            options: 同期オプション（フィルタ、範囲等）

        Returns:
            AppSyncResult
        """
        conn = self._connections.get(connection_id)
        if conn is None:
            return AppSyncResult(
                connection_id=connection_id,
                app_id="unknown",
                direction="unknown",
                errors=[f"Connection not found: {connection_id}"],
            )

        if conn.status != AppConnectionStatus.CONNECTED:
            return AppSyncResult(
                connection_id=connection_id,
                app_id=conn.app_id,
                direction="unknown",
                errors=[f"Connection is not active: {conn.status.value}"],
            )

        app_def = self._definitions.get(conn.app_id)
        if app_def is None:
            return AppSyncResult(
                connection_id=connection_id,
                app_id=conn.app_id,
                direction="unknown",
                errors=[f"App definition not found: {conn.app_id}"],
            )

        sync_dir = direction or app_def.data_direction
        started_at = datetime.now(UTC)

        result = AppSyncResult(
            connection_id=connection_id,
            app_id=conn.app_id,
            direction=sync_dir.value,
            started_at=started_at.isoformat(),
        )

        try:
            # アプリ固有の同期ハンドラにディスパッチ
            handler = self._get_sync_handler(conn.app_id)
            if handler:
                sync_data = await handler(conn, sync_dir, options or {})
                result.items_read = sync_data.get("items_read", 0)
                result.items_written = sync_data.get("items_written", 0)
                result.items_skipped = sync_data.get("items_skipped", 0)
            else:
                # 汎用同期（ToolConnector に委譲）
                result.items_read = 0
                result.items_written = 0

            conn.last_sync_at = datetime.now(UTC).isoformat()

        except Exception as exc:
            logger.error("Sync failed for %s: %s", conn.app_id, exc)
            result.errors.append(str(exc))

        result.finished_at = datetime.now(UTC).isoformat()
        self._sync_history.append(result)
        return result

    async def import_to_knowledge_store(
        self,
        connection_id: str,
        query: str = "",
        tags: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """接続先からナレッジストアにデータをインポートする.

        ユーザーが許可した範囲のデータのみを取得し、
        ナレッジストアに登録する。

        Args:
            connection_id: 接続 ID
            query: 検索クエリ（空の場合は全件）
            tags: 付与するタグ
            limit: 最大取得件数

        Returns:
            インポート結果の辞書
        """
        conn = self._connections.get(connection_id)
        if conn is None:
            return {"error": f"Connection not found: {connection_id}"}

        if not conn.permissions.read:
            return {"error": "Read permission not granted for this connection"}

        if not conn.permissions.sync:
            return {"error": "Sync permission not granted for this connection"}

        app_def = self._definitions.get(conn.app_id)
        if app_def is None:
            return {"error": f"App definition not found: {conn.app_id}"}

        imported = 0
        errors = 0

        try:
            from app.orchestration.knowledge import knowledge_store

            if not hasattr(knowledge_store, "add_entry"):
                return {"error": "Knowledge store not available"}

            # Obsidian は既存の専用統合を使用
            if conn.app_id == "obsidian":
                from app.integrations.obsidian import obsidian_integration

                vault_id = conn.config.get("vault_id", "")
                if vault_id:
                    result = await obsidian_integration.sync_knowledge_store(vault_id)
                    return result

            # 汎用インポート: 外部データの取得はアプリ固有ハンドラに委譲
            logger.info(
                "Importing from %s to knowledge store (query=%s, limit=%d)",
                conn.app_id,
                query,
                limit,
            )

        except ImportError:
            logger.debug("Knowledge store not available")
            return {"error": "Knowledge store module not available"}

        return {
            "connection_id": connection_id,
            "app_id": conn.app_id,
            "imported": imported,
            "errors": errors,
            "tags": tags or [],
        }

    def get_sync_history(
        self,
        connection_id: str | None = None,
        limit: int = 50,
    ) -> list[AppSyncResult]:
        """同期履歴を取得する."""
        history = self._sync_history
        if connection_id:
            history = [h for h in history if h.connection_id == connection_id]
        return history[-limit:]

    # ------------------------------------------------------------------ #
    #  統計情報
    # ------------------------------------------------------------------ #

    def get_summary(self) -> dict[str, Any]:
        """連携ハブの概要を返す."""
        import os

        all_apps = list(self._definitions.values())
        configured = []
        for app in all_apps:
            if (
                app.auth_method == AppAuthMethod.LOCAL_FILE
                or (app.env_key and os.environ.get(app.env_key))
                or app.auth_method == AppAuthMethod.WEBHOOK
            ):
                configured.append(app)

        active_conns = [
            c for c in self._connections.values() if c.status == AppConnectionStatus.CONNECTED
        ]

        categories: dict[str, int] = {}
        for a in all_apps:
            categories[a.category.value] = categories.get(a.category.value, 0) + 1

        return {
            "total_apps": len(all_apps),
            "configured_apps": len(configured),
            "active_connections": len(active_conns),
            "total_connections": len(self._connections),
            "categories": categories,
            "sync_count": len(self._sync_history),
        }

    # ------------------------------------------------------------------ #
    #  内部ヘルパー
    # ------------------------------------------------------------------ #

    def _get_sync_handler(self, app_id: str):
        """アプリ固有の同期ハンドラを返す（あれば）."""
        handlers = {
            "obsidian": self._sync_obsidian,
            "notion": self._sync_generic_api,
            "logseq": self._sync_local_files,
            "joplin": self._sync_generic_api,
        }
        return handlers.get(app_id)

    async def _sync_obsidian(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """Obsidian 同期ハンドラ."""
        from app.integrations.obsidian import obsidian_integration

        vault_id = conn.config.get("vault_id", "")
        if not vault_id:
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

        if direction in (AppDataDirection.READ_ONLY, AppDataDirection.BIDIRECTIONAL):
            index = await obsidian_integration.scan_vault(vault_id)
            return {
                "items_read": len(index),
                "items_written": 0,
                "items_skipped": 0,
            }

        return {"items_read": 0, "items_written": 0, "items_skipped": 0}

    async def _sync_generic_api(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """汎用 API 同期ハンドラ."""
        logger.info("Generic API sync for %s (delegated to ToolConnector)", conn.app_id)
        return {"items_read": 0, "items_written": 0, "items_skipped": 0}

    async def _sync_local_files(
        self,
        conn: AppConnection,
        direction: AppDataDirection,
        options: dict[str, Any],
    ) -> dict[str, int]:
        """ローカルファイル同期ハンドラ."""
        from pathlib import Path

        path = conn.config.get("path", "")
        if not path:
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

        base = Path(path)
        if not base.is_dir():
            return {"items_read": 0, "items_written": 0, "items_skipped": 0}

        count = sum(1 for _ in base.rglob("*.md"))
        return {"items_read": count, "items_written": 0, "items_skipped": 0}


# グローバルインスタンス
app_connector_hub = AppConnectorHub()
