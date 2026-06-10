import io
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from pzio.modules.communication import service
from pzio.modules.communication.schemas import CommentCreate, CommentUpdate


def _create_comment(db_session: Session, task_id: int, author_id: int, content: str):
    return service.create_comment(
        db_session,
        task_id,
        author_id,
        CommentCreate(content=content),
    )


def _save_attachment(
    db_session: Session,
    *,
    task_id: int,
    uploader_id: int,
    filename: str,
    content_type: str,
    data: bytes,
):
    file_obj = io.BytesIO(data)
    return service.save_attachment(
        db_session,
        task_id=task_id,
        uploader_id=uploader_id,
        filename=filename,
        content_type=content_type,
        file_obj=file_obj,
    )


def test_create_list_get_comment(db_session: Session, user_factory) -> None:
    user = user_factory()
    first = _create_comment(db_session, 1, user.user_id, "First")
    second = _create_comment(db_session, 1, user.user_id, "Second")
    _create_comment(db_session, 2, user.user_id, "Other task")

    comments = service.list_comments(db_session, 1)
    ids = {comment.comment_id for comment in comments}

    assert ids == {first.comment_id, second.comment_id}
    assert service.get_comment(db_session, first.comment_id).comment_id == first.comment_id


def test_get_comment_not_found(db_session: Session) -> None:
    with pytest.raises(service.CommentNotFoundError):
        service.get_comment(db_session, 999)


def test_create_comment_nonexistent_task(db_session: Session, user_factory) -> None:
    user = user_factory()

    with pytest.raises(service.TaskNotFoundError):
        _create_comment(db_session, 999999, user.user_id, "Orphan")

    assert service.list_comments(db_session, 999999) == []


def test_save_attachment_nonexistent_task(
    db_session: Session, user_factory, upload_dir: Path
) -> None:
    user = user_factory()

    with pytest.raises(service.TaskNotFoundError):
        _save_attachment(
            db_session,
            task_id=999999,
            uploader_id=user.user_id,
            filename="orphan.txt",
            content_type="text/plain",
            data=b"orphan",
        )

    assert service.list_attachments(db_session, 999999) == []
    assert not upload_dir.exists()


def test_update_comment_success(db_session: Session, user_factory) -> None:
    user = user_factory()
    comment = _create_comment(db_session, 1, user.user_id, "Old")

    updated = service.update_comment(
        db_session,
        comment.comment_id,
        user.user_id,
        CommentUpdate(content="New"),
    )

    assert updated.content == "New"
    assert updated.updated_at is not None


def test_update_comment_not_owner(db_session: Session, user_factory) -> None:
    owner = user_factory(email="owner@example.com")
    other = user_factory(email="other@example.com")
    comment = _create_comment(db_session, 1, owner.user_id, "Hello")

    with pytest.raises(service.NotOwnerError):
        service.update_comment(
            db_session,
            comment.comment_id,
            other.user_id,
            CommentUpdate(content="Nope"),
        )


def test_delete_comment_success(db_session: Session, user_factory) -> None:
    user = user_factory()
    comment = _create_comment(db_session, 1, user.user_id, "To delete")

    service.delete_comment(db_session, comment.comment_id, user.user_id)

    with pytest.raises(service.CommentNotFoundError):
        service.get_comment(db_session, comment.comment_id)


def test_delete_comment_not_owner(db_session: Session, user_factory) -> None:
    owner = user_factory(email="owner2@example.com")
    other = user_factory(email="other2@example.com")
    comment = _create_comment(db_session, 1, owner.user_id, "Cannot delete")

    with pytest.raises(service.NotOwnerError):
        service.delete_comment(db_session, comment.comment_id, other.user_id)


def test_save_list_get_attachment(db_session: Session, user_factory, upload_dir: Path) -> None:
    user = user_factory()

    attachment = _save_attachment(
        db_session,
        task_id=1,
        uploader_id=user.user_id,
        filename="note.txt",
        content_type="",
        data=b"hello",
    )

    assert upload_dir.exists()
    assert Path(attachment.file_path).exists()
    assert attachment.file_size == 5
    assert attachment.content_type == "application/octet-stream"

    attachments = service.list_attachments(db_session, 1)
    assert [item.attachment_id for item in attachments] == [attachment.attachment_id]

    fetched = service.get_attachment(db_session, attachment.attachment_id)
    assert fetched.filename == "note.txt"


def test_list_attachments_filters_by_task(db_session: Session, user_factory, upload_dir: Path) -> None:
    user = user_factory()

    first = _save_attachment(
        db_session,
        task_id=1,
        uploader_id=user.user_id,
        filename="first.txt",
        content_type="text/plain",
        data=b"first",
    )
    _save_attachment(
        db_session,
        task_id=2,
        uploader_id=user.user_id,
        filename="second.txt",
        content_type="text/plain",
        data=b"second",
    )

    attachments = service.list_attachments(db_session, 1)
    assert [item.attachment_id for item in attachments] == [first.attachment_id]


def test_get_attachment_not_found(db_session: Session) -> None:
    with pytest.raises(service.AttachmentNotFoundError):
        service.get_attachment(db_session, 999)


def test_delete_attachment_removes_file_and_record(
    db_session: Session, user_factory, upload_dir: Path
) -> None:
    user = user_factory()
    attachment = _save_attachment(
        db_session,
        task_id=1,
        uploader_id=user.user_id,
        filename="file.bin",
        content_type="application/octet-stream",
        data=b"data",
    )

    service.delete_attachment(db_session, attachment.attachment_id, user.user_id)

    assert not Path(attachment.file_path).exists()
    with pytest.raises(service.AttachmentNotFoundError):
        service.get_attachment(db_session, attachment.attachment_id)


def test_delete_attachment_missing_file_is_ok(
    db_session: Session, user_factory, upload_dir: Path
) -> None:
    user = user_factory()
    attachment = _save_attachment(
        db_session,
        task_id=1,
        uploader_id=user.user_id,
        filename="file.bin",
        content_type="application/octet-stream",
        data=b"data",
    )

    Path(attachment.file_path).unlink()
    service.delete_attachment(db_session, attachment.attachment_id, user.user_id)

    with pytest.raises(service.AttachmentNotFoundError):
        service.get_attachment(db_session, attachment.attachment_id)


def test_delete_attachment_not_owner(db_session: Session, user_factory, upload_dir: Path) -> None:
    owner = user_factory(email="owner3@example.com")
    other = user_factory(email="other3@example.com")
    attachment = _save_attachment(
        db_session,
        task_id=1,
        uploader_id=owner.user_id,
        filename="file.bin",
        content_type="application/octet-stream",
        data=b"data",
    )

    with pytest.raises(service.NotOwnerError):
        service.delete_attachment(db_session, attachment.attachment_id, other.user_id)
