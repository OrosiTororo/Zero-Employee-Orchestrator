"""Auth endpoint tests."""

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.routes import auth as auth_routes
from app.core.config import settings
from app.models.audit import AuditLog
from app.models.user import OAuthIdentity, User
from app.services import auth_service
from app.services.auth_service import (
    GoogleOAuthExchangeError,
    GoogleUserInfo,
)

CODE_VERIFIER = "verifier_value_that_is_long_enough_for_pkce_1234567890"


def _configure_google(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_LOGIN_CLIENT_ID", "client-id")
    monkeypatch.setattr(settings, "GOOGLE_LOGIN_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(
        settings,
        "GOOGLE_LOGIN_REDIRECT_URI",
        "https://app.example.com/api/v1/auth/google/callback",
    )


async def _start_google_flow(client: AsyncClient) -> str:
    response = await client.get("/api/v1/auth/google/authorize")
    assert response.status_code == 200
    return response.json()["state"]


async def _complete_google_flow(
    client: AsyncClient,
    state: str,
    code: str = "authorization-code",
):
    return await client.get(
        "/api/v1/auth/google/callback",
        params={"state": state, "code": code},
    )


async def _poll_google_flow(client: AsyncClient, state: str):
    return await client.post(
        "/api/v1/auth/google/poll",
        json={"state": state},
    )


@pytest.mark.asyncio
async def test_register_creates_user(client: AsyncClient):
    """登録で新規ユーザーが作成される."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "display_name": "test",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "test"
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_existing_user(client: AsyncClient):
    """既存ユーザーで再ログインできる."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test2@example.com",
            "password": "testpassword123",
            "display_name": "test2",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test2@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """ログアウトが正常に完了する."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_google_authorize_requires_configuration(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "GOOGLE_LOGIN_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GOOGLE_LOGIN_CLIENT_SECRET", "")

    response = await client.get("/api/v1/auth/google/authorize")

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_google_authorize_binds_server_state_and_pkce(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_google(monkeypatch)

    response = await client.get("/api/v1/auth/google/authorize")

    assert response.status_code == 200
    state = response.json()["state"]
    pending = auth_routes._google_oauth_pending[state]
    query = parse_qs(urlparse(response.json()["url"]).query)
    assert query["state"] == [state]
    assert query["code_challenge"] == [auth_routes._pkce_challenge(pending.code_verifier)]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == ["https://app.example.com/api/v1/auth/google/callback"]
    assert "access_type" not in query
    assert "prompt" not in query
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"


@pytest.mark.asyncio
async def test_google_login_creates_stable_identity_and_audit(
    client: AsyncClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_google(monkeypatch)
    seen_verifier = ""

    async def fake_exchange(code: str, code_verifier: str) -> GoogleUserInfo:
        nonlocal seen_verifier
        assert code == "authorization-code"
        seen_verifier = code_verifier
        return GoogleUserInfo(
            subject="google-subject-1",
            email="google@example.com",
            display_name="Google User",
        )

    monkeypatch.setattr(auth_routes, "exchange_google_code", fake_exchange)
    state = await _start_google_flow(client)
    pending_verifier = auth_routes._google_oauth_pending[state].code_verifier

    callback_response = await _complete_google_flow(client, state)
    poll_response = await _poll_google_flow(client, state)

    assert callback_response.status_code == 200
    assert seen_verifier == pending_verifier
    assert poll_response.status_code == 200
    assert poll_response.json()["status"] == "complete"
    assert poll_response.headers["cache-control"] == "no-store"
    assert poll_response.headers["referrer-policy"] == "no-referrer"
    user_id = poll_response.json()["user_id"]

    identity_result = await db_session.execute(select(OAuthIdentity))
    identity = identity_result.scalar_one()
    assert str(identity.user_id) == user_id
    assert identity.provider == "google"
    assert identity.subject == "google-subject-1"
    assert identity.provider_email == "google@example.com"

    audit_result = await db_session.execute(select(AuditLog))
    audit = audit_result.scalar_one()
    assert audit.event_type == "auth.oauth.login"
    assert audit.details_json == {"provider": "google", "account_created": True}
    assert (await _poll_google_flow(client, state)).status_code == 404


@pytest.mark.asyncio
async def test_google_login_reuses_subject_when_email_changes(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_google(monkeypatch)
    current_email = "first@example.com"

    async def fake_exchange(code: str, code_verifier: str) -> GoogleUserInfo:
        return GoogleUserInfo(
            subject="stable-google-subject",
            email=current_email,
            display_name="Google User",
        )

    monkeypatch.setattr(auth_routes, "exchange_google_code", fake_exchange)

    first_state = await _start_google_flow(client)
    await _complete_google_flow(client, first_state)
    first_poll = await _poll_google_flow(client, first_state)

    current_email = "renamed@example.com"
    second_state = await _start_google_flow(client)
    await _complete_google_flow(client, second_state)
    second_poll = await _poll_google_flow(client, second_state)

    assert first_poll.status_code == 200
    assert second_poll.status_code == 200
    assert second_poll.json()["user_id"] == first_poll.json()["user_id"]


@pytest.mark.asyncio
async def test_google_login_does_not_implicitly_link_local_account(
    client: AsyncClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_google(monkeypatch)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "existing@example.com",
            "password": "testpassword123",
            "display_name": "Existing User",
        },
    )

    async def fake_exchange(code: str, code_verifier: str) -> GoogleUserInfo:
        return GoogleUserInfo(
            subject="different-google-subject",
            email="existing@example.com",
            display_name="Existing User",
        )

    monkeypatch.setattr(auth_routes, "exchange_google_code", fake_exchange)
    state = await _start_google_flow(client)

    callback_response = await _complete_google_flow(client, state)
    poll_response = await _poll_google_flow(client, state)

    assert callback_response.status_code == 409
    assert poll_response.json() == {
        "status": "failed",
        "error": "account_link_required",
    }
    user_result = await db_session.execute(select(User).where(User.email == "existing@example.com"))
    assert user_result.scalar_one().auth_provider == "local"


@pytest.mark.asyncio
async def test_google_login_returns_sanitized_provider_error(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_google(monkeypatch)

    async def fake_exchange(code: str, code_verifier: str) -> GoogleUserInfo:
        raise GoogleOAuthExchangeError("provider response included sensitive details")

    monkeypatch.setattr(auth_routes, "exchange_google_code", fake_exchange)
    state = await _start_google_flow(client)

    callback_response = await _complete_google_flow(client, state)
    poll_response = await _poll_google_flow(client, state)

    assert callback_response.status_code == 400
    assert "provider response included sensitive details" not in callback_response.text
    assert poll_response.json() == {
        "status": "failed",
        "error": "oauth_failed",
    }


@pytest.mark.asyncio
async def test_google_provider_error_is_not_reflected_in_callback_html(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_google(monkeypatch)
    state = await _start_google_flow(client)

    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"state": state, "error": "<script>alert(1)</script>"},
    )

    assert response.status_code == 400
    assert "<script>alert(1)</script>" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert (await _poll_google_flow(client, state)).json()["status"] == "failed"


@pytest.mark.asyncio
async def test_google_callback_result_cannot_be_overwritten(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_google(monkeypatch)

    async def fake_exchange(code: str, code_verifier: str) -> GoogleUserInfo:
        return GoogleUserInfo(
            subject="one-shot-subject",
            email="one-shot@example.com",
            display_name="One Shot User",
        )

    monkeypatch.setattr(auth_routes, "exchange_google_code", fake_exchange)
    state = await _start_google_flow(client)

    assert (await _complete_google_flow(client, state)).status_code == 200
    replay = await client.get(
        "/api/v1/auth/google/callback",
        params={"state": state, "error": "access_denied"},
    )
    poll_response = await _poll_google_flow(client, state)

    assert replay.status_code == 400
    assert "invalid or expired" in replay.text
    assert poll_response.json()["status"] == "complete"


@pytest.mark.asyncio
async def test_google_poll_rejects_expired_state(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_google(monkeypatch)
    state = await _start_google_flow(client)
    auth_routes._google_oauth_pending[state].created_at = datetime.now(UTC) - timedelta(minutes=11)

    response = await _poll_google_flow(client, state)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_google_exchange_sends_verifier_and_validates_identity(
    monkeypatch: pytest.MonkeyPatch,
):
    captured_token_request: dict = {}

    class FakeResponse:
        def __init__(self, payload: dict):
            self.payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self.payload

    class FakeAsyncClient:
        def __init__(self, *, timeout: float):
            assert timeout == 10.0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, url: str, *, data: dict) -> FakeResponse:
            captured_token_request.update(data)
            return FakeResponse({"access_token": "provider-access-token"})

        async def get(self, url: str, *, headers: dict) -> FakeResponse:
            assert headers == {"Authorization": "Bearer provider-access-token"}
            return FakeResponse(
                {
                    "sub": "stable-subject",
                    "email": "verified@example.com",
                    "email_verified": True,
                    "name": "Verified User",
                }
            )

    _configure_google(monkeypatch)
    monkeypatch.setattr(auth_service.httpx, "AsyncClient", FakeAsyncClient)

    identity = await auth_service.exchange_google_code("code", CODE_VERIFIER)

    assert identity.subject == "stable-subject"
    assert identity.email == "verified@example.com"
    assert captured_token_request["code_verifier"] == CODE_VERIFIER
    assert captured_token_request["redirect_uri"] == (
        "https://app.example.com/api/v1/auth/google/callback"
    )
