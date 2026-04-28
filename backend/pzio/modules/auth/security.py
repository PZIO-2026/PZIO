from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from pzio.config import settings
from pzio.modules.auth.models import UserRole


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be decoded or has expired."""


def hash_password(plain_password: str) -> str:
    """bcrypt hash (NFR04). Returns the encoded hash as utf-8 string."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Constant-time password check. Returns False on any decoding error."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int, role: UserRole) -> tuple[str, int]:
    """Issue a signed JWT. Returns (token, expires_in_seconds)."""
    expires_in = settings.jwt_expires_min * 60
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """Verify signature + expiry. Raises InvalidTokenError on any failure."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
