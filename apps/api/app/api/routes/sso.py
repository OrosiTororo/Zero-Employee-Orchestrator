"""SAML/SSO endpoints for enterprise single sign-on."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.models.user import User

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


_SSO_PROVIDERS: list[dict] = [
    {"id": "google-oauth", "name": "Google OAuth 2.0", "protocol": "oauth2", "enabled": True},
    {"id": "saml-generic", "name": "SAML 2.0 (Generic)", "protocol": "saml", "enabled": False},
    {"id": "okta-saml", "name": "Okta SAML", "protocol": "saml", "enabled": False},
    {"id": "azure-ad", "name": "Azure AD (OIDC)", "protocol": "oidc", "enabled": False},
]


@router.get("/saml/metadata", response_model=SAMLMetadata)
async def saml_metadata(request: Request) -> SAMLMetadata:
    """Return SAML Service Provider metadata for IdP configuration."""
    base = str(request.base_url).rstrip("/")
    return SAMLMetadata(
        entity_id=f"{base}/api/v1/sso/saml/metadata",
        acs_url=f"{base}/api/v1/sso/saml/acs",
        sls_url=f"{base}/api/v1/sso/saml/sls",
        certificate="Configure via SSO_SAML_CERT environment variable",
    )


@router.post("/saml/acs", response_model=SAMLAssertionResponse)
async def saml_acs(request: Request) -> SAMLAssertionResponse:
    """SAML Assertion Consumer Service — receives assertions from the IdP."""
    # Stub: in production, validate the SAML response XML, extract
    # NameID, check signature, and create/link the user session.
    return SAMLAssertionResponse(
        status="not_configured",
        error="SAML IdP not configured. Set SSO_SAML_IDP_METADATA_URL in environment.",
    )


@router.get("/providers", response_model=list[SSOProvider])
async def list_sso_providers(
    user: User = Depends(get_current_user),
) -> list[SSOProvider]:
    """List all configured SSO/identity providers."""
    return [SSOProvider(**p) for p in _SSO_PROVIDERS]
