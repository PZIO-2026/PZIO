"""
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

from .models import (
    MEMBERSHIP_MANAGER_ROLES,
    Project,
    ProjectMember,
    ProjectRole,
    ProjectStatus,
    Sprint,
    SprintStatus,
)
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


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return project


def _get_sprint_or_404(db: Session, sprint_id: int) -> Sprint:
    sprint = db.get(Sprint, sprint_id)
    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint '{sprint_id}' not found.",
        )
    return sprint


def _get_member_or_404(db: Session, project_id: int, user_id: int) -> ProjectMember:
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


def _get_membership(db: Session, project_id: int, user_id: int) -> Optional[ProjectMember]:
    """Return the ProjectMember row for user in project, or None."""
    return (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )


def _require_project_access(db: Session, project_id: int, user_id: int) -> ProjectMember:
    """Raise 403 if the user is not a member of the project."""
    membership = _get_membership(db, project_id, user_id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project.",
        )
    return membership


def _require_membership_manager(db: Session, project_id: int, user_id: int) -> None:
    """Raise 403 unless the user holds project_owner or scrum_master role."""
    membership = _get_membership(db, project_id, user_id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project.",
        )
    user_roles = {ProjectRole(r) for r in membership.roles}
    if not user_roles.intersection(MEMBERSHIP_MANAGER_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Project Owners and Scrum Masters can manage project membership.",
        )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
def create_project(db: Session, payload: ProjectCreate, current_user_id: int) -> ProjectOut:
    project = Project(
        name=payload.name,
        description=payload.description,
        status=ProjectStatus.ACTIVE,
    )
    db.add(project)
    db.flush()
    
    # Automatyczne dodanie twórcy
    owner = ProjectMember(
        project_id=project.project_id,
        user_id=current_user_id,
        roles=[ProjectRole.PROJECT_OWNER]
    )
    db.add(owner)
    db.commit()
    db.refresh(project)
    
    return ProjectOut.model_validate(project)

def list_projects(
    db: Session, params: ProjectListParams, current_user_id: int
) -> Page[ProjectOut]:
    # Users can only see projects they are a member of
    query = (
        db.query(Project)
        .join(ProjectMember)
        .filter(ProjectMember.user_id == current_user_id)
    )
    
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

    sort_column = params.sortBy if params.sortBy in _SORTABLE_FIELDS else "created_at"
    col = getattr(Project, sort_column)
    query = query.order_by(col.asc() if params.sortDirection == "asc" else col.desc())

    total: int = query.count()
    offset = (params.page - 1) * params.size
    projects = query.offset(offset).limit(params.size).all()

    return Page(
        items=[ProjectOut.model_validate(p) for p in projects],
        total=total,
        page=params.page,
        size=params.size,
    )


def get_project(db: Session, project_id: int, current_user_id: int) -> ProjectDetailOut:
    project = _get_project_or_404(db, project_id)
    _require_project_access(db, project_id, current_user_id)

    member_count = (
        db.query(func.count(ProjectMember.id))
        .filter(ProjectMember.project_id == project_id)
        .scalar()
        or 0
    )
    sprint_count = (
        db.query(func.count(Sprint.sprint_id))
        .filter(Sprint.project_id == project_id)
        .scalar()
        or 0
    )

    return ProjectDetailOut(
        **ProjectOut.model_validate(project).model_dump(),
        stats=ProjectStats(member_count=member_count, sprint_count=sprint_count),
    )


def update_project(
    db: Session, project_id: int, payload: ProjectUpdate, current_user_id: int
) -> ProjectOut:
    project = _get_project_or_404(db, project_id)
    _require_project_access(db, project_id, current_user_id)

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


def delete_project(db: Session, project_id: int, current_user_id: int) -> None:
    """Soft-delete: sets status to ARCHIVED."""
    project = _get_project_or_404(db, project_id)
    _require_project_access(db, project_id, current_user_id)
    project.status = ProjectStatus.ARCHIVED
    project.updated_at = datetime.now(timezone.utc)
    db.commit()


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------
def add_member(
    db: Session, project_id: int, payload: ProjectMemberCreate, current_user_id: int
) -> ProjectMemberOut:
    _get_project_or_404(db, project_id)
    _require_membership_manager(db, project_id, current_user_id)

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.user_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{payload.user_id}' is already a member of this project.",
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=payload.user_id,
        roles=payload.roles,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return ProjectMemberOut.model_validate(member)


def list_members(
    db: Session, project_id: int, params: MemberListParams, current_user_id: int
) -> Page[ProjectMemberOut]:
    _get_project_or_404(db, project_id)
    _require_project_access(db, project_id, current_user_id)

    query = db.query(ProjectMember).filter(ProjectMember.project_id == project_id)

    if params.role:
        query = query.filter(ProjectMember.roles.contains([params.role]))

    if params.search:
        # Search by user_id (int) — exact match only; for name/email search
        # join with the users table when the auth module exposes that relation.
        try:
            query = query.filter(ProjectMember.user_id == int(params.search))
        except ValueError:
            # Non-integer search term → no results for user_id column
            query = query.filter(False)  # noqa: simplest safe no-op filter

    total: int = query.count()
    offset = (params.page - 1) * params.size
    members = query.offset(offset).limit(params.size).all()

    return Page(
        items=[ProjectMemberOut.model_validate(m) for m in members],
        total=total,
        page=params.page,
        size=params.size,
    )


def remove_member(
    db: Session, project_id: int, user_id: int, current_user_id: int
) -> None:
    _get_project_or_404(db, project_id)
    _require_membership_manager(db, project_id, current_user_id)
    
    member = _get_member_or_404(db, project_id, user_id)
    
    if ProjectRole.PROJECT_OWNER in member.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the project owner."
        )
        
    db.delete(member)
    db.commit()

# ---------------------------------------------------------------------------
# Sprints
# ---------------------------------------------------------------------------
def create_sprint(
    db: Session, project_id: int, payload: SprintCreate, current_user_id: int
) -> SprintOut:
    _get_project_or_404(db, project_id)
    _require_project_access(db, project_id, current_user_id)

    if payload.end_date <= payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endDate must be after startDate.",
        )

    sprint = Sprint(
        project_id=project_id,
        name=payload.name,
        status=SprintStatus.PLANNED,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return SprintOut.model_validate(sprint)


def list_sprints(
    db: Session, project_id: int, current_user_id: int
) -> list[SprintOut]:
    _get_project_or_404(db, project_id)
    _require_project_access(db, project_id, current_user_id)

    sprints = (
        db.query(Sprint)
        .filter(Sprint.project_id == project_id)
        .order_by(Sprint.start_date.asc())
        .all()
    )
    return [SprintOut.model_validate(s) for s in sprints]


def update_sprint(
    db: Session, sprint_id: int, payload: SprintUpdate, current_user_id: int
) -> SprintOut:
    sprint = _get_sprint_or_404(db, sprint_id)
    _require_project_access(db, sprint.project_id, current_user_id)

    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    for field, value in changes.items():
        setattr(sprint, field, value)

    if sprint.end_date <= sprint.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endDate must be after startDate.",
        )

    sprint.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sprint)
    return SprintOut.model_validate(sprint)


def delete_sprint(db: Session, sprint_id: int, current_user_id: int) -> None:
    sprint = _get_sprint_or_404(db, sprint_id)
    _require_project_access(db, sprint.project_id, current_user_id)
    db.delete(sprint)
    db.commit()


# ---------------------------------------------------------------------------
# Burndown chart
# ---------------------------------------------------------------------------
def get_burndown(db: Session, sprint_id: int, current_user_id: int) -> BurndownOut:
    """
    Generates a daily burndown chart for a sprint.

    NOTE: Task story-points are stubbed until the `tasks` module is integrated.
    Replace `_stub_burndown_data` with a real cross-module query/service call.
    """
    sprint = _get_sprint_or_404(db, sprint_id)
    _require_project_access(db, sprint.project_id, current_user_id)

    total_points, daily_remaining = _stub_burndown_data(sprint)

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
    Placeholder: generates a linear ideal burndown.
    Replace once the tasks module is integrated.
    """
    total_points = 0
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