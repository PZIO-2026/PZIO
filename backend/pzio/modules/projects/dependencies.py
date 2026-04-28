"""
Shared FastAPI dependencies for the `projects` module.
Location: backend/pzio/modules/projects/dependencies.py
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 1. Tymczasowy model AuthUser, dopóki nie powstanie pzio.auth
class CurrentUser(BaseModel):
    id: str
    email: str
    role: str = "user"

# 2. Zaślepki (stubs) dla zależności
def get_db() -> Session:
    raise NotImplementedError("Moduł bazy danych (pzio.db) jeszcze nie istnieje.")

def get_current_user() -> CurrentUser:
    raise NotImplementedError("Moduł autoryzacji (pzio.auth) jeszcze nie istnieje.")

# 3. Wygodne aliasy dla routerów
DBSession = Annotated[Session, Depends(get_db)]
AuthUser = Annotated[CurrentUser, Depends(get_current_user)]