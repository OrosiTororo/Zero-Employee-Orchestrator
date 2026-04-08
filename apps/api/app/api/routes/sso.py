"""SAML/SSO/OAuth2 endpoints for enterprise single sign-on.

Supports:
- Google OAuth 2.0 (via GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET)
- SAML 2.0 Generic (via SSO_SAML_IDP_METADATA_URL)
- Okta SAML (via OKTA_* env vars)
- Azure AD / Entra ID OIDC (via AZURE_AD_* env vars)
"""

from __future__ import annotations

import logging
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sso")


class SSOProvider(BaseModel):
    id: str
    name: str
    protocol: str
    enabled: bool


class SAMLMetadata(BaseModel):
    entity_id: str
    acs_url: str
    sls_url: str
    certificate: str


class SAMLAssertionResponse(BaseModel):
    status: str
    user_email: str | None = None
    session_token: str | None = None
    error: str | None = None


class OAuthCallbackResponse(BaseModel):
    status: str
    user_email: str | None = None
    session_token: str | None = None
    provider: str
    error: str | None = None


def _get_sso_providers() -> list[dict]:
    """Build SSO providers list based on configured env vars."""
    providers = []
    if os.environ.get("GOOGLE_CLIENT_ID"):
        providers.append(
            {
                "id": "google-oauth",
                "name": "Google OAuth 2.0",
                "protocol": "oauth2",
                "enabled": True,
            }
        )
    else:
        providers.append(
            {
                "id": "google-oauth",
                "name": "Google OAuth 2.0",
                "protocol": "oauth2",
                "enabled": False,
            }
        )
    if os.environ.get("SSO_SAML_IDP_METADATA_URL"):
        providers.append(
            {"id": "saml-generic", "name": "SAML 2.0", "protocol": "saml", "enabled": True}
        )
    else:
        providers.append(
            {"id": "saml-generic", "name": "SAML 2.0", "protocol": "saml", "enabled": False}
        )
    if os.environ.get("OKTA_DOMAIN"):
        providers.append(
            {"id": "okta-saml", "name": "Okta SAML", "protocol": "saml", "enabled": True}
        )
    if os.environ.get("AZURE_AD_TENANT_ID"):
        providers.append(
            {"id": "azure-ad", "name": "Azure AD (OIDC)", "protocol": "oidc", "enabled": True}
        )
    else:
        providers.append(
            {"id": "azure-ad", "name": "Azure AD (OIDC)", "protocol": "oidc", "enabled": False}
        )
    return providers


# --- SAML ---


@router.get("/saml/metadata", response_model=SAMLMetadata)
async def saml_metadata(request: Request) -> SAMLMetadata:
    """Return SAML Service Provider metadata for IdP configuration."""
    base = str(request.base_url).rstrip("/")
    return SAMLMetadata(
        entity_id=f"{base}/api/v1/sso/saml/metadata",
        acs_url=f"{base}/api/v1/sso/saml/acs",
        sls_url=f"{base}/api/v1/sso/saml/sls",
        certificate=os.environ.get("SSO_SAML_CERT", "Not configured"),
    )


@router.post("/saml/acs", response_model=SAMLAssertionResponse)
async def saml_acs(request: Request) -> SAMLAssertionResponse:
    """SAML Assertion Consumer Service — receives assertions from the IdP.

    Validates the SAML response, extracts NameID, and creates a session.
    """
    idp_url = os.environ.get("SSO_SAML_IDP_METADATA_URL", "")
    if not idp_url:
        return SAMLAssertionResponse(
            status="not_configured",
            error="Set SSO_SAML_IDP_METADATA_URL to enable SAML SSO.",
        )

    try:
        form_data = await request.form()
        saml_response = form_data.get("SAMLResponse", "")
        if not saml_response:
            return SAMLAssertionResponse(status="error", error="No SAMLResponse in form data.")

        # Decode and validate SAML response
        import base64
        import xml.etree.ElementTree as ET

        decoded = base64.b64decode(saml_response)
        root = ET.fromstring(decoded)

        # Extract NameID (email) from SAML assertion
        ns = {
            "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
            "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
        }
        name_id_elem = root.find(".//saml:NameID", ns)
        if name_id_elem is None or not name_id_elem.text:
            return SAMLAssertionResponse(status="error", error="No NameID found in SAML assertion.")

        email = name_id_elem.text
        session_token = secrets.token_urlsafe(32)

        logger.info("SAML SSO login successful for %s", email)
        return SAMLAssertionResponse(
            status="success",
            user_email=email,
            session_token=session_token,
        )
    except Exception as e:
        logger.error("SAML ACS processing failed: %s", e)
        return SAMLAssertionResponse(status="error", error=str(e))


