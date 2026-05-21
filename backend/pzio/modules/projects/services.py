"""
All database operations and domain rules live here.
Routers call these functions and handle only HTTP concerns.
"""

from __future__ import annotations

from collections import defaultdict
import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from pzio.modules.tasks.models import (
    TimeLog,
    WorkItem,
)
from sqlalchemy import func, or_, String, cast
from sqlalchemy.orm import Session
from pzio.modules.auth.models import User

from .models import (
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
    ProjectMemberUpdate,
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



def _require_project_roles(
    db: Session,
    project_id: int,
    user_id: int,
    allowed_roles: set[ProjectRole],
) -> ProjectMember:
    membership = _get_membership_or_403(db, project_id, user_id)

    user_roles = {ProjectRole(r) for r in membership.roles}

    if not user_roles.intersection(allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )

    return membership


def _get_membership_or_403(db: Session, project_id: int, user_id: int) -> Optional[ProjectMember]:
    """Return the ProjectMember row for user in project, or None. Administrators bypass this and get a virtual ProjectOwner membership."""
    user = db.get(User, user_id)
    is_admin = user and getattr(user, "role", "") == "Administrator"
    membership = db.query(ProjectMember)\
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )\
        .first()
    
    if membership is None:
        if is_admin:
            return ProjectMember(
                project_id=project_id,
                user_id=user_id,
                roles=[ProjectRole.PROJECT_OWNER]
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project.",
        )

    return membership

def _get_membership_or_404(db: Session, project_id: int, user_id: int) -> ProjectMember:
    """Return the ProjectMember row for the target user, or raise 404."""
    membership = db.query(ProjectMember)\
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )\
        .first()
    
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' is not a member of this project.",
        )

    return membership


def _project_out(project: Project, roles: list[ProjectRole]) -> ProjectOut:
    data = ProjectOut.model_validate(project).model_dump(
        exclude={"current_user_roles"}
    )
    return ProjectOut(**data, current_user_roles=roles)

# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
def create_project(db: Session, payload: ProjectCreate, current_user_id: int) -> ProjectOut:
    existing_projects = (
        db.query(Project.name)
        .join(ProjectMember)
        .filter(
            ProjectMember.user_id == current_user_id,
            Project.name.like(f"{payload.name}%")
        )
        .all()
    )
    
    existing_names = {row[0] for row in existing_projects}
    
    final_name = payload.name
    if final_name in existing_names:
        counter = 1
        while f"{payload.name} ({counter})" in existing_names:
            counter += 1
        final_name = f"{payload.name} ({counter})"

    project = Project(
        name=final_name,
        description=payload.description,
        status=ProjectStatus.ACTIVE,
    )
    db.add(project)
    db.flush()
    owner = ProjectMember(
        project_id=project.project_id,
        user_id=current_user_id,
        roles=[ProjectRole.PROJECT_OWNER]
    )
    db.add(owner)
    db.commit()
    db.refresh(project)
    
    return _project_out(project, owner.roles)

def list_projects(
    db: Session, params: ProjectListParams, current_user_id: int
) -> Page[ProjectOut]:
    user = db.get(User, current_user_id)
    is_admin = user and getattr(user, "role", "") == "Administrator"

    query = (
        db.query(Project, ProjectMember)
        .outerjoin(
            ProjectMember,
            (ProjectMember.project_id == Project.project_id) &
            (ProjectMember.user_id == current_user_id)
        )
    )

    if not is_admin:
        query = query.filter(ProjectMember.user_id == current_user_id)

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
    rows = query.offset(offset).limit(params.size).all()

    return Page(
        items=[
            _project_out(project, membership.roles if membership else [])
            for project, membership in rows
        ],
        total=total,
        page=params.page,
        size=params.size,
    )


def get_project(db: Session, project_id: int, current_user_id: int) -> ProjectDetailOut:
    project = _get_project_or_404(db, project_id)
    membership = _get_membership_or_403(db, project_id, current_user_id)

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
        **ProjectOut.model_validate(project).model_dump(
            exclude={"current_user_roles"}
        ),
        stats=ProjectStats(member_count=member_count, sprint_count=sprint_count),
        current_user_roles=membership.roles,
    )


def update_project(
    db: Session, project_id: int, payload: ProjectUpdate, current_user_id: int
) -> ProjectOut:
    project = _get_project_or_404(db, project_id)
    
    _require_project_roles(
        db, project_id, current_user_id, allowed_roles={ProjectRole.PROJECT_OWNER}
    )

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
    membership = _get_membership_or_403(db, project_id, current_user_id)
    return _project_out(project, membership.roles)


