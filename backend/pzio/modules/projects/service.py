from sqlalchemy.orm import Session
from uuid import UUID

from pzio.modules.projects import models, schemas

def create_project(db: Session, payload: schemas.ProjectCreate) -> models.Project:
    # 1. Tworzymy nowy obiekt modelu bazy danych na podstawie danych z Pydantic (payload)
    db_project = models.Project(
        name=payload.name,
        description=payload.description,
        # status i creation_date ustawią się same dzięki 'default' w models.py
    )
    
    # 2. Dodajemy do sesji i zapisujemy w bazie
    db.add(db_project)
    db.commit()
    db.refresh(db_project) # Pobieramy z bazy, żeby mieć wygenerowane ID i datę
    
    return db_project