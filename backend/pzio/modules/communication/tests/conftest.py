from collections.abc import Callable
from pathlib import Path
import io

import pytest
from sqlalchemy.orm import Session

from pzio.config import settings
from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import create_access_token, hash_password
from pzio.modules.communication import service
from pzio.modules.communication.models import Attachment, Comment
from pzio.modules.communication.schemas import CommentCreate


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


@pytest.fixture
def auth_headers() -> Callable[[User], dict[str, str]]:
    def _make_headers(user: User) -> dict[str, str]:
        token, _ = create_access_token(user.user_id, user.role)
        return {"Authorization": f"Bearer {token}"}

    return _make_headers


@pytest.fixture
def upload_dir(tmp_path, monkeypatch) -> Path:
    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(upload_root))
    return upload_root


@pytest.fixture
def comment_factory(db_session: Session) -> Callable[..., Comment]:
    def _create_comment(*, task_id: int, author_id: int, content: str) -> Comment:
        return service.create_comment(
            db_session,
            task_id,
            author_id,
            CommentCreate(content=content),
        )

    return _create_comment


@pytest.fixture
def attachment_factory(
    db_session: Session,
    upload_dir: Path,
) -> Callable[..., Attachment]:
    def _save_attachment(
        *,
        task_id: int,
        uploader_id: int,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> Attachment:
        file_obj = io.BytesIO(data)
        return service.save_attachment(
            db_session,
            task_id=task_id,
            uploader_id=uploader_id,
            filename=filename,
            content_type=content_type,
            file_obj=file_obj,
        )

    return _save_attachment
