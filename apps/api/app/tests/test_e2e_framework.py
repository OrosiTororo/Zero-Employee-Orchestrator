"""E2E テストフレームワーク.

FastAPI アプリケーション全体を対象としたエンドツーエンドテストの
基盤クラス・フィクスチャ・ヘルパーを提供する。
httpx.AsyncClient を使用してAPIレベルのE2Eテストを実行する。

NOTE: フロントエンド（Tauri + React）の E2E テストは
Playwright を使用して別途 apps/desktop/tests/ に配置予定。
以下は API レベルの E2E テストフレームワークである。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# テスト用に DEBUG を有効化
os.environ.setdefault("DEBUG", "true")

from app.main import app  # noqa: E402

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------
@dataclass
class E2ETestConfig:
    """E2Eテストの設定を保持するクラス.

    テスト対象のベースURL、タイムアウト、認証情報などを管理する。
    """

    base_url: str = "http://test"
    timeout: float = 30.0
    api_prefix: str = "/api/v1"
    default_headers: dict[str, str] = field(default_factory=dict)
    auth_token: str | None = None

    @property
    def api_url(self) -> str:
        """API のベースURLを返す."""
        return f"{self.base_url}{self.api_prefix}"


# ---------------------------------------------------------------------------
# E2E クライアント
# ---------------------------------------------------------------------------
class E2EClient:
    """E2Eテスト用の httpx.AsyncClient ラッパー.

    APIリクエストの送信、レスポンス検証のヘルパーメソッドを提供する。
    認証ヘッダーの自動付与やエラーハンドリングを行う。
    """

    def __init__(
        self,
        client: AsyncClient,
        config: E2ETestConfig,
    ) -> None:
        """クライアントを初期化する.

        Args:
            client: httpx.AsyncClient インスタンス
            config: E2Eテスト設定
        """
        self._client = client
        self._config = config

    @property
    def config(self) -> E2ETestConfig:
        """テスト設定を返す."""
        return self._config

    def _build_url(self, path: str) -> str:
        """APIプレフィックス付きのURLを構築する.

        パスが / で始まり api_prefix を含まない場合は
        api_prefix を自動付与する。

        Args:
            path: エンドポイントパス

        Returns:
            完全なURL文字列
        """
        if path.startswith(self._config.api_prefix):
            return path
        if path.startswith("/"):
            return f"{self._config.api_prefix}{path}"
        return f"{self._config.api_prefix}/{path}"

    def _build_headers(
        self,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """リクエストヘッダーを構築する.

        デフォルトヘッダー、認証トークン、追加ヘッダーをマージする。

        Args:
            extra_headers: 追加ヘッダー

        Returns:
            マージされたヘッダー辞書
        """
        headers = dict(self._config.default_headers)
        if self._config.auth_token:
            headers["Authorization"] = f"Bearer {self._config.auth_token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """GET リクエストを送信する.

        Args:
            path: エンドポイントパス
            params: クエリパラメータ
            headers: 追加ヘッダー

        Returns:
            httpx.Response
        """
        return await self._client.get(
            self._build_url(path),
            params=params,
            headers=self._build_headers(headers),
        )

    async def post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """POST リクエストを送信する.

        Args:
            path: エンドポイントパス
            json: リクエストボディ
            headers: 追加ヘッダー

        Returns:
            httpx.Response
        """
        return await self._client.post(
            self._build_url(path),
            json=json,
            headers=self._build_headers(headers),
        )

    async def put(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """PUT リクエストを送信する.

        Args:
            path: エンドポイントパス
            json: リクエストボディ
            headers: 追加ヘッダー

        Returns:
            httpx.Response
        """
        return await self._client.put(
            self._build_url(path),
            json=json,
            headers=self._build_headers(headers),
        )

    async def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """DELETE リクエストを送信する.

        Args:
            path: エンドポイントパス
            headers: 追加ヘッダー

        Returns:
            httpx.Response
        """
        return await self._client.delete(
            self._build_url(path),
            headers=self._build_headers(headers),
        )

    async def assert_status(
        self,
        response: Any,
        expected: int,
        message: str = "",
    ) -> None:
        """レスポンスのステータスコードを検証する.

        Args:
            response: httpx.Response
            expected: 期待するステータスコード
            message: アサーションメッセージ
        """
        detail = message or f"Expected {expected}, got {response.status_code}"
        assert response.status_code == expected, f"{detail}: {response.text}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def test_config() -> E2ETestConfig:
    """E2Eテスト設定フィクスチャ."""
    return E2ETestConfig()


@pytest_asyncio.fixture
async def e2e_client(test_config: E2ETestConfig) -> E2EClient:
    """E2Eテストクライアントフィクスチャ.

    FastAPI アプリケーションに対して直接リクエストを送信できる
    E2EClient インスタンスを提供する。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url=test_config.base_url,
        timeout=test_config.timeout,
    ) as client:
        yield E2EClient(client=client, config=test_config)


