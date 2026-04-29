import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from pzio.modules.communication.models import Attachment, Comment
from pzio.modules.communication.schemas import CommentCreate, CommentUpdate

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "uploads"))


class CommentNotFoundError(Exception):
    """Raised when a comment ID does not exist (404)."""


class AttachmentNotFoundError(Exception):
    """Raised when an attachment ID does not exist (404)."""


class NotOwnerError(Exception):
    """Raised when a user tries to modify a resource they don't own (403)."""


def create_comment(db: Session, task_id: int, author_id: int, payload: CommentCreate) -> Comment:
    """Add a new comment to a task."""
    comment = Comment(
        task_id=task_id,
        author_id=author_id,
        content=payload.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, task_id: int) -> list[Comment]:
    """Return all comments for a task, ordered chronologically."""
    stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at.asc())
    return list(db.execute(stmt).scalars().all())


def get_comment(db: Session, comment_id: int) -> Comment:
    """Retrieve a single comment by ID. Raises CommentNotFoundError if missing."""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise CommentNotFoundError(comment_id)
    return comment


def update_comment(db: Session, comment_id: int, user_id: int, payload: CommentUpdate) -> Comment:
    """Edit comment content. Only the author may edit. Raises NotOwnerError / CommentNotFoundError."""
    comment = get_comment(db, comment_id)
    if comment.author_id != user_id:
        raise NotOwnerError()

    comment.content = payload.content
    comment.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment_id: int, user_id: int) -> None:
    """Delete a comment. Only the author may delete. Raises NotOwnerError / CommentNotFoundError."""
    comment = get_comment(db, comment_id)
    if comment.author_id != user_id:
        raise NotOwnerError()

    db.delete(comment)
    db.commit()


def _ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def save_attachment(
    db: Session,
    task_id: int,
    uploader_id: int,
    filename: str,
    content_type: str,
    file_obj: object,
) -> Attachment:
    """Persist an uploaded file to disk and create a DB record.

    ``file_obj`` is expected to behave like ``UploadFile.file`` (a file-like
    object supporting ``.read()``).
    """
    upload_dir = _ensure_upload_dir()

    # Generate a unique on-disk name to avoid collisions, but keep the original extension.
    ext = Path(filename).suffix
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / stored_name

    # Write uploaded bytes to disk
    with open(dest, "wb") as out:
        shutil.copyfileobj(file_obj, out)

    file_size = dest.stat().st_size

    attachment = Attachment(
        task_id=task_id,
        uploader_id=uploader_id,
        filename=filename,
        content_type=content_type or "application/octet-stream",
        file_path=str(dest),
        file_size=file_size,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def list_attachments(db: Session, task_id: int) -> list[Attachment]:
    """Return all attachments for a task."""
    stmt = select(Attachment).where(Attachment.task_id == task_id).order_by(Attachment.created_at.asc())
    return list(db.execute(stmt).scalars().all())


def get_attachment(db: Session, attachment_id: int) -> Attachment:
    """Retrieve a single attachment by ID. Raises AttachmentNotFoundError if missing."""
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise AttachmentNotFoundError(attachment_id)
    return attachment


def delete_attachment(db: Session, attachment_id: int, user_id: int) -> None:
    """Delete an attachment record and its file on disk. Only the uploader may delete."""
    attachment = get_attachment(db, attachment_id)
    if attachment.uploader_id != user_id:
        raise NotOwnerError()

    try:
        os.remove(attachment.file_path)
    except FileNotFoundError:
        pass

    db.delete(attachment)
    db.commit()
