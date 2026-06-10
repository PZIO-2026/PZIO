import secrets
import httpx
from typing import Sequence

from sqlalchemy import func, or_, select, text
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
from pzio.config import settings


class EmailAlreadyExistsError(Exception):
    """Raised when registering an email that is already taken (→ 409)."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials don't match any user (→ 401)."""


class AccountDeactivatedError(Exception):
    """Raised when valid credentials belong to a deactivated account (→ 403)."""


class UserNotFoundError(Exception):
    """Raised when a user is not found by ID (→ 404)."""


class InvalidResetTokenError(Exception):
    """Raised when a password reset token is invalid or expired (→ 400)."""


class OAuthProviderNotSupportedError(Exception):
    """Raised when an unsupported OAuth provider is requested (→ 400)."""


class SelfRoleChangeError(Exception):
    """Raised when an admin attempts to change their own role (→ 400)."""


# Arbitrary 64-bit constant identifying the "first-admin bootstrap" critical
# section for PostgreSQL's `pg_advisory_xact_lock`. Any int fits as long as it
# is unique to this purpose within the application.
_ADMIN_BOOTSTRAP_LOCK_KEY = 0x707A696F61646D31  # "pzioadm1" as ASCII bytes


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def _admin_exists(db: Session) -> bool:
    """Check whether any user with the Administrator role exists in the database."""
    return db.execute(
        select(User.user_id).where(User.role == UserRole.ADMINISTRATOR).limit(1)
    ).first() is not None


def _pick_role_for_new_user(db: Session) -> UserRole:
    """Return the role for a freshly registered user (zero-config bootstrap).

    The first user to register on an empty database becomes Administrator;
    every subsequent registration defaults to TeamMember. To prevent two
    concurrent first-time registrations from both observing "no admin yet"
    and both being promoted, on PostgreSQL we acquire a transaction-scoped
    advisory lock around the check. SQLite already serialises writes via the
    database-level lock, so no extra synchronisation is required there.
    """
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:k)"),
            {"k": _ADMIN_BOOTSTRAP_LOCK_KEY},
        )
    return UserRole.ADMINISTRATOR if not _admin_exists(db) else UserRole.TEAM_MEMBER


def create_user(db: Session, payload: UserCreate) -> User:
    """Register a new user. Raises EmailAlreadyExistsError on duplicate email.

    Zero-config bootstrap: when no Administrator exists yet, the newly created
    account is promoted to Administrator. Otherwise the default role is TeamMember.
    """
    if _get_user_by_email(db, payload.email) is not None:
        raise EmailAlreadyExistsError(payload.email)

    role = _pick_role_for_new_user(db)

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Verify credentials.

    Raises InvalidCredentialsError when the email is unknown or the password is
    wrong, and AccountDeactivatedError only once the credentials are confirmed
    valid but the account is deactivated. Checking the password first means we
    never reveal that an account is deactivated to someone who can't already
    authenticate as that user.
    """
    user = _get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    if not user.is_active:
        raise AccountDeactivatedError()
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


def update_user_role(
    db: Session,
    *,
    target_user_id: int,
    new_role: UserRole,
    current_user: User,
) -> User:
    """Change another user's role (Admin only).

    Raises SelfRoleChangeError when the admin tries to change their own role,
    UserNotFoundError when the target user does not exist.
    """
    if target_user_id == current_user.user_id:
        raise SelfRoleChangeError()

    target = get_user_by_id(db, target_user_id)
    if target is None:
        raise UserNotFoundError()

    target.role = new_role
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


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
    
    reset_link = f"{settings.frontend_url}/reset-password?token={token}"
    
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
            fallback_name = user_email.split("@")[0] if user_email else "User"
            first_name = data.get("given_name") or fallback_name
            last_name = data.get("family_name") or fallback_name
        except Exception:
            raise InvalidCredentialsError()

    elif provider == "github":
        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": settings.github_client_id,
                        "client_secret": settings.github_client_secret,
                        "code": token, 
                    },
                    headers={"Accept": "application/json"}
                )
                
                token_resp.raise_for_status()
                data = token_resp.json()

            if data.get("error"):
                raise InvalidCredentialsError()

            access_token = data.get("access_token")
            if not access_token:
                raise InvalidCredentialsError()

            resp = await oauth.github.get(
                "user/emails", 
                token={"access_token": access_token}
            )
            resp.raise_for_status()
            emails = resp.json()
            
            user_email = next((e["email"] for e in emails if e.get("primary")), None)
            if not user_email:
                raise InvalidCredentialsError()

            fallback_name = user_email.split("@")[0]
            
            try:
                resp_profile = await oauth.github.get("user", token={"access_token": access_token})
                resp_profile.raise_for_status()
                profile_data = resp_profile.json()
                full_name = profile_data.get("name")
            except Exception:
                full_name = None

            if full_name:
                name_parts = full_name.split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else fallback_name
            else:
                first_name = fallback_name
                last_name = fallback_name
                
        except (httpx.HTTPStatusError, httpx.RequestError):
            raise InvalidCredentialsError()
        except Exception: 
            raise InvalidCredentialsError()
    else:
        raise OAuthProviderNotSupportedError(provider)

    user = _get_user_by_email(db, user_email)

    if not user:
        # Same zero-config bootstrap as `create_user`: first user becomes Administrator.
        role = _pick_role_for_new_user(db)
        user = User(
            email=user_email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            first_name=first_name[:100],
            last_name=last_name[:100],
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise AccountDeactivatedError()

    return user