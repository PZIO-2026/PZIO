from fnmatch import fnmatch
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from pzio.config import settings
from pzio.db import get_db
from pzio.path_params import PathId
from pzio.modules.auth.models import User
from pzio.modules.communication import service
from pzio.modules.communication.base import EmailService
from pzio.modules.communication.deps import get_current_user, provide_email_service
from pzio.modules.communication.schemas import (
    AttachmentRead,
    CommentCreate,
    CommentRead,
    CommentUpdate,
)
from pzio.modules.projects.services import require_project_member
from pzio.modules.tasks.service import get_work_item
from pzio.modules.tasks import service as tasks_service
from pzio.config import settings

router = APIRouter(tags=["Communication"])

# File upload security constraints
MAX_FILE_SIZE = settings.max_file_size
ALLOWED_MIME_TYPES = ["image/*", "application/pdf", "text/*", "application/json"]


def _is_mime_type_allowed(content_type: str | None) -> bool:
    """Check if content_type matches the whitelist of allowed MIME types."""
    if not content_type:
        return False
    for allowed in ALLOWED_MIME_TYPES:
        if fnmatch(content_type, allowed):
            return True
    return False


def _require_task_member(db: Session, task_id: int, user_id: int) -> None:
    """Ensure the task exists and the caller may access it.

    Raises 404 when the task does not exist (without leaking membership) and 403
    when the caller is not a member of the owning project. Administrators bypass
    the membership check inside require_project_member.
    """
    task = get_work_item(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    require_project_member(db, project_id=task.project_id, user_id=user_id)


@router.post(
    "/api/tasks/{task_id}/comments",
    response_model=CommentRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task",
    description="Creates a new comment on the specified task. "
    "The system sends an e-mail notification (SMTP) to the task assignee and prior commenters.",
    responses={
        201: {"description": "Comment created"},
        400: {"description": "Validation error"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Caller is not a member of the project"},
        404: {"description": "Task not found"},
    },
)
def add_comment(
    task_id: PathId,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(provide_email_service),
) -> CommentRead:
    _require_task_member(db, task_id, current_user.user_id)
    try:
        comment = service.create_comment(db, task_id, current_user.user_id, payload)
        task = tasks_service.get_work_item(db, task_id)
        assert task is not None
    except service.TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    recipients = service.get_comment_notification_recipients(
        db,
        task_id,
        current_user.user_id,
        task.assignee_id,
    )
    subject, body = service.build_comment_notification_message(
        task_id,
        task.title,
        current_user,
        payload.content,
    )
    service.send_comment_notifications(email_service, recipients, subject, body)

    return CommentRead.model_validate(comment)


@router.get(
    "/api/tasks/{task_id}/comments",
    response_model=list[CommentRead],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get comment history for a task",
    description="Returns all comments for the task in chronological order.",
    responses={
        200: {"description": "List of comments"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Caller is not a member of the project"},
        404: {"description": "Task not found"},
    },
)
def get_comments(
    task_id: PathId,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CommentRead]:
    _require_task_member(db, task_id, current_user.user_id)
    comments = service.list_comments(db, task_id)
    return [CommentRead.model_validate(c) for c in comments]


@router.patch(
    "/api/comments/{comment_id}",
    response_model=CommentRead,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Edit a comment",
    description="Updates the content of an existing comment. Only the author may edit.",
    responses={
        200: {"description": "Comment updated"},
        400: {"description": "Validation error"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not the comment author or not a member of the project"},
        404: {"description": "Comment not found"},
    },
)
def edit_comment(
    comment_id: PathId,
    payload: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentRead:
    try:
        comment = service.get_comment(db, comment_id)
        _require_task_member(db, comment.task_id, current_user.user_id)
        comment = service.update_comment(db, comment_id, current_user.user_id, payload)
    except service.CommentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    except service.NotOwnerError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can edit this comment")
    return CommentRead.model_validate(comment)


@router.delete(
    "/api/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    description="Removes a comment. Only the author may delete.",
    responses={
        204: {"description": "Comment deleted"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not the comment author or not a member of the project"},
        404: {"description": "Comment not found"},
    },
)
def delete_comment(
    comment_id: PathId,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        comment = service.get_comment(db, comment_id)
        _require_task_member(db, comment.task_id, current_user.user_id)
        service.delete_comment(db, comment_id, current_user.user_id)
    except service.CommentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    except service.NotOwnerError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can delete this comment")


@router.post(
    "/api/tasks/{task_id}/attachments",
    response_model=AttachmentRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an attachment",
    description="Uploads a file attachment to the specified task. "
    "Request must use `multipart/form-data`. Max file size: 10 MB. "
    "Allowed types: images, PDFs.",
    responses={
        201: {"description": "Attachment created"},
        400: {"description": "File too large or unsupported file type"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Caller is not a member of the project"},
        404: {"description": "Task not found"},
    },
)
def upload_attachment(
    task_id: PathId,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttachmentRead:
    _require_task_member(db, task_id, current_user.user_id)

    # Validate MIME type
    if not _is_mime_type_allowed(file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported types: {', '.join(ALLOWED_MIME_TYPES)}",
        )
    
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {max_mb:.0f} MB",
        )
    
    try:
        attachment = service.save_attachment(
            db,
            task_id=task_id,
            uploader_id=current_user.user_id,
            filename=file.filename or "unnamed",
            content_type=file.content_type,
            file_obj=file.file,
        )
    except service.TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return AttachmentRead.model_validate(attachment)


@router.get(
    "/api/tasks/{task_id}/attachments",
    response_model=list[AttachmentRead],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="List attachments for a task",
    description="Returns metadata for all attachments on the specified task.",
    responses={
        200: {"description": "List of attachments"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Caller is not a member of the project"},
        404: {"description": "Task not found"},
    },
)
def list_attachments(
    task_id: PathId,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AttachmentRead]:
    _require_task_member(db, task_id, current_user.user_id)
    attachments = service.list_attachments(db, task_id)
    return [AttachmentRead.model_validate(a) for a in attachments]


@router.get(
    "/api/attachments/{attachment_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download an attachment file",
    description="Returns the binary file stream (`application/octet-stream`).",
    responses={
        200: {"description": "File stream", "content": {"application/octet-stream": {}}},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Caller is not a member of the project"},
        404: {"description": "Attachment not found"},
    },
)
def download_attachment(
    attachment_id: PathId,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        attachment = service.get_attachment(db, attachment_id)
    except service.AttachmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    _require_task_member(db, attachment.task_id, current_user.user_id)

    file_path = Path(attachment.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found")

    return FileResponse(
        path=str(file_path),
        filename=attachment.filename,
        media_type=attachment.content_type,
    )


@router.delete(
    "/api/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an attachment",
    description="Removes the attachment record and its file from disk. Only the uploader may delete.",
    responses={
        204: {"description": "Attachment deleted"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Not the uploader or not a member of the project"},
        404: {"description": "Attachment not found"},
    },
)
def delete_attachment(
    attachment_id: PathId,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        attachment = service.get_attachment(db, attachment_id)
        _require_task_member(db, attachment.task_id, current_user.user_id)
        service.delete_attachment(db, attachment_id, current_user.user_id)
    except service.AttachmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    except service.NotOwnerError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader can delete this attachment")
