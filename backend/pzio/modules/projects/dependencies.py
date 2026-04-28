"""
Shared FastAPI dependencies for the `projects` module.
Location: backend/pzio/modules/projects/dependencies.py
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

# Assumes a shared get_db generator in pzio/database.py
from pzio.db import get_db

# Assumes a shared JWT auth dependency in pzio/auth.py
# It raises HTTP 401 automatically when the token is missing/invalid.
from pzio.auth import get_current_user, CurrentUser

# Convenient type aliases for use in router function signatures
DBSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[CurrentUser, Depends(get_current_user)]
