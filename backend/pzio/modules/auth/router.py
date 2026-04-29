from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from pzio.db import get_db
from pzio.modules.auth import service
from pzio.modules.auth.models import User
from pzio.modules.auth.schemas import (
    LoginRequest,
    PaginatedUserResponse,
    TokenResponse,
    UserCreate,
    UserRead,
    UserStatusUpdate,
    UserUpdate,
)
from pzio.modules.auth.security import create_access_token
from pzio.modules.auth.deps import get_current_user, require_admin

# Endpoints in this module: see SAD §4.1 (paths /api/auth/* and /api/users/*).
# Each route declares its full path on the decorator — no router-level prefix is set
# because the auth module owns multiple URL roots.
router = APIRouter(tags=["Auth"])


@router.post(
    "/api/auth/register",
    response_model=UserRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a user with role `TeamMember`. Returns the user without the password hash.",
    responses={
        201: {"description": "User created"},
        400: {"description": "Validation error"},
        409: {"description": "Email already in use"},
    },
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    try:
        user = service.create_user(db, payload)
    except service.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    return UserRead.model_validate(user)


@router.post(
    "/api/auth/login",
    response_model=TokenResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Log in with email and password",
    description="Returns a JWT access token. Use it as `Authorization: Bearer <token>` on protected routes.",
    responses={
        200: {"description": "Authenticated"},
        401: {"description": "Invalid credentials"},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = service.authenticate_user(db, payload.email, payload.password)
    except service.InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token, expires_in = create_access_token(user.user_id, user.role)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get(
    "/api/users/me",
    response_model=UserRead,
    response_model_by_alias=True,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
def get_profile(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch(
    "/api/users/me",
    response_model=UserRead,
    response_model_by_alias=True,
    summary="Update current user profile",
    description="Updates the profile of the currently authenticated user. All fields are optional.",
)
def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    updated_user = service.update_user_profile(db, current_user, payload)
    return UserRead.model_validate(updated_user)


@router.get(
    "/api/users",
    response_model=PaginatedUserResponse,
    response_model_by_alias=True,
    summary="List users (Admin)",
    description="Returns a paginated list of users. Requires Administrator role.",
)
def list_users(
    search: str | None = Query(None, description="Search by email, first name, or last name"),
    is_active: bool | None = Query(None, alias="isActive", description="Filter by active status"),
    sort_by: str | None = Query(None, alias="sortBy", description="Field to sort by"),
    sort_direction: str | None = Query("desc", alias="sortDirection", description="Sort direction (asc or desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> PaginatedUserResponse:
    items, total = service.get_users_paginated(db, search, is_active, sort_by, sort_direction, page, size)
    
    return PaginatedUserResponse(
        items=[UserRead.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size
    )


@router.patch(
    "/api/users/{id}/status",
    response_model=UserRead,
    response_model_by_alias=True,
    summary="Change user status (Admin)",
    description="Activates or deactivates a user account. Requires Administrator role.",
    responses={404: {"description": "User not found"}},
)
def update_user_status(
    id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserRead:
    try:
        updated_user = service.update_user_status(db, id, payload.is_active)
    except service.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserRead.model_validate(updated_user)