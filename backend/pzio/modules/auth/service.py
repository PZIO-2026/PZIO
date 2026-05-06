import secrets
from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.schemas import (
    OAuthLoginRequest,
    PasswordResetConfirm,
    UserCreate,
    UserUpdate,
)
from pzio.modules.auth.security import (
    InvalidTokenError,
    create_reset_token,
    decode_reset_token,
    hash_password,
    verify_password,
)
from pzio.modules.communication.base import EmailService
from pzio.modules.auth.oauth import oauth


class EmailAlreadyExistsError(Exception):
    """Raised when registering an email that is already taken (→ 409)."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials don't match any active user (→ 401)."""


class UserNotFoundError(Exception):
    """Raised when a user is not found by ID (→ 404)."""


class InvalidResetTokenError(Exception):
    """Raised when a password reset token is invalid or expired (→ 400)."""


class OAuthProviderNotSupportedError(Exception):
    """Raised when an unsupported OAuth provider is requested (→ 400)."""


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, payload: UserCreate) -> User:
    """Register a new user. Raises EmailAlreadyExistsError on duplicate email."""
    if _get_user_by_email(db, payload.email) is not None:
        raise EmailAlreadyExistsError(payload.email)

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=UserRole.TEAM_MEMBER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Verify credentials. Raises InvalidCredentialsError on any mismatch."""
    user = _get_user_by_email(db, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user


def update_user_profile(db: Session, user: User, payload: UserUpdate) -> User:
    """Update the current user's profile."""
    update_data = payload.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_status(db: Session, user_id: int, is_active: bool) -> User:
    """Activate or deactivate a user account (Admin only)."""
    user = get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()
    
    user.is_active = is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_users_paginated(
    db: Session, 
    search: str | None = None, 
    is_active: bool | None = None, 
    sort_by: str | None = None,
    sort_direction: str | None = "desc",
    page: int = 1, 
    size: int = 50
) -> tuple[Sequence[User], int]:
    """Get a paginated list of users with optional filtering and sorting."""
    stmt = select(User)
    
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
            )
        )
        
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
        
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(total_stmt) or 0
    
    if sort_by:
        sort_columns = {
            "email": User.email,
            "firstName": User.first_name,
            "lastName": User.last_name,
            "isActive": User.is_active,
            "userId": User.user_id
        }
        column = sort_columns.get(sort_by, User.user_id)
        
        if sort_direction and sort_direction.lower() == "asc":
            stmt = stmt.order_by(column.asc())
        else:
            stmt = stmt.order_by(column.desc())
    else:
        stmt = stmt.order_by(User.user_id.desc())
    
    stmt = stmt.offset((page - 1) * size).limit(size)
    items = db.scalars(stmt).all()
    
    return items, total


def request_password_reset(db: Session, email: str, email_service: EmailService) -> None:
    """
    Generates a reset token and sends it via email.
    Always returns None to prevent email enumeration.
    """
    user = _get_user_by_email(db, email)
    if not user:
        return

    token = create_reset_token(user.email)
    
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    
    subject = "Resetowanie hasła w PZIO"
    body = (
        f"Cześć {user.first_name},\n\n"
        f"Otrzymaliśmy prośbę o zresetowanie Twojego hasła. Kliknij w poniższy link, aby ustawić nowe:\n"
        f"{reset_link}\n\n"
        "Link jest ważny przez 15 minut. Jeśli to nie Ty, zignoruj tę wiadomość."
    )
    
    email_service.send_email(to=user.email, subject=subject, body=body)


def confirm_password_reset(db: Session, payload: PasswordResetConfirm) -> None:
    """Verifies token and sets a new password for the user."""
    try:
        email = decode_reset_token(payload.token)
    except InvalidTokenError:
        raise InvalidResetTokenError()

    user = _get_user_by_email(db, email)
    if not user:
        raise UserNotFoundError()

    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()


async def authenticate_oauth(db: Session, payload: OAuthLoginRequest) -> User:
    """
    Verifying OAuth tokens directly with the provider using Authlib.
    """
    provider = payload.provider.lower()
    token = payload.oauth_token

    if provider == "google":
        try:
            resp = await oauth.google.get(
                "https://www.googleapis.com/oauth2/v3/userinfo", 
                token={"access_token": token}
            )
            resp.raise_for_status()
            data = resp.json()
            
            user_email = data.get("email")
            first_name = data.get("given_name", "Google")
            last_name = data.get("family_name", "User")
        except Exception:
            raise InvalidCredentialsError()

    elif provider == "github":
        try:
            resp = await oauth.github.get(
                "user/emails", 
                token={"access_token": token}
            )
            resp.raise_for_status()
            emails = resp.json()
            
            user_email = next((e["email"] for e in emails if e.get("primary")), None)
            first_name = "GitHub"
            last_name = "User"
            if not user_email:
                raise InvalidCredentialsError()
        except Exception:
            raise InvalidCredentialsError()
    else:
        raise OAuthProviderNotSupportedError(provider)

    user = _get_user_by_email(db, user_email)
    
    if not user:
        user = User(
            email=user_email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            first_name=first_name[:100],
            last_name=last_name[:100],
            role=UserRole.TEAM_MEMBER,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return user