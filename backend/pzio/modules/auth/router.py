from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from pzio.db import get_db
from pzio.modules.auth import service
from pzio.modules.auth.schemas import LoginRequest, TokenResponse, UserCreate, UserRead
from pzio.modules.auth.security import create_access_token

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
