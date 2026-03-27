"""Auth-related DTOs."""

from pydantic import BaseModel, EmailStr


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


class OAuthLoginRequest(BaseModel):
    provider: str
    code: str
    redirect_uri: str | None = None


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
