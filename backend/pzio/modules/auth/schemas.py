from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from pzio.modules.auth.models import UserRole

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
NAME_MAX_LENGTH = 100


class UserCreate(BaseModel):
    """Body for `POST /api/auth/register` (SAD §4.1)."""

    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    first_name: str = Field(alias="firstName", min_length=1, max_length=NAME_MAX_LENGTH)
    last_name: str = Field(alias="lastName", min_length=1, max_length=NAME_MAX_LENGTH)

    model_config = ConfigDict(populate_by_name=True)


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LoginRequest(BaseModel):
    """Body for `POST /api/auth/login` (SAD §4.1)."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class TokenResponse(BaseModel):
    """Response for login / oauth (SAD §4.1)."""

    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(default="bearer", serialization_alias="tokenType")
    expires_in: int = Field(serialization_alias="expiresIn")

class UserUpdate(BaseModel):
    """Body for `PATCH /api/users/me`. All fields are optional."""

    first_name: str | None = Field(default=None, alias="firstName", min_length=1, max_length=NAME_MAX_LENGTH)
    last_name: str | None = Field(default=None, alias="lastName", min_length=1, max_length=NAME_MAX_LENGTH)
    avatar: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(populate_by_name=True)


class UserStatusUpdate(BaseModel):
    """Body for `PATCH /api/users/{id}/status` (Admin only)."""

    is_active: bool = Field(alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class PaginatedUserResponse(BaseModel):
    """Response for `GET /api/users` (Admin only)."""

    items: list[UserRead]
    total: int
    page: int
    size: int