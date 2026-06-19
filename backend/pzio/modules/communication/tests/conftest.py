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
from pzio.modules.projects.models import Project, ProjectMember
from pzio.modules.tasks.models import WorkItem

SEED_PROJECT_ID = 1


@pytest.fixture(autouse=True)
def seed_project_with_tasks(db_session: Session) -> None:
    """Comments and attachments require an existing parent task in a project.

    Tests in this module reference task ids 1, 2 and 123, so create them up
    front (all in project 1) instead of repeating the setup in every test.
    """
    if db_session.get(Project, SEED_PROJECT_ID) is None:
        db_session.add(Project(project_id=SEED_PROJECT_ID, name="Communication tests"))
    for task_id in (1, 2, 123):
        if db_session.get(WorkItem, task_id) is None:
            db_session.add(
                WorkItem(
                    id=task_id,
                    project_id=SEED_PROJECT_ID,
                    title=f"Task {task_id}",
                    type="Task",
                    priority="Medium",
                )
            )
    db_session.commit()


@pytest.fixture
def task_factory(db_session: Session) -> Callable[..., WorkItem]:
    def _create_task(
        *,
        title: str = "Fix login bug",
        assignee_id: int | None = None,
        project_id: int = 1,
    ) -> WorkItem:
        task = WorkItem(
            project_id=project_id,
            title=title,
            type="Task",
            priority="Medium",
            assignee_id=assignee_id,
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task

    return _create_task


@pytest.fixture
def user_factory(db_session: Session) -> Callable[..., User]:
    def _create_user(
        *,
        email: str = "user@example.com",
        password: str = "s3cret-pass",
        first_name: str = "Ada",
        last_name: str = "Lovelace",
        avatar: str | None = None,
        role: UserRole = UserRole.TEAM_MEMBER,
        is_active: bool = True,
        project_member: bool = True,
    ) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            avatar=avatar,
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        if project_member:
            db_session.add(
                ProjectMember(
                    project_id=SEED_PROJECT_ID,
                    user_id=user.user_id,
                    roles=["developer"],
                )
            )
            db_session.commit()
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
