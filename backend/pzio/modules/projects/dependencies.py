"""
Delegates DB and auth entirely to the existing pzio infrastructure
so the projects module stays consistent with the auth module.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from pzio.db import get_db
from pzio.modules.auth.deps import get_current_user
from pzio.modules.auth.models import User

# Usage:
#   def my_endpoint(db: DBSession, current_user: AuthUser) -> ...:
DBSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[User, Depends(get_current_user)]
