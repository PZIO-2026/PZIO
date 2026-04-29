from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import create_access_token, hash_password


def seed_user(
    db: Session,
    *,
    email: str,
    password: str = "s3cret-pass",
    role: UserRole = UserRole.TEAM_MEMBER,
    is_active: bool = True,
) -> User:
    """Insert a user and return the persisted row. Mirrors auth tests' helper."""
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name="Test",
        last_name="User",
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict[str, str]:
    """Build an `Authorization: Bearer ...` header for the given user."""
    token, _ = create_access_token(user.user_id, user.role)
    return {"Authorization": f"Bearer {token}"}
