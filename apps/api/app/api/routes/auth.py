"""Authentication endpoints - registration, login, session management."""

import base64
import hashlib
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html import escape
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user, get_optional_user  # noqa: F401
from app.api.deps.database import get_db
from app.core.rate_limit import limiter
from app.core.security import generate_uuid, hash_password
from app.models.audit import AuditLog
from app.models.company import Company
from app.models.user import CompanyMember, User
from app.schemas.auth import (
    AnonymousSessionResponse,
    ChangePasswordRequest,
    GoogleAuthorizeResponse,
    GooglePollCompleteResponse,
    GooglePollFailedResponse,
    GooglePollPendingResponse,
    GooglePollRequest,
    LinkAccountResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MessageResponse,
    OAuthLoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshResponse,
    RegisterRequest,
    SetupStatusResponse,
    UserRead,
)
from app.services.auth_service import (
    GoogleOAuthConfigurationError,
    GoogleOAuthError,
    OAuthAccountLinkRequired,
    authenticate_user,
    build_google_authorization_url,
    change_password,
    confirm_password_reset,
    create_access_token,
    exchange_google_code,
    get_or_create_google_user,
    register_user,
    request_password_reset,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_user_setup_completed(db: AsyncSession, user_id: str) -> bool:
    """Check if the user's company has completed initial setup."""
    result = await db.execute(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(CompanyMember.user_id == uuid.UUID(user_id))
        .limit(1)
    )
    company = result.scalar_one_or_none()
    if company is None:
        return False
    return bool(company.setup_completed)


@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")
async def register(request: Request, req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new account — email + password, auto-create default organization."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This email address is already registered")

    user = await register_user(db, req.email, req.password, req.display_name)
    token = create_access_token(str(user.id))

    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
        setup_completed=False,
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/password."""
    user = await authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email address or password")

    token = create_access_token(str(user.id))
    setup_done = await _get_user_setup_completed(db, str(user.id))
    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
        setup_completed=setup_done,
    )


# ---------------------------------------------------------------------------
# Google OAuth — short-lived server-side PKCE transaction store
# ---------------------------------------------------------------------------

GOOGLE_OAUTH_TRANSACTION_TTL = timedelta(minutes=10)
OAUTH_RESPONSE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'"
    ),
}


@dataclass
class _GoogleOAuthPending:
    code_verifier: str
    created_at: datetime
    callback_started: bool = False
    result: dict[str, Any] | None = None


_google_oauth_pending: dict[str, _GoogleOAuthPending] = {}


def _pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _prune_google_oauth_pending(now: datetime | None = None) -> None:
    current_time = now or datetime.now(UTC)
    expired_states = [
        state
        for state, pending in _google_oauth_pending.items()
        if current_time - pending.created_at > GOOGLE_OAUTH_TRANSACTION_TTL
        or current_time < pending.created_at
    ]
    for state in expired_states:
        _google_oauth_pending.pop(state, None)


def _oauth_html_response(
    *,
    success: bool,
    message: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    return HTMLResponse(
        _oauth_result_html(success=success, message=message),
        status_code=status_code,
        headers=OAUTH_RESPONSE_HEADERS,
    )


def _set_oauth_response_headers(response: Response) -> None:
    for name, value in OAUTH_RESPONSE_HEADERS.items():
        response.headers[name] = value


@router.get("/google/authorize", response_model=GoogleAuthorizeResponse)
@limiter.limit("10/minute")
async def google_authorize(request: Request, response: Response) -> GoogleAuthorizeResponse:
    """Start a short-lived Google OAuth transaction for Web or Tauri clients."""
    _set_oauth_response_headers(response)
    _prune_google_oauth_pending()
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    try:
        url = build_google_authorization_url(
            state,
            _pkce_challenge(code_verifier),
        )
    except GoogleOAuthConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _google_oauth_pending[state] = _GoogleOAuthPending(
        code_verifier=code_verifier,
        created_at=datetime.now(UTC),
    )
    return GoogleAuthorizeResponse(url=url, state=state)


@router.get("/google/callback", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Complete a server-bound PKCE exchange and make the result pollable once."""
    _prune_google_oauth_pending()

    if not state:
        logger.warning("Google OAuth provider returned an incomplete response")
        return _oauth_html_response(
            success=False,
            message="Google sign-in could not be completed.",
            status_code=400,
        )

    pending = _google_oauth_pending.get(state)
    if pending is None or pending.callback_started:
        return _oauth_html_response(
            success=False,
            message="This Google sign-in request is invalid or expired.",
            status_code=400,
        )

    if error or not code:
        pending.callback_started = True
        pending.result = {
            "status": "failed",
            "error": "oauth_failed",
        }
        logger.warning("Google OAuth provider returned an incomplete response")
        return _oauth_html_response(
            success=False,
            message="Google sign-in could not be completed.",
            status_code=400,
        )

    pending.callback_started = True

    try:
        identity = await exchange_google_code(code, pending.code_verifier)
        oauth_result = await get_or_create_google_user(db, identity)
        user = oauth_result.user
        setup_done = await _get_user_setup_completed(db, str(user.id))
        db.add(
            AuditLog(
                id=generate_uuid(),
                company_id=oauth_result.company_id,
                actor_type="user",
                actor_user_id=user.id,
                event_type="auth.oauth.login",
                target_type="user",
                target_id=user.id,
                details_json={
                    "provider": "google",
                    "account_created": oauth_result.created,
                },
            )
        )
        await db.commit()
    except OAuthAccountLinkRequired:
        await db.rollback()
        pending.result = {
            "status": "failed",
            "error": "account_link_required",
        }
        return _oauth_html_response(
            success=False,
            message=(
                "An account with this email already exists. "
                "Sign in with your password before linking Google."
            ),
            status_code=409,
        )
    except GoogleOAuthConfigurationError:
        await db.rollback()
        pending.result = {
            "status": "failed",
            "error": "not_configured",
        }
        return _oauth_html_response(
            success=False,
            message="Google sign-in is not configured.",
            status_code=503,
        )
    except GoogleOAuthError:
        await db.rollback()
        pending.result = {
            "status": "failed",
            "error": "oauth_failed",
        }
        return _oauth_html_response(
            success=False,
            message="Google sign-in could not be completed.",
            status_code=400,
        )
    except Exception:
        await db.rollback()
        pending.result = {
            "status": "failed",
            "error": "oauth_failed",
        }
        logger.exception("Unexpected Google OAuth callback failure")
        return _oauth_html_response(
            success=False,
            message="Google sign-in could not be completed.",
            status_code=500,
        )

    pending.result = {
        "status": "complete",
        "access_token": create_access_token(str(user.id)),
        "user_id": str(user.id),
        "display_name": user.display_name,
        "setup_completed": setup_done,
    }
    return _oauth_html_response(success=True)


@router.post(
    "/google/poll",
    response_model=(
        GooglePollCompleteResponse | GooglePollPendingResponse | GooglePollFailedResponse
    ),
)
@limiter.limit("150/minute")
async def google_poll(
    request: Request,
    response: Response,
    req: GooglePollRequest,
) -> GooglePollCompleteResponse | GooglePollPendingResponse | GooglePollFailedResponse:
    """Return a completed OAuth result once without putting state in access logs."""
    _set_oauth_response_headers(response)
    _prune_google_oauth_pending()
    pending = _google_oauth_pending.get(req.state)
    if pending is None:
        raise HTTPException(status_code=404, detail="Unknown or expired state")
    if pending.result is None:
        return GooglePollPendingResponse(status="pending")

    result = pending.result
    _google_oauth_pending.pop(req.state, None)
    if result.get("status") == "failed":
        return GooglePollFailedResponse.model_validate(result)
    return GooglePollCompleteResponse.model_validate(result)


@router.post("/oauth/login", response_model=LoginResponse)
async def oauth_login(req: OAuthLoginRequest) -> LoginResponse:
    """Reject the legacy direct-code endpoint in favor of the PKCE flow."""
    raise HTTPException(
        status_code=410,
        detail="Use GET /auth/google/authorize and POST /auth/google/poll.",
    )


def _oauth_result_html(*, success: bool, message: str | None = None) -> str:
    """Return a minimal, escaped HTML page shown after the OAuth callback."""
    if success:
        title = "Login Successful"
        body = (
            "<h2>&#10004; Login successful</h2><p>You can close this tab and return to the app.</p>"
        )
    else:
        title = "Login Failed"
        safe_message = escape(message or "Unknown error")
        body = f"<h2>&#10008; Login failed</h2><p>{safe_message}</p>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;
background:#1E1E1E;color:#D4D4D4;font-size:13px;}}
.card{{text-align:center;padding:2rem 3rem;border-radius:8px;background:#252526;
border:1px solid #3E3E42;}} h2{{margin-bottom:.5rem;}} p{{color:#BBBBBB;}}</style></head>
<body><div class="card">{body}</div></body></html>"""


@router.post("/logout", response_model=LogoutResponse)
async def logout():
    """Logout."""
    return {"status": "ok", "message": "Logged out successfully"}


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserRead(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        status=user.status,
        auth_provider=user.auth_provider,
        last_login_at=str(user.last_login_at) if user.last_login_at else None,
        created_at=str(user.created_at),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(user: User = Depends(get_current_user)):
    """Refresh token."""
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
@limiter.limit("3/minute")
async def password_reset_request(
    request: Request,
    req: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset.

    Generates a short-lived reset token.  In production this token
    would be sent via email; in the current implementation it is
    returned directly in the response for development convenience.
    """
    token = await request_password_reset(db, req.email)
    # Always return 200 to prevent email enumeration attacks
    if token is None:
        return {"message": "If an account with this email exists, a reset link has been sent."}
    # NOTE: In production, send the token via email instead of returning it.
    return {
        "message": "If an account with this email exists, a reset link has been sent.",
        "reset_token": token,  # Remove in production — send via email instead
    }


@router.post("/password-reset/confirm", response_model=MessageResponse)
@limiter.limit("5/minute")
async def password_reset_confirm(
    request: Request,
    req: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Confirm a password reset with the token received via email."""
    success = await confirm_password_reset(db, req.token, req.new_password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        )
    return {"message": "Password has been reset successfully"}


@router.post("/change-password", response_model=MessageResponse)
async def change_password_endpoint(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the current authenticated user."""
    success = await change_password(db, user, req.current_password, req.new_password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )
    return {"message": "Password changed successfully"}


@router.post("/anonymous-session", response_model=AnonymousSessionResponse)
@limiter.limit("10/minute")
async def create_anonymous_session(request: Request, db: AsyncSession = Depends(get_db)):
    """Create an anonymous session without login.

    Basic features are available without logging in.
    Logging in enables state sharing across multiple devices.
    Anonymous session data can be linked to an account later.
    """
    anon_id = generate_uuid()
    async with db.begin_nested():
        user = User(
            id=anon_id,
            email=None,
            display_name=f"Anonymous-{str(anon_id)[:8]}",
            role="anonymous",
            status="active",
            auth_provider="anonymous",
        )
        db.add(user)

        company = Company(
            id=generate_uuid(),
            slug=f"anon-{str(anon_id)[:8]}",
            name="Anonymous Workspace",
            mission="",
            description="",
            status="active",
        )
        db.add(company)

        member = CompanyMember(
            id=generate_uuid(),
            company_id=company.id,
            user_id=user.id,
            company_role="owner",
            status="active",
            joined_at=datetime.now(UTC),
        )
        db.add(member)

    await db.commit()

    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "user_id": str(user.id),
        "company_id": str(company.id),
        "display_name": user.display_name,
        "is_anonymous": True,
        "setup_completed": False,
        "message": "Login to enable state sharing across multiple devices",
    }


class LinkAccountRequest(BaseModel):
    email: str
    password: str
    display_name: str


@router.post("/link-account", response_model=LinkAccountResponse)
async def link_anonymous_to_account(
    req: LinkAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link an anonymous session to a formal account.

    After starting without login, create an account and
    carry over existing data.
    """
    if user.role != "anonymous":
        raise HTTPException(status_code=400, detail="Already linked to an account")

    # Check for duplicate email
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This email address is already registered")

    user.email = req.email
    user.display_name = req.display_name
    user.role = "user"
    user.auth_provider = "local"
    user.password_hash = hash_password(req.password)

    await db.commit()

    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "user_id": str(user.id),
        "display_name": req.display_name,
        "linked": True,
        "message": "Account created. Multi-device sharing is now enabled",
    }


@router.get("/setup-status", response_model=SetupStatusResponse)
async def get_setup_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether the current user's organization has completed initial setup."""
    setup_done = await _get_user_setup_completed(db, str(user.id))
    return {"setup_completed": setup_done}


@router.post("/setup-complete", response_model=SetupStatusResponse)
async def mark_setup_complete(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark the current user's organization setup as completed."""
    result = await db.execute(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(CompanyMember.user_id == user.id)
        .limit(1)
    )
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="No organization found")
    company.setup_completed = True
    await db.commit()
    return {"setup_completed": True}