def delete_project(db: Session, project_id: int, current_user_id: int) -> None:
    """Soft-delete: sets status to ARCHIVED."""
    project = _get_project_or_404(db, project_id)
    _require_project_roles(db, project_id, current_user_id, allowed_roles={ProjectRole.PROJECT_OWNER})

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
    _require_project_roles(db, project_id, current_user_id, allowed_roles={ProjectRole.PROJECT_OWNER, ProjectRole.SCRUM_MASTER})

    user = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{payload.email}' was not found.",
        )


    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.user_id,
        )
        .first()
    )
    
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{payload.email}' is already a member of this project.",
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=user.user_id,
        roles=payload.roles,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return ProjectMemberOut(
        id=member.id,
        project_id=member.project_id,
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        roles=member.roles,
        joined_at=member.joined_at,
    )


def list_members(
    db: Session, project_id: int, params: MemberListParams, current_user_id: int
) -> Page[ProjectMemberOut]:
    _get_project_or_404(db, project_id)
    _get_membership_or_403(db, project_id, current_user_id)

    # query = db.query(ProjectMember).filter(ProjectMember.project_id == project_id)
    query = (
        db.query(ProjectMember, User)
        .join(User, User.user_id == ProjectMember.user_id)
        .filter(ProjectMember.project_id == project_id)
    )

    if params.role:
        # check if the underlying database supports array operations (e.g. Postgres)
        dialect = db.bind.dialect.name if db.bind else db.get_bind().dialect.name
        if dialect == "postgresql":
            query = query.filter(ProjectMember.roles.contains([params.role.value]))            
        else:
            search_term = f'%"{params.role.value}"%'
            query = query.filter(cast(ProjectMember.roles, String).like(search_term))

    if params.search:
        search_term = f"%{params.search.strip()}%"

        query = query.filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
            )
        )

    total: int = query.count()

    offset = (params.page - 1) * params.size

    rows = (
        query
        .offset(offset)
        .limit(params.size)
        .all()
    )



    items = [
        ProjectMemberOut(
            id=member.id,
            project_id=member.project_id,
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            roles=member.roles,
            joined_at=member.joined_at,
        )
        for member, user in rows
    ]

    return Page(
        items=items,
        total=total,
        page=params.page,
        size=params.size,
    )


def remove_member(
    db: Session, project_id: int, user_id: int, current_user_id: int
) -> None:
    _get_project_or_404(db, project_id)
    _require_project_roles(db, project_id, current_user_id, allowed_roles={ProjectRole.PROJECT_OWNER, ProjectRole.SCRUM_MASTER})

    membership = _get_membership_or_403(db, project_id, current_user_id)
    membership_to_be_removed = _get_membership_or_404(db, project_id, user_id)
    
    if ProjectRole.PROJECT_OWNER in membership_to_be_removed.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the project owner."
        )
    
    # scrum master can not remove another scrum master
    if ProjectRole.PROJECT_OWNER not in membership.roles:
        if ProjectRole.SCRUM_MASTER in membership_to_be_removed.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Scrum master cannot remove another scrum master."
            )
        
    db.delete(membership_to_be_removed)
    db.commit()

def update_member_roles(
    db: Session, 
    project_id: int, 
    user_id: int, 
    payload: ProjectMemberUpdate, 
    current_user_id: int
) -> ProjectMemberOut:
    _get_project_or_404(db, project_id)
    
    current_membership = _require_project_roles(
        db, project_id, current_user_id, allowed_roles={ProjectRole.PROJECT_OWNER, ProjectRole.SCRUM_MASTER}
    )

    membership_to_be_updated = _get_membership_or_404(db, project_id, user_id)

    is_editing_owner = ProjectRole.PROJECT_OWNER in membership_to_be_updated.roles
    is_current_user_owner = ProjectRole.PROJECT_OWNER in current_membership.roles
    is_trying_to_remove_owner = is_editing_owner and ProjectRole.PROJECT_OWNER not in payload.roles
    is_trying_to_add_owner = not is_editing_owner and ProjectRole.PROJECT_OWNER in payload.roles

    if is_editing_owner and not is_current_user_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the current Owner can edit roles of another Owner."
        )

    if is_trying_to_add_owner and not is_current_user_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the current Owner can grant the Project Owner role."
        )

    if is_trying_to_remove_owner:
        
        # check dialect for array support
        dialect = db.get_bind().dialect.name
        if dialect == "postgresql":
            owner_count = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.roles.contains([ProjectRole.PROJECT_OWNER.value])
            ).count()
        else:
            search_term = f'%"{ProjectRole.PROJECT_OWNER.value}"%'
            owner_count = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                cast(ProjectMember.roles, String).like(search_term)
            ).count()
        
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the Owner role: a project must have at least one Owner."
            )

    membership_to_be_updated.roles = payload.roles
    db.commit()
    db.refresh(membership_to_be_updated)

    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' was not found.",
        )

    return ProjectMemberOut(
        id=membership_to_be_updated.id,
        project_id=membership_to_be_updated.project_id,
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        roles=membership_to_be_updated.roles,
        joined_at=membership_to_be_updated.joined_at,
    )