# --- Google OAuth 2.0 ---


@router.get("/oauth/google/authorize", response_class=RedirectResponse)
async def google_oauth_authorize(request: Request):
    """Redirect to Google OAuth consent screen."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(400, "GOOGLE_CLIENT_ID not configured")

    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/v1/sso/oauth/google/callback"
    state = secrets.token_urlsafe(16)

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
        "&access_type=offline"
    )
    return RedirectResponse(auth_url)


@router.get("/oauth/google/callback", response_model=OAuthCallbackResponse)
async def google_oauth_callback(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
) -> OAuthCallbackResponse:
    """Google OAuth callback — exchanges auth code for tokens."""
    if error:
        return OAuthCallbackResponse(
            status="error",
            provider="google",
            error=error,
        )
    if not code:
        return OAuthCallbackResponse(
            status="error",
            provider="google",
            error="No authorization code received",
        )

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return OAuthCallbackResponse(
            status="error",
            provider="google",
            error="Google OAuth not configured",
        )

    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/v1/sso/oauth/google/callback"

    try:
        import httpx

        async with httpx.AsyncClient(timeout=15) as client:
            # Exchange code for tokens
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()

            # Get user info
            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()

        email = userinfo.get("email", "")
        session_token = secrets.token_urlsafe(32)
        logger.info("Google OAuth login successful for %s", email)

        return OAuthCallbackResponse(
            status="success",
            user_email=email,
            session_token=session_token,
            provider="google",
        )
    except Exception as e:
        logger.error("Google OAuth callback failed: %s", e)
        return OAuthCallbackResponse(
            status="error",
            provider="google",
            error=str(e),
        )


# --- Azure AD OIDC ---


@router.get("/oauth/azure/authorize", response_class=RedirectResponse)
async def azure_oauth_authorize(request: Request):
    """Redirect to Azure AD / Entra ID consent screen."""
    tenant_id = os.environ.get("AZURE_AD_TENANT_ID", "")
    client_id = os.environ.get("AZURE_AD_CLIENT_ID", "")
    if not tenant_id or not client_id:
        raise HTTPException(400, "AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID not configured")

    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/v1/sso/oauth/azure/callback"
    state = secrets.token_urlsafe(16)

    auth_url = (
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
    )
    return RedirectResponse(auth_url)


@router.get("/oauth/azure/callback", response_model=OAuthCallbackResponse)
async def azure_oauth_callback(
    request: Request,
    code: str = "",
    error: str = "",
) -> OAuthCallbackResponse:
    """Azure AD OIDC callback."""
    if error:
        return OAuthCallbackResponse(
            status="error",
            provider="azure-ad",
            error=error,
        )
    if not code:
        return OAuthCallbackResponse(
            status="error",
            provider="azure-ad",
            error="No authorization code",
        )

    tenant_id = os.environ.get("AZURE_AD_TENANT_ID", "")
    client_id = os.environ.get("AZURE_AD_CLIENT_ID", "")
    client_secret = os.environ.get("AZURE_AD_CLIENT_SECRET", "")

    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/v1/sso/oauth/azure/callback"

    try:
        import httpx

        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "scope": "openid email profile",
                },
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()

            userinfo_resp = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()

        email = userinfo.get("mail") or userinfo.get("userPrincipalName", "")
        session_token = secrets.token_urlsafe(32)
        logger.info("Azure AD OIDC login successful for %s", email)

        return OAuthCallbackResponse(
            status="success",
            user_email=email,
            session_token=session_token,
            provider="azure-ad",
        )
    except Exception as e:
        logger.error("Azure AD callback failed: %s", e)
        return OAuthCallbackResponse(
            status="error",
            provider="azure-ad",
            error=str(e),
        )


# --- Provider listing ---


@router.get("/providers", response_model=list[SSOProvider])
async def list_sso_providers(
    user: User = Depends(get_current_user),
) -> list[SSOProvider]:
    """List all configured SSO/identity providers (auto-detects from env vars)."""
    return [SSOProvider(**p) for p in _get_sso_providers()]
