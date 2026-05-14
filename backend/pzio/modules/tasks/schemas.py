from datetime import datetime
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

TASK_TITLE_MAX_LENGTH = 255
TASK_DESCRIPTION_MAX_LENGTH = 5000
TASK_TYPE_MAX_LENGTH = 100
TASK_PRIORITY_MAX_LENGTH = 20


class TaskStatus(StrEnum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class WorkItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=TASK_TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=TASK_DESCRIPTION_MAX_LENGTH)
    type: str = Field(min_length=1, max_length=TASK_TYPE_MAX_LENGTH)
    priority: TaskPriority
    story_points: int | None = Field(None, ge=0, alias="storyPoints")
    parent_id: int | None = Field(None, gt=0, alias="parentId")
    assignee_id: int | None = Field(None, gt=0, alias="assigneeId")
    sprint_id: int | None = Field(None, gt=0, alias="sprintId")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class WorkItemCreate(WorkItemBase):
    """Body for POST /api/projects/{id}/tasks."""

    status: TaskStatus = TaskStatus.TODO

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "title": "Implement OAuth callback handler",
                "description": "Handle the redirect from Google and exchange the code for a JWT.",
                "type": "Task",
                "priority": "High",
                "storyPoints": 5,
                "status": "ToDo",
                "parentId": 100,
                "assigneeId": 42,
                "sprintId": 21,
            }
        },
    )


class WorkItemUpdate(BaseModel):
    """Body for PATCH /api/tasks/{id} - all fields optional."""

    title: str | None = Field(default=None, min_length=1, max_length=TASK_TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=TASK_DESCRIPTION_MAX_LENGTH)
    type: str | None = Field(default=None, min_length=1, max_length=TASK_TYPE_MAX_LENGTH)
    priority: TaskPriority | None = None
    story_points: int | None = Field(None, ge=0, alias="storyPoints")
    parent_id: int | None = Field(None, gt=0, alias="parentId")
    assignee_id: int | None = Field(None, gt=0, alias="assigneeId")
    sprint_id: int | None = Field(None, gt=0, alias="sprintId")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "priority": "Medium",
                "storyPoints": 3,
                "assigneeId": 88,
            }
        },
    )


class StatusUpdate(BaseModel):
    """Body for PATCH /api/tasks/{id}/status - Kanban column move."""

    status: TaskStatus

    model_config: ClassVar[ConfigDict] = ConfigDict(
        json_schema_extra={"example": {"status": "InProgress"}}
    )


class WorkItemResponse(WorkItemBase):
    """Response body for a work item (task / bug / epic)."""

    id: int
    project_id: int = Field(serialization_alias="projectId")
    status: TaskStatus
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 123,
                "projectId": 7,
                "title": "Implement OAuth callback handler",
                "description": "Handle the redirect from Google and exchange the code for a JWT.",
                "type": "Task",
                "priority": "High",
                "storyPoints": 5,
                "status": "ToDo",
                "parentId": 100,
                "assigneeId": 42,
                "sprintId": 21,
                "createdAt": "2026-05-14T12:00:00Z",
                "updatedAt": None,
            }
        },
    )


class TimeLogCreate(BaseModel):
    """Body for POST /api/tasks/{id}/worklogs."""

    hours_spent: float = Field(..., gt=0, alias="hoursSpent")
    note: str | None = Field(default=None, max_length=TASK_DESCRIPTION_MAX_LENGTH)

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "hoursSpent": 2.5,
                "note": "Wired up the redirect handler and unit-tested the token exchange.",
            }
        },
    )


class TimeLogResponse(TimeLogCreate):
    """Response body for a worklog entry."""

    id: int
    work_item_id: int = Field(serialization_alias="workItemId")
    created_at: datetime = Field(alias="createdAt")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 9,
                "workItemId": 123,
                "hoursSpent": 2.5,
                "note": "Wired up the redirect handler and unit-tested the token exchange.",
                "createdAt": "2026-05-14T16:00:00Z",
            }
        },
    )
