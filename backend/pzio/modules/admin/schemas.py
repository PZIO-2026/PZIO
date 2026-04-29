from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

TASK_TYPE_NAME_MAX_LENGTH = 100


class TaskTypeCreate(BaseModel):
    """Body for `POST /api/admin/task-types` (SAD §4.5)."""

    name: str = Field(min_length=1, max_length=TASK_TYPE_NAME_MAX_LENGTH)

    model_config = ConfigDict(str_strip_whitespace=True)


class TaskTypeRead(BaseModel):
    """Public dictionary entry returned by /api/task-types and /api/admin/task-types."""

    task_type_id: int = Field(serialization_alias="taskTypeId")
    name: str
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BackupRead(BaseModel):
    """Response for `POST /api/admin/backups` (SAD §4.5).

    PDF specifies the response shape as `{backupId, timestamp, status}` —
    `timestamp` is read from the ORM column `created_at` via `validation_alias`.
    """

    backup_id: int = Field(serialization_alias="backupId")
    timestamp: datetime = Field(validation_alias="created_at")
    status: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ActivityLogRead(BaseModel):
    """Single audit entry returned by `GET /api/tasks/{id}/history` (SAD §4.5)."""

    activity_log_id: int = Field(serialization_alias="activityLogId")
    task_id: int = Field(serialization_alias="taskId")
    user_id: int = Field(serialization_alias="userId")
    action: str
    field_name: str | None = Field(default=None, serialization_alias="fieldName")
    old_value: str | None = Field(default=None, serialization_alias="oldValue")
    new_value: str | None = Field(default=None, serialization_alias="newValue")
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
