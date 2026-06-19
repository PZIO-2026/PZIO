from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

TASK_TYPE_NAME_MAX_LENGTH = 100


class TaskTypeCreate(BaseModel):
    """Body for `POST /api/admin/task-types` (SAD §4.5)."""

    name: str = Field(min_length=1, max_length=TASK_TYPE_NAME_MAX_LENGTH)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"example": {"name": "Epic"}},
    )


class TaskTypeRead(BaseModel):
    """Public dictionary entry returned by GET and POST /api/admin/task-types."""

    task_type_id: int = Field(serialization_alias="taskTypeId")
    name: str
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "taskTypeId": 3,
                "name": "Epic",
                "createdAt": "2026-05-14T08:00:00Z",
            }
        },
    )


class BackupRead(BaseModel):
    """Response for `POST /api/admin/backups` (SAD §4.5).

    PDF specifies the response shape as `{backupId, timestamp, status}` —
    `timestamp` is read from the ORM column `created_at` via `validation_alias`.
    """

    backup_id: int = Field(serialization_alias="backupId")
    timestamp: datetime = Field(validation_alias="created_at")
    status: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "backupId": 12,
                "timestamp": "2026-05-14T03:00:00Z",
                "status": "completed",
            }
        },
    )


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

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "activityLogId": 87,
                "taskId": 123,
                "userId": 42,
                "action": "STATUS_CHANGE",
                "fieldName": "status",
                "oldValue": "ToDo",
                "newValue": "InProgress",
                "createdAt": "2026-05-14T13:15:00Z",
            }
        },
    )
