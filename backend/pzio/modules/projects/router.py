"""
FastAPI router for the `projects` module.
Location: backend/pzio/modules/projects/router.py

Responsibilities:
  - Declare routes with correct HTTP methods, paths and status codes.
  - Inject dependencies (DB session, current user).
  - Delegate ALL business logic to services.py.
  - Return typed response models.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

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

router = APIRouter(tags=["projects"])


# ===========================================================================
# Projects
# ===========================================================================


@router.post(
    "/api/projects",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
def create_project(
    payload: ProjectCreate,
    db: DBSession,
    _current_user: AuthUser,
) -> ProjectOut:
    return services.create_project(db, payload)


@router.get(
    "/api/projects",
    response_model=Page[ProjectOut],
    status_code=status.HTTP_200_OK,
    summary="List projects with pagination and filters",
)
def list_projects(
    db: DBSession,
    _current_user: AuthUser,
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
    return services.list_projects(db, params)


@router.get(
    "/api/projects/{id}",
    response_model=ProjectDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Get a single project with member and sprint statistics",
)
def get_project(
    id: str,
    db: DBSession,
    _current_user: AuthUser,
) -> ProjectDetailOut:
    return services.get_project(db, id)


@router.patch(
    "/api/projects/{id}",
    response_model=ProjectOut,
    status_code=status.HTTP_200_OK,
    summary="Partially update a project (only supplied fields are changed)",
)
def update_project(
    id: str,
    payload: ProjectUpdate,
    db: DBSession,
    _current_user: AuthUser,
) -> ProjectOut:
    return services.update_project(db, id, payload)


@router.delete(
    "/api/projects/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a project",
)
def delete_project(
    id: str,
    db: DBSession,
    _current_user: AuthUser,
) -> None:
    services.delete_project(db, id)


# ===========================================================================
# Project Members
# ===========================================================================


@router.post(
    "/api/projects/{id}/members",
    response_model=ProjectMemberOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a user to a project",
)
def add_member(
    id: str,
    payload: ProjectMemberCreate,
    db: DBSession,
    _current_user: AuthUser,
) -> ProjectMemberOut:
    return services.add_member(db, id, payload)


@router.get(
    "/api/projects/{id}/members",
    response_model=Page[ProjectMemberOut],
    status_code=status.HTTP_200_OK,
    summary="List project members with optional role/search filtering",
)
def list_members(
    id: str,
    db: DBSession,
    _current_user: AuthUser,
    role: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[ProjectMemberOut]:
    params = MemberListParams(role=role, search=search, page=page, size=size)
    return services.list_members(db, id, params)


@router.delete(
    "/api/projects/{id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a user from a project",
)
def remove_member(
    id: str,
    user_id: str,
    db: DBSession,
    _current_user: AuthUser,
) -> None:
    services.remove_member(db, id, user_id)


# ===========================================================================
# Sprints
# ===========================================================================


@router.post(
    "/api/projects/{id}/sprints",
    response_model=SprintOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sprint in a project (status defaults to 'planned')",
)
def create_sprint(
    id: str,
    payload: SprintCreate,
    db: DBSession,
    _current_user: AuthUser,
) -> SprintOut:
    return services.create_sprint(db, id, payload)


@router.get(
    "/api/projects/{id}/sprints",
    response_model=list[SprintOut],
    status_code=status.HTTP_200_OK,
    summary="List all sprints for a project ordered by start date",
)
def list_sprints(
    id: str,
    db: DBSession,
    _current_user: AuthUser,
) -> list[SprintOut]:
    return services.list_sprints(db, id)


@router.patch(
    "/api/sprints/{id}",
    response_model=SprintOut,
    status_code=status.HTTP_200_OK,
    summary="Partially update a sprint",
)
def update_sprint(
    id: str,
    payload: SprintUpdate,
    db: DBSession,
    _current_user: AuthUser,
) -> SprintOut:
    return services.update_sprint(db, id, payload)


@router.delete(
    "/api/sprints/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sprint",
)
def delete_sprint(
    id: str,
    db: DBSession,
    _current_user: AuthUser,
) -> None:
    services.delete_sprint(db, id)


@router.get(
    "/api/sprints/{id}/burndown",
    response_model=BurndownOut,
    status_code=status.HTTP_200_OK,
    summary="Get the burndown chart data for a sprint",
)
def get_burndown(
    id: str,
    db: DBSession,
    _current_user: AuthUser,
) -> BurndownOut:
    return services.get_burndown(db, id)
