from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

COMMENT_CONTENT_MAX_LENGTH = 10000


class CommentCreate(BaseModel):
    """Body for POST /api/tasks/{id}/comments"""

    content: str = Field(min_length=1, max_length=COMMENT_CONTENT_MAX_LENGTH)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Pushed the fix to the feature branch — please review when you get a chance.",
            }
        }
    )


class CommentUpdate(BaseModel):
    """Body for PATCH /api/comments/{id}"""

    content: str = Field(min_length=1, max_length=COMMENT_CONTENT_MAX_LENGTH)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Edited: pushed the fix and rebased onto master.",
            }
        }
    )


class CommentRead(BaseModel):
    """Public comment representation."""

    comment_id: int = Field(serialization_alias="commentId")
    task_id: int = Field(serialization_alias="taskId")
    author_id: int = Field(serialization_alias="authorId")
    content: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "commentId": 17,
                "taskId": 123,
                "authorId": 42,
                "content": "Pushed the fix to the feature branch — please review when you get a chance.",
                "createdAt": "2026-05-14T17:30:00Z",
                "updatedAt": None,
            }
        },
    )


class AttachmentRead(BaseModel):
    """Public attachment representation (excludes internal file_path)."""

    attachment_id: int = Field(serialization_alias="attachmentId")
    task_id: int = Field(serialization_alias="taskId")
    uploader_id: int = Field(serialization_alias="uploaderId")
    filename: str
    content_type: str = Field(serialization_alias="contentType")
    file_size: int = Field(serialization_alias="fileSize")
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "attachmentId": 4,
                "taskId": 123,
                "uploaderId": 42,
                "filename": "auth-flow.png",
                "contentType": "image/png",
                "fileSize": 184302,
                "createdAt": "2026-05-14T18:00:00Z",
            }
        },
    )
