from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from pzio.db import get_db
from pzio.modules.auth.models import User
from pzio.modules.communication import service
from pzio.modules.communication.deps import get_current_user
from pzio.modules.communication.schemas import (
    AttachmentRead,
    CommentCreate,
    CommentRead,
    CommentUpdate,
)

router = APIRouter(tags=["Communication"])


@router.post(
    "/api/tasks/{task_id}/comments",
    response_model=CommentRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task",
    description="Creates a new comment on the specified task. "
    "The system sends an e-mail notification (SMTP) to observers.",
    responses={
        201: {"description": "Comment created"},
        400: {"description": "Validation error"},
        401: {"description": "Missing or invalid token"},
    },
)
def add_comment(
    task_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentRead:
    comment = service.create_comment(db, task_id, current_user.user_id, payload)
    # TODO: SMTP
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
    },
)
def get_comments(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CommentRead]:
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
        403: {"description": "Not the comment author"},
        404: {"description": "Comment not found"},
    },
)
def edit_comment(
    comment_id: int,
    payload: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentRead:
    try:
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
        403: {"description": "Not the comment author"},
        404: {"description": "Comment not found"},
    },
)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
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
    "Request must use `multipart/form-data`.",
    responses={
        201: {"description": "Attachment created"},
        401: {"description": "Missing or invalid token"},
    },
)
def upload_attachment(
    task_id: int,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttachmentRead:
    attachment = service.save_attachment(
        db,
        task_id=task_id,
        uploader_id=current_user.user_id,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        file_obj=file.file,
    )
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
    },
)
def list_attachments(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AttachmentRead]:
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
        404: {"description": "Attachment not found"},
    },
)
def download_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        attachment = service.get_attachment(db, attachment_id)
    except service.AttachmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    return FileResponse(
        path=attachment.file_path,
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
        403: {"description": "Not the uploader"},
        404: {"description": "Attachment not found"},
    },
)
def delete_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        service.delete_attachment(db, attachment_id, current_user.user_id)
    except service.AttachmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    except service.NotOwnerError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader can delete this attachment")
