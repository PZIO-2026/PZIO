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
    status: TaskStatus = TaskStatus.TODO


class WorkItemUpdate(BaseModel):
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
    )


class StatusUpdate(BaseModel):
    status: TaskStatus


class WorkItemResponse(WorkItemBase):
    id: int
    project_id: int = Field(serialization_alias="projectId")
    status: TaskStatus
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True, populate_by_name=True
    )


class TimeLogCreate(BaseModel):
    hours_spent: float = Field(..., gt=0, alias="hoursSpent")
    note: str | None = Field(default=None, max_length=TASK_DESCRIPTION_MAX_LENGTH)

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimeLogResponse(TimeLogCreate):
    id: int
    work_item_id: int = Field(serialization_alias="workItemId")
    created_at: datetime = Field(alias="createdAt")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True, populate_by_name=True
    )
