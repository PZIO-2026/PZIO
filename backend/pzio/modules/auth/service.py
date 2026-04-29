from sqlalchemy import select
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.schemas import UserCreate
from pzio.modules.auth.security import hash_password, verify_password


class EmailAlreadyExistsError(Exception):
    """Raised when registering an email that is already taken (→ 409)."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials don't match any active user (→ 401)."""


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


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
