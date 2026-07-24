"""Auth-related DTOs."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    display_name: str
    setup_completed: bool = False


class OAuthLoginRequest(BaseModel):
    provider: Literal["google"]


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserRead(BaseModel):
    id: str
    email: str | None = None
    display_name: str
    role: str
    status: str
    auth_provider: str | None = None
    last_login_at: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleAuthorizeResponse(BaseModel):
    url: str
    state: str


class GooglePollRequest(BaseModel):
    state: str = Field(
        min_length=32,
        max_length=256,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class GooglePollPendingResponse(BaseModel):
    status: Literal["pending"]


class GooglePollFailedResponse(BaseModel):
    status: Literal["failed"]
    error: Literal["oauth_failed", "account_link_required", "not_configured"]


class GooglePollCompleteResponse(BaseModel):
    status: Literal["complete"]
    access_token: str
    user_id: str
    display_name: str
    setup_completed: bool = False


class LogoutResponse(BaseModel):
    status: str
    message: str


class MessageResponse(BaseModel):
    message: str


class PasswordResetRequestResponse(BaseModel):
    message: str
    reset_token: str | None = None


class AnonymousSessionResponse(BaseModel):
    access_token: str
    user_id: str
    company_id: str
    display_name: str
    is_anonymous: bool = True
    setup_completed: bool = False
    message: str


class LinkAccountResponse(BaseModel):
    access_token: str
    user_id: str
    display_name: str
    linked: bool = True
    message: str


class SetupStatusResponse(BaseModel):
    setup_completed: bool
