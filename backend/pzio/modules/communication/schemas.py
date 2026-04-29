from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

COMMENT_CONTENT_MAX_LENGTH = 10000


class CommentCreate(BaseModel):
    """Body for POST /api/tasks/{id}/comments"""

    content: str = Field(min_length=1, max_length=COMMENT_CONTENT_MAX_LENGTH)


class CommentUpdate(BaseModel):
    """Body for PATCH /api/comments/{id}"""

    content: str = Field(min_length=1, max_length=COMMENT_CONTENT_MAX_LENGTH)


class CommentRead(BaseModel):
    """Public comment representation."""

    comment_id: int = Field(serialization_alias="commentId")
    task_id: int = Field(serialization_alias="taskId")
    author_id: int = Field(serialization_alias="authorId")
    content: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AttachmentRead(BaseModel):
    """Public attachment representation (excludes internal file_path)."""

    attachment_id: int = Field(serialization_alias="attachmentId")
    task_id: int = Field(serialization_alias="taskId")
    uploader_id: int = Field(serialization_alias="uploaderId")
    filename: str
    content_type: str = Field(serialization_alias="contentType")
    file_size: int = Field(serialization_alias="fileSize")
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
