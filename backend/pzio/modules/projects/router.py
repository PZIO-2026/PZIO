"""
Responsibilities:
  - Declare routes with correct HTTP methods, paths and status codes.
  - Inject dependencies (DB session, current user) via dependencies.py.
  - Delegate ALL business logic to services.py.
  - Return typed response models with camelCase JSON (response_model_by_alias=True).
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from .dependencies import AuthUser, DBSession
from .schemas import (
    BurndownOut,
    MemberListParams,
    Page,
    ProjectCreate,
    ProjectDetailOut,
    ProjectListParams,
    ProjectMemberCreate,
    ProjectMemberOut,
    ProjectOut,
    ProjectUpdate,
    SprintCreate,
    SprintOut,
    SprintUpdate,
)
from . import services

router = APIRouter(tags=["Projects"])

# ---------------------------------------------------------------------------
# PROJECTS
# ---------------------------------------------------------------------------

@router.post(
    "/api/projects",
    response_model=ProjectOut,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
def create_project(
    payload: ProjectCreate,
    db: DBSession,
    current_user: AuthUser,
) -> ProjectOut:
    return services.create_project(db, payload, current_user.user_id)


@router.get(
    "/api/projects",
    response_model=Page[ProjectOut],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="List projects the current user is a member of",
)
def list_projects(
    db: DBSession,
    current_user: AuthUser,
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    sortBy: str = Query(default="created_at"),
    sortDirection: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[ProjectOut]:
    params = ProjectListParams(
        status=status_filter,
        search=search,
        sortBy=sortBy,
        sortDirection=sortDirection,
        page=page,
        size=size,
    )
    return services.list_projects(db, params, current_user.user_id)


@router.get(
    "/api/projects/{id}",
    response_model=ProjectDetailOut,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get a single project with member and sprint statistics",
)
def get_project(
    id: int,
    db: DBSession,
    current_user: AuthUser,
) -> ProjectDetailOut:
    return services.get_project(db, id, current_user.user_id)


@router.patch(
    "/api/projects/{id}",
    response_model=ProjectOut,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Partially update a project",
)
def update_project(
    id: int,
    payload: ProjectUpdate,
    db: DBSession,
    current_user: AuthUser,
) -> ProjectOut:
    return services.update_project(db, id, payload, current_user.user_id)


@router.delete(
    "/api/projects/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a project",
)
def delete_project(
    id: int,
    db: DBSession,
    current_user: AuthUser,
) -> None:
    services.delete_project(db, id, current_user.user_id)


# ---------------------------------------------------------------------------
# PROJECT MEMBERS
# ---------------------------------------------------------------------------

@router.post(
    "/api/projects/{id}/members",
    response_model=ProjectMemberOut,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Add a user to a project (requires project_owner or scrum_master role)",
)
def add_member(
    id: int,
    payload: ProjectMemberCreate,
    db: DBSession,
    current_user: AuthUser,
) -> ProjectMemberOut:
    return services.add_member(db, id, payload, current_user.user_id)


@router.get(
    "/api/projects/{id}/members",
    response_model=Page[ProjectMemberOut],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="List project members with optional role/search filtering",
)
def list_members(
    id: int,
    db: DBSession,
    current_user: AuthUser,
    role: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[ProjectMemberOut]:
    params = MemberListParams(role=role, search=search, page=page, size=size)
    return services.list_members(db, id, params, current_user.user_id)


@router.delete(
    "/api/projects/{id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a user from a project (requires project_owner or scrum_master role)",
)
def remove_member(
    id: int,
    user_id: int,
    db: DBSession,
    current_user: AuthUser,
) -> None:
    services.remove_member(db, id, user_id, current_user.user_id)


# ---------------------------------------------------------------------------
# SPRINTS
# ---------------------------------------------------------------------------

@router.post(
    "/api/projects/{id}/sprints",
    response_model=SprintOut,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sprint in a project",
)
def create_sprint(
    id: int,
    payload: SprintCreate,
    db: DBSession,
    current_user: AuthUser,
) -> SprintOut:
    

    return services.create_sprint(db, id, payload, current_user.user_id)


@router.get(
    "/api/projects/{id}/sprints",
    response_model=list[SprintOut],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="List all sprints for a project ordered by start date",
)
def list_sprints(
    id: int,
    db: DBSession,
    current_user: AuthUser,
) -> list[SprintOut]:
    return services.list_sprints(db, id, current_user.user_id)


@router.patch(
    "/api/sprints/{id}",
    response_model=SprintOut,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Partially update a sprint",
)
def update_sprint(
    id: int,
    payload: SprintUpdate,
    db: DBSession,
    current_user: AuthUser,
) -> SprintOut:
    return services.update_sprint(db, id, payload, current_user.user_id)


@router.delete(
    "/api/sprints/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sprint",
)
def delete_sprint(
    id: int,
    db: DBSession,
    current_user: AuthUser,
) -> None:
    services.delete_sprint(db, id, current_user.user_id)


@router.get(
    "/api/sprints/{id}/burndown",
    response_model=BurndownOut,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get burndown chart data for a sprint",
)
def get_burndown(
    id: int,
    db: DBSession,
    current_user: AuthUser,
) -> BurndownOut:
    return services.get_burndown(db, id, current_user.user_id)