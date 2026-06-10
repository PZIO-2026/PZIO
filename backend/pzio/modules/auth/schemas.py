from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from pzio.modules.auth.models import UserRole

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
NAME_MAX_LENGTH = 100


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    first_name: str = Field(alias="firstName", min_length=1, max_length=NAME_MAX_LENGTH)
    last_name: str = Field(alias="lastName", min_length=1, max_length=NAME_MAX_LENGTH)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "alice@example.com",
                "password": "correct-horse-battery-staple",
                "firstName": "Alice",
                "lastName": "Smith",
            }
        },
    )

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: Any) -> Any:
        return v.lower() if isinstance(v, str) else v


class UserRead(BaseModel):
    """Public user representation. Never includes `passwordHash` (NFR04)."""

    user_id: int = Field(serialization_alias="userId")
    email: EmailStr
    first_name: str = Field(serialization_alias="firstName")
    last_name: str = Field(serialization_alias="lastName")
    avatar: str | None = None
    role: UserRole
    is_active: bool = Field(serialization_alias="isActive")
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "userId": 42,
                "email": "alice@example.com",
                "firstName": "Alice",
                "lastName": "Smith",
                "avatar": None,
                "role": "TeamMember",
                "isActive": True,
                "createdAt": "2026-05-14T09:30:00Z",
            }
        },
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "alice@example.com",
                "password": "correct-horse-battery-staple",
            }
        }
    )

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: Any) -> Any:
        return v.lower() if isinstance(v, str) else v


class TokenResponse(BaseModel):
    """Response for login / oauth (SAD §4.1)."""

    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(default="bearer", serialization_alias="tokenType")
    expires_in: int = Field(serialization_alias="expiresIn")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsInJvbGUiOiJUZWFtTWVtYmVyIiwiZXhwIjoxNzc4Nzk1NDIwfQ.signature",
                "tokenType": "bearer",
                "expiresIn": 3600,
            }
        },
    )

class UserUpdate(BaseModel):
    """Body for `PATCH /api/users/me`. All fields are optional."""

    first_name: str | None = Field(default=None, alias="firstName", min_length=1, max_length=NAME_MAX_LENGTH)
    last_name: str | None = Field(default=None, alias="lastName", min_length=1, max_length=NAME_MAX_LENGTH)
    avatar: str | None = Field(default=None, max_length=255)

    @field_validator("avatar", mode="before")
    @classmethod
    def _validate_avatar(cls, value: object) -> str | None:
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            raise ValueError("avatar must be a string URL")
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("avatar must be a valid http(s) URL")
        return value

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "firstName": "Alice",
                "lastName": "Smith-Jones",
                "avatar": "https://cdn.example.com/avatars/42.png",
            }
        },
    )


class UserStatusUpdate(BaseModel):
    """Body for `PATCH /api/users/{id}/status` (Admin only)."""

    is_active: bool = Field(alias="isActive")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"isActive": False}},
    )


class UserRoleUpdate(BaseModel):
    """Body for `PATCH /api/users/{id}/role` (Admin only)."""

    role: UserRole

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"role": "Manager"}},
    )


class PaginatedUserResponse(BaseModel):
    """Response for `GET /api/users` (Admin only)."""

    items: list[UserRead]
    total: int
    page: int
    size: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "userId": 42,
                        "email": "alice@example.com",
                        "firstName": "Alice",
                        "lastName": "Smith",
                        "avatar": None,
                        "role": "TeamMember",
                        "isActive": True,
                        "createdAt": "2026-05-14T09:30:00Z",
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 20,
            }
        }
    )


class PasswordResetRequest(BaseModel):
    email: EmailStr

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "alice@example.com"}}
    )

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: Any) -> Any:
        return v.lower() if isinstance(v, str) else v


class PasswordResetConfirm(BaseModel):
    """Body for POST /api/auth/reset-password/confirm"""
    token: str
    new_password: str = Field(alias="newPassword", min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "token": "8c1b0f7e-3d2a-4b9a-9e6f-1a2b3c4d5e6f",
                "newPassword": "new-correct-horse-battery-staple",
            }
        },
    )


class OAuthLoginRequest(BaseModel):
    """Body for POST /api/auth/oauth"""
    provider: str = Field(description="e.g., 'google' or 'github'")
    oauth_token: str = Field(alias="oauthToken")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "provider": "google",
                "oauthToken": "ya29.A0AfH6SMB...redacted...",
            }
        },
    )


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Password reset email sent."}}
    )



class ChangeEmailRequest(BaseModel):
    """Body for PATCH /api/users/me/email"""
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: Any) -> Any:
        return v.lower() if isinstance(v, str) else v


class ChangePasswordRequest(BaseModel):
    """Body for POST /api/users/me/change-password"""
    old_password: str = Field(alias="oldPassword")
    new_password: str = Field(alias="newPassword", min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    model_config = ConfigDict(populate_by_name=True)