# ---------------------------------------------------------------------------
# Sprints
# ---------------------------------------------------------------------------
def create_sprint(
    db: Session, project_id: int, payload: SprintCreate, current_user_id: int
) -> SprintOut:
    _get_project_or_404(db, project_id)
    _require_project_roles(db, project_id, current_user_id, allowed_roles={ProjectRole.PROJECT_OWNER, ProjectRole.SCRUM_MASTER})

    if payload.end_date <= payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endDate must be after startDate.",
        )
    
    if (payload.end_date - payload.start_date).days > 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sprint duration is too long. Maximum allowed duration is 60 days.",
        )

    sprint = Sprint(
        project_id=project_id,
        name=payload.name,
        status=SprintStatus.PLANNED,
        start_date=payload.start_date,
        goal=payload.goal,
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
    _get_membership_or_403(db, project_id, current_user_id)

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
    _require_project_roles(db, sprint.project_id, current_user_id, allowed_roles={ProjectRole.PROJECT_OWNER, ProjectRole.SCRUM_MASTER})

    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )
    
    new_status = changes.get("status")
    if new_status == SprintStatus.ACTIVE:
        existing_active = (
            db.query(Sprint)
            .filter(
                Sprint.project_id == sprint.project_id,
                Sprint.status == SprintStatus.ACTIVE,
                Sprint.sprint_id != sprint.sprint_id,
            )
            .first()
        )

        if existing_active is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="There is already an active sprint in this project.",
            )

    for field, value in changes.items():
        setattr(sprint, field, value)

    if sprint.end_date <= sprint.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endDate must be after startDate.",
        )
    
    if (sprint.end_date - sprint.start_date).days > 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sprint duration is too long. Maximum allowed duration is 60 days.",
        )

    sprint.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sprint)
    return SprintOut.model_validate(sprint)


def delete_sprint(db: Session, sprint_id: int, current_user_id: int) -> None:
    sprint = _get_sprint_or_404(db, sprint_id)
    _require_project_roles(db, sprint.project_id, current_user_id, allowed_roles={ProjectRole.PROJECT_OWNER, ProjectRole.SCRUM_MASTER})
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

    _get_membership_or_403(
        db,
        sprint.project_id,
        current_user_id,
    )

    tasks = (
        db.query(WorkItem)
        .filter(WorkItem.sprint_id == sprint_id)
        .all()
    )

    logs = (
        db.query(TimeLog)
        .join(
            WorkItem,
            WorkItem.id == TimeLog.work_item_id,
        )
        .filter(WorkItem.sprint_id == sprint_id)
        .order_by(TimeLog.created_at.asc())
        .all()
    )

    total_points, daily_remaining = (
        _generate_burndown_data(
            sprint=sprint,
            tasks=tasks,
            logs=logs,
        )
    )

    days = [
        BurndownDay.model_validate(
            {
                "date": date,
                "remainingPoints": remaining,
            }
        )
        for date, remaining in daily_remaining
    ]

    return BurndownOut.model_validate(
        {
            "sprint_id": sprint_id,
            "total_points": total_points,
            "days": days,
        }
    )


def _generate_burndown_data(
    sprint: Sprint,
    tasks: list[WorkItem],
    logs: list[TimeLog],
) -> tuple[int, list[tuple[datetime, int]]]:
    """
    Generates historical burndown data using TimeLog
    status transitions.
    """

    start_date = sprint.start_date.date()
    end_date = sprint.end_date.date()

    sprint_days = (
        end_date - start_date
    ).days + 1

    task_points: dict[int, int] = {
        task.id: task.story_points or 0
        for task in tasks
    }

    total_points = sum(task_points.values())

    completed_points_by_day: dict[datetime.date, int] = (
        defaultdict(int)
    )

    for log in logs:
        transitioned_to_done = (
            log.new_status in {"Done"}
            and log.old_status not in {"Done"}
        )

        if not transitioned_to_done:
            continue

        completed_points_by_day[
            log.created_at.date()
        ] += task_points.get(
            log.work_item_id,
            0,
        )

    remaining_points = total_points

    days: list[tuple[datetime, int]] = []

    for i in range(sprint_days):
        current_date = (
            start_date + timedelta(days=i)
        )

        remaining_points -= completed_points_by_day.get(
            current_date,
            0,
        )

        remaining_points = max(
            remaining_points,
            0,
        )

        day_datetime = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            tzinfo=timezone.utc,
        )

        days.append(
            (
                day_datetime,
                remaining_points,
            )
        )

    return total_points, days