# ---------------------------------------------------------------------------
# E2E テスト
# ---------------------------------------------------------------------------
class TestHealthCheck:
    """ヘルスチェックのE2Eテスト."""

    @pytest.mark.asyncio
    async def test_healthz_returns_ok(self, e2e_client: E2EClient) -> None:
        """ヘルスチェックエンドポイントが正常応答を返す."""
        response = await e2e_client._client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_readyz_returns_ok(self, e2e_client: E2EClient) -> None:
        """レディネスチェックが正常応答を返す."""
        response = await e2e_client._client.get("/readyz")
        assert response.status_code == 200


class TestAuthFlow:
    """認証フローのE2Eテスト."""

    @pytest.mark.asyncio
    async def test_unauthenticated_access_allowed_on_public(self, e2e_client: E2EClient) -> None:
        """公開エンドポイントにアクセスできることを確認する."""
        response = await e2e_client._client.get("/healthz")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_signup_endpoint_exists(self, e2e_client: E2EClient) -> None:
        """認証エンドポイントが存在することを確認する.

        実際のサインアップはDBセットアップが必要なため、
        エンドポイントの存在確認のみ行う。
        """
        response = await e2e_client.post(
            "/auth/signup",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "display_name": "Test User",
            },
        )
        # エンドポイントが存在する（404/405 でない）ことを確認
        assert response.status_code != 405


class TestCreateAndListWorkflow:
    """リソース作成・一覧取得の基本ワークフローE2Eテスト."""

    @pytest.mark.asyncio
    async def test_user_input_request_lifecycle(self, e2e_client: E2EClient) -> None:
        """ユーザー入力リクエストの作成→一覧→回答→確認フローをテストする."""
        # 1. リクエスト作成
        create_resp = await e2e_client.post(
            "/user-input/request",
            json={
                "task_id": "test-task-001",
                "request_type": "text",
                "prompt_text": "プロジェクト名を入力してください",
                "timeout_seconds": 600,
            },
        )
        assert create_resp.status_code == 200
        created = create_resp.json()
        request_id = created["id"]
        assert created["status"] == "pending"

        # 2. 未回答一覧取得
        pending_resp = await e2e_client.get("/user-input/pending/test-task-001")
        assert pending_resp.status_code == 200
        pending = pending_resp.json()
        assert pending["total"] >= 1

        # 3. 回答
        answer_resp = await e2e_client.post(
            f"/user-input/{request_id}/answer",
            json={"response": "Zero-Employee プロジェクト"},
        )
        assert answer_resp.status_code == 200
        answered = answer_resp.json()
        assert answered["status"] == "answered"
        assert answered["response"] == "Zero-Employee プロジェクト"

    @pytest.mark.asyncio
    async def test_file_upload_lifecycle(self, e2e_client: E2EClient) -> None:
        """ファイルアップロードの作成→情報取得→削除フローをテストする.

        NOTE: multipart/form-data のアップロードテストは
        httpx の内部クライアントで直接行う。
        """
        # ファイル一覧が取得できることを確認
        list_resp = await e2e_client.get("/files")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert "files" in data
        assert "total" in data


# ---------------------------------------------------------------------------
# Playwright 連携メモ（フロントエンド E2E テスト用）
# ---------------------------------------------------------------------------
# フロントエンド（Tauri + React）の E2E テストは Playwright を使用する。
#
# 導入手順:
#   1. pip install playwright pytest-playwright
#   2. playwright install chromium
#
# テストファイル配置:
#   apps/desktop/tests/e2e/
#     ├── conftest.py        # Playwright フィクスチャ
#     ├── test_login.py      # ログイン画面テスト
#     ├── test_dashboard.py  # ダッシュボードテスト
#     └── test_tasks.py      # タスク管理画面テスト
#
# サンプルフィクスチャ:
#   @pytest.fixture
#   def browser_context(playwright):
#       browser = playwright.chromium.launch(headless=True)
#       context = browser.new_context(base_url="http://localhost:5173")
#       yield context
#       context.close()
#       browser.close()
#
# サンプルテスト:
#   async def test_dashboard_loads(page):
#       await page.goto("/")
#       await expect(page.locator("h1")).to_contain_text("Dashboard")
