from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import hash_password


@pytest.fixture
def user_factory(db_session: Session) -> Callable[..., User]:
    def _create_user(
        *,
        email: str = "user@example.com",
        password: str = "s3cret-pass",
        first_name: str = "Ada",
        last_name: str = "Lovelace",
        role: UserRole = UserRole.TEAM_MEMBER,
    ) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user
