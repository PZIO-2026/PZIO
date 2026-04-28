"""
Business logic for the `projects` module.
Location: backend/pzio/modules/projects/services.py

All database operations and domain rules live here.
Routers call these functions and handle only HTTP concerns.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import Project, ProjectMember, ProjectStatus, Sprint, SprintStatus
from .schemas import (
    BurndownDay,
    BurndownOut,
    MemberListParams,
    Page,
    ProjectCreate,
    ProjectDetailOut,
    ProjectListParams,
    ProjectMemberCreate,
    ProjectMemberOut,
    ProjectOut,
    ProjectStats,
    ProjectUpdate,
    SprintCreate,
    SprintOut,
    SprintUpdate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SORTABLE_FIELDS: set[str] = {"created_at", "updated_at", "name", "status"}


def _get_project_or_404(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return project


def _get_sprint_or_404(db: Session, sprint_id: str) -> Sprint:
    sprint = db.get(Sprint, sprint_id)
    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint '{sprint_id}' not found.",
        )
    return sprint


def _get_member_or_404(db: Session, project_id: str, user_id: str) -> ProjectMember:
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member '{user_id}' not found in project '{project_id}'.",
        )
    return member


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


def create_project(db: Session, payload: ProjectCreate) -> ProjectOut:
    project = Project(
        name=payload.name,
        description=payload.description,
        status=ProjectStatus.ACTIVE,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


def list_projects(db: Session, params: ProjectListParams) -> Page[ProjectOut]:
    query = db.query(Project)

    # Filtering
    if params.status is not None:
        query = query.filter(Project.status == params.status)

    if params.search:
        like = f"%{params.search}%"
        query = query.filter(
            or_(
                Project.name.ilike(like),
                Project.description.ilike(like),
            )
        )

    # Sorting – only allow whitelisted column names
    sort_column = params.sortBy if params.sortBy in _SORTABLE_FIELDS else "created_at"
    col = getattr(Project, sort_column)
    if params.sortDirection == "asc":
        query = query.order_by(col.asc())
    else:
        query = query.order_by(col.desc())

    total: int = query.count()
    offset = (params.page - 1) * params.size
    projects = query.offset(offset).limit(params.size).all()

    return Page(
        items=[ProjectOut.model_validate(p) for p in projects],
        total=total,
        page=params.page,
        size=params.size,
    )


def get_project(db: Session, project_id: str) -> ProjectDetailOut:
    project = _get_project_or_404(db, project_id)

    member_count = (
        db.query(func.count(ProjectMember.id))
        .filter(ProjectMember.project_id == project_id)
        .scalar()
        or 0
    )
    sprint_count = (
        db.query(func.count(Sprint.id))
        .filter(Sprint.project_id == project_id)
        .scalar()
        or 0
    )

    return ProjectDetailOut(
        **ProjectOut.model_validate(project).model_dump(),
        stats=ProjectStats(member_count=member_count, sprint_count=sprint_count),
    )


def update_project(db: Session, project_id: str, payload: ProjectUpdate) -> ProjectOut:
    project = _get_project_or_404(db, project_id)

    # Only update fields that were actually sent in the request body
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    for field, value in changes.items():
        setattr(project, field, value)

    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


def delete_project(db: Session, project_id: str) -> None:
    """Soft-delete: sets status to ARCHIVED. Hard-delete can be swapped in."""
    project = _get_project_or_404(db, project_id)
    project.status = ProjectStatus.ARCHIVED
    project.updated_at = datetime.now(timezone.utc)
    db.commit()


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


def add_member(
    db: Session, project_id: str, payload: ProjectMemberCreate
) -> ProjectMemberOut:
    _get_project_or_404(db, project_id)

    # 409 – member already exists in this project
    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.userId,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{payload.userId}' is already a member of this project.",
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=payload.userId,
        roles=payload.roles,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return ProjectMemberOut.model_validate(member)


def list_members(
    db: Session, project_id: str, params: MemberListParams
) -> Page[ProjectMemberOut]:
    _get_project_or_404(db, project_id)

    query = db.query(ProjectMember).filter(ProjectMember.project_id == project_id)

    if params.role:
        # PostgreSQL ARRAY contains operator
        query = query.filter(ProjectMember.roles.contains([params.role]))

    if params.search:
        like = f"%{params.search}%"
        query = query.filter(ProjectMember.user_id.ilike(like))

    total: int = query.count()
    offset = (params.page - 1) * params.size
    members = query.offset(offset).limit(params.size).all()

    return Page(
        items=[ProjectMemberOut.model_validate(m) for m in members],
        total=total,
        page=params.page,
        size=params.size,
    )


def remove_member(db: Session, project_id: str, user_id: str) -> None:
    _get_project_or_404(db, project_id)
    member = _get_member_or_404(db, project_id, user_id)
    db.delete(member)
    db.commit()


# ---------------------------------------------------------------------------
# Sprints
# ---------------------------------------------------------------------------


def create_sprint(db: Session, project_id: str, payload: SprintCreate) -> SprintOut:
    _get_project_or_404(db, project_id)

    if payload.endDate <= payload.startDate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endDate must be after startDate.",
        )

    sprint = Sprint(
        project_id=project_id,
        name=payload.name,
        status=SprintStatus.PLANNED,
        start_date=payload.startDate,
        end_date=payload.endDate,
    )
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return SprintOut.model_validate(sprint)


def list_sprints(db: Session, project_id: str) -> list[SprintOut]:
    _get_project_or_404(db, project_id)

    sprints = (
        db.query(Sprint)
        .filter(Sprint.project_id == project_id)
        .order_by(Sprint.start_date.asc())
        .all()
    )
    return [SprintOut.model_validate(s) for s in sprints]


def update_sprint(db: Session, sprint_id: str, payload: SprintUpdate) -> SprintOut:
    sprint = _get_sprint_or_404(db, sprint_id)

    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    # Map camelCase aliases back to ORM column names
    alias_map = {"startDate": "start_date", "endDate": "end_date"}
    normalised = {alias_map.get(k, k): v for k, v in changes.items()}

    for field, value in normalised.items():
        setattr(sprint, field, value)

    # Validate date invariant after applying changes
    if sprint.end_date <= sprint.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endDate must be after startDate.",
        )

    sprint.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sprint)
    return SprintOut.model_validate(sprint)


def delete_sprint(db: Session, sprint_id: str) -> None:
    sprint = _get_sprint_or_404(db, sprint_id)
    db.delete(sprint)
    db.commit()


# ---------------------------------------------------------------------------
# Burndown chart
# ---------------------------------------------------------------------------


def get_burndown(db: Session, sprint_id: str) -> BurndownOut:
    """
    Generates a daily burndown chart for a sprint.

    NOTE: This implementation uses a stub for task story-points because the
    `tasks` module is managed by a separate team. When the tasks service is
    ready, replace `_fetch_task_points` with a real call/query.

    Current logic:
    - totalPoints = sum of story points for tasks assigned to the sprint.
    - For each calendar day [startDate .. endDate] we sum the story points of
      tasks NOT yet completed by end of that day (remainingPoints).
    - Days before today that have no completion data are carried forward.
    """
    sprint = _get_sprint_or_404(db, sprint_id)

    # --- Stub: replace with real task-point query ---
    total_points, daily_remaining = _stub_burndown_data(sprint)
    # ------------------------------------------------

    days = [
        BurndownDay.model_validate({"date": d, "remainingPoints": r})
        for d, r in daily_remaining
    ]

    return BurndownOut.model_validate(
        {
            "sprintId": sprint_id,
            "totalPoints": total_points,
            "days": days,
        }
    )


def _stub_burndown_data(
    sprint: Sprint,
) -> tuple[int, list[tuple[datetime, int]]]:
    """
    Placeholder that generates a linear ideal burndown.
    Replace the body of this function once the tasks module is integrated.
    """
    total_points = 0  # No tasks yet → 0 total points
    start = sprint.start_date
    end = sprint.end_date

    delta_days = max((end.date() - start.date()).days, 0)
    daily: list[tuple[datetime, int]] = []

    for i in range(delta_days + 1):
        day_dt = datetime(
            *(start.date() + timedelta(days=i)).timetuple()[:3],
            tzinfo=timezone.utc,
        )
        remaining = max(
            0,
            total_points - math.floor(total_points * i / max(delta_days, 1)),
        )
        daily.append((day_dt, remaining))

    return total_points, daily
