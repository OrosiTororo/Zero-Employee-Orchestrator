"""Authentication endpoints - registration, login, session management."""

import logging
import secrets
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import generate_uuid, hash_password
from app.models.company import Company
from app.models.user import CompanyMember, User
from app.schemas.auth import (
    AnonymousSessionResponse,
    ChangePasswordRequest,
    GoogleAuthorizeResponse,
    GooglePollCompleteResponse,
    GooglePollPendingResponse,
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
    authenticate_user,
    change_password,
    confirm_password_reset,
    create_access_token,
    decode_access_token,
    get_user_by_id,
    oauth_login_or_register,
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


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> User:
    """Extract current user from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.replace("Bearer ", "")
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


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
# Google OAuth — in-memory pending state store
# ---------------------------------------------------------------------------
# Maps state -> {"token": ..., "user_id": ..., ...} after successful callback.
# Entries are cleaned up after polling or after a timeout.
_google_oauth_pending: dict[str, dict] = {}

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def _google_redirect_uri(request: Request) -> str:
    """Build the Google OAuth redirect URI based on the incoming request."""
    base = str(request.base_url).rstrip("/")
    return f"{base}{settings.API_V1_PREFIX}/auth/google/callback"


@router.get("/google/authorize", response_model=GoogleAuthorizeResponse)
async def google_authorize(request: Request):
    """Get Google OAuth authorization URL.

    Returns the URL and a state token. The frontend should open this URL
    (in a popup or system browser) and poll /auth/google/poll?state=...
    until the login completes.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=501,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET via `zero-employee config set` or .env file.",
        )

    state = secrets.token_urlsafe(32)
    _google_oauth_pending[state] = {}  # placeholder — awaiting callback

    redirect_uri = _google_redirect_uri(request)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = f"{GOOGLE_AUTH_URL}?{httpx.QueryParams(params)}"
    return {"url": url, "state": state}


@router.get("/google/callback", response_class=HTMLResponse)
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback.

    Google redirects here after the user authenticates. This endpoint
    exchanges the authorization code for tokens, fetches user info,
    creates or finds the user, and stores the result for polling.
    Returns an HTML page that tells the user to return to the app.
    """
    if error:
        return HTMLResponse(
            _oauth_result_html(success=False, message=f"Google login failed: {error}")
        )

    if not code or not state:
        return HTMLResponse(
            _oauth_result_html(success=False, message="Missing code or state parameter.")
        )

    if state not in _google_oauth_pending:
        return HTMLResponse(_oauth_result_html(success=False, message="Invalid or expired state."))

    redirect_uri = _google_redirect_uri(request)

    try:
        # Exchange authorization code for tokens
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
        if token_resp.status_code != 200:
            logger.warning("Google token exchange failed: %s", token_resp.text)
            _google_oauth_pending.pop(state, None)
            return HTMLResponse(
                _oauth_result_html(success=False, message="Failed to exchange authorization code.")
            )

        token_data = token_resp.json()
        access_token_google = token_data.get("access_token")
        if not access_token_google:
            _google_oauth_pending.pop(state, None)
            return HTMLResponse(
                _oauth_result_html(success=False, message="No access token from Google.")
            )

        # Fetch user info from Google
        async with httpx.AsyncClient(timeout=10) as client:
            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token_google}"},
            )
        if userinfo_resp.status_code != 200:
            _google_oauth_pending.pop(state, None)
            return HTMLResponse(
                _oauth_result_html(success=False, message="Failed to fetch user info from Google.")
            )

        userinfo = userinfo_resp.json()
        email = userinfo.get("email")
        name = userinfo.get("name", email)

        if not email:
            _google_oauth_pending.pop(state, None)
            return HTMLResponse(
                _oauth_result_html(success=False, message="Google account has no email address.")
            )

        # Create or find user
        user, is_new = await oauth_login_or_register(
            db, email=email, display_name=name, provider="google"
        )
        token = create_access_token(str(user.id))
        setup_done = await _get_user_setup_completed(db, str(user.id))

        _google_oauth_pending[state] = {
            "access_token": token,
            "user_id": str(user.id),
            "display_name": user.display_name,
            "setup_completed": setup_done,
        }

        return HTMLResponse(_oauth_result_html(success=True))

    except httpx.HTTPError as exc:
        logger.exception("Google OAuth HTTP error: %s", exc)
        _google_oauth_pending.pop(state, None)
        return HTMLResponse(
            _oauth_result_html(success=False, message="Network error during Google login.")
        )


@router.get(
    "/google/poll",
    response_model=GooglePollCompleteResponse | GooglePollPendingResponse,
)
async def google_poll(state: str):
    """Poll for Google OAuth completion.

    The frontend calls this after opening the Google auth URL.
    Returns {"status": "pending"} until the callback is processed,
    then returns the login response and removes the state entry.
    """
    if state not in _google_oauth_pending:
        raise HTTPException(status_code=404, detail="Unknown or expired state")

    data = _google_oauth_pending[state]
    if not data:
        return {"status": "pending"}

    # Login complete — remove state and return credentials
    _google_oauth_pending.pop(state, None)
    return {
        "status": "complete",
        "access_token": data["access_token"],
        "user_id": data["user_id"],
        "display_name": data["display_name"],
        "setup_completed": data.get("setup_completed", False),
    }


@router.post("/oauth/login", response_model=LoginResponse)
async def oauth_login(req: OAuthLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login via OAuth provider.

    Currently supported: google (via /auth/google/authorize).
    Other providers (github, microsoft, okta) are on the roadmap.
    """
    supported = ["google"]
    if req.provider.lower() not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth provider '{req.provider}' is not yet supported. "
            f"Supported providers: {', '.join(supported)}. "
            "Use POST /auth/google/authorize for Google OAuth.",
        )


def _oauth_result_html(*, success: bool, message: str | None = None) -> str:
    """Return a minimal HTML page shown in the browser after OAuth callback."""
    if success:
        title = "Login Successful"
        body = (
            "<h2>&#10004; Login successful</h2><p>You can close this tab and return to the app.</p>"
        )
    else:
        title = "Login Failed"
        body = f"<h2>&#10008; Login failed</h2><p>{message or 'Unknown error'}</p>"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
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


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> User | None:
    """Authentication is optional — returns user if token is present, otherwise None."""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    user_id = decode_access_token(token)
    if not user_id:
        return None
    return await get_user_by_id(db, user_id)
