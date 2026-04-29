from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.schemas import UserCreate, UserUpdate
from pzio.modules.auth.security import hash_password, verify_password


class EmailAlreadyExistsError(Exception):
    """Raised when registering an email that is already taken (→ 409)."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials don't match any active user (→ 401)."""

class UserNotFoundError(Exception):
    """Raised when a user is not found by ID (→ 404)."""


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
    """Verify credentials. Raises InvalidCredentialsError on any mismatch.

    The same exception is raised whether the email is unknown or the password is
    wrong — this prevents user enumeration via response timing/messages.
    """
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
    page: int = 1, 
    size: int = 50
) -> tuple[Sequence[User], int]:
    """Get a paginated list of users with optional filtering."""
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
    
    stmt = stmt.order_by(User.user_id.desc()).offset((page - 1) * size).limit(size)
    items = db.scalars(stmt).all()
    
    return items, total