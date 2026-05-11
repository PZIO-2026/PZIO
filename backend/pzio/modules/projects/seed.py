import argparse
import logging
from sqlalchemy.orm import Session

# Importy bazy danych
from pzio.db import SessionLocal
from datetime import datetime, timedelta, timezone
import random

# Import zależnego usera (z auth)
from pzio.modules.auth.models import User, UserRole

# Import zależnego work item
from pzio.modules.tasks.models import WorkItem
from pzio.modules.auth.security import hash_password


# Importy z Twojego modułu
from pzio.modules.projects.models import (
    Project, 
    ProjectMember, 
    Sprint, 
    ProjectStatus, 
    ProjectRole,
    SprintStatus
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_db(db: Session):
    """Czyści dane specyficzne dla tego modułu oraz testowych użytkowników."""
    logger.info("Usuwanie starych danych modułu Projects...")
    
    try:
        # Usuwamy w odpowiedniej kolejności (najpierw tabele zależne)
        db.query(Sprint).delete()
        db.query(ProjectMember).delete()
        db.query(Project).delete()
        
        # Usuwamy tylko użytkowników testowych wygenerowanych przez ten skrypt
        db.query(User).filter(User.email.like("test_user_%@example.com")).delete(synchronize_session=False)
        
        db.commit()
        logger.info("Baza danych została wyczyszczona z danych testowych.")
    except Exception as e:
        db.rollback()
        logger.error(f"Błąd podczas czyszczenia bazy: {e}")
        raise



def seed_projects_module(db: Session, should_clear: bool = False):
    if should_clear:
        clear_db(db)

    logger.info("Rozpoczynam zasilanie modułu: PROJECTS")

    # 1. Generowanie 10 użytkowników
    logger.info("Generowanie 10 użytkowników testowych...")
    users = []
    for i in range(1, 11):
        email = f"test_user_{i}@example.com"
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(
                email=email,
                password_hash=hash_password("password123"),
                first_name=f"{i} Test",
                last_name="User",
                role=UserRole.TEAM_MEMBER,
                is_active=True,
            )
            db.add(user)
        users.append(user)

    user1 = users[0]
    user2 = users[1]
    pool_users = users[2:8]  # Użytkownicy od 3 do 8 (indeksy 2-7)

    # 2. Generowanie 5 projektów dla Usera 1
    logger.info(f"Generowanie projektów dla: {user1.email}")
    for k in range(1, 6):
        project = Project(
            name=f"Projekt A{k} - Startowy",
            description=f"To jest projekt testowy numer {k} zarządzany przez usera 1.",
            status=ProjectStatus.ACTIVE
        )
        db.add(project)
        db.flush()  # Zapisuje obiekt w sesji, żeby wygenerować project.project_id


        for j in range(1, 5):
            if j == 1:
                sprint_status = SprintStatus.ACTIVE
            else:
                sprint_status = random.choice([SprintStatus.PLANNED, SprintStatus.COMPLETED])

            sprint = Sprint(
                name=f"Sprint {j}",
                goal=f"Cel sprintu {j} dla projektu {project.name}",
                start_date=datetime.now(timezone.utc) + timedelta(days=(j-1)*14),
                status=sprint_status,
                end_date=datetime.now(timezone.utc) + timedelta(days=j*14),
                project_id=project.project_id
            )
            db.add(sprint)
            db.flush()

            task_titles = [
                "Implement authentication",
                "Create login page",
                "Fix dashboard bug",
                "Setup CI pipeline",
                "Improve API validation",
                "Add project members page",
                "Refactor permissions",
                "Create sprint board",
                "Optimize queries",
                "Write integration tests",
            ]

            statuses_by_sprint = {
                SprintStatus.PLANNED: ["ToDo"],
                SprintStatus.ACTIVE: ["ToDo", "InProgress", "Done"],
                SprintStatus.COMPLETED: ["Done"],
            }

            for i in range(random.randint(8, 15)):

                work_item = WorkItem(
                    project_id=project.project_id,
                    sprint_id=sprint.sprint_id,
                    title=random.choice(task_titles),
                    description="Seeded test task.",
                    type=random.choice([
                        "Task",
                        "Bug",
                        "Story",
                    ]),
                    priority=random.choice(["Low", "Medium", "High"]),
                    story_points=random.choice([
                        1,
                        2,
                        3,
                        5,
                        8,
                    ]),
                    assignee_id=random.choice(users).user_id,
                    status=random.choice(statuses_by_sprint[sprint.status]),
                )

                db.add(work_item)



        # Przypisanie Usera 1 jako PROJECT_OWNER
        owner_member = ProjectMember(
            project_id=project.project_id,
            user_id=user1.user_id,
            roles=[ProjectRole.PROJECT_OWNER]
        )
        db.add(owner_member)

        # Dodanie użytkowników 3-8 do projektu jako DEVELOPER
        for pu in pool_users:
            member = ProjectMember(
                project_id=project.project_id,
                user_id=pu.user_id,
                roles=[ProjectRole.DEVELOPER]
            )
            db.add(member)

    # 3. Generowanie 5 projektów dla Usera 2
    logger.info(f"Generowanie projektów dla: {user2.email}")
    for i in range(1, 6):
        project = Project(
            name=f"Projekt B{i} - Badawczy",
            description=f"Inny rodzaj projektu, zarządzany przez usera 2.",
            status=ProjectStatus.ACTIVE
        )
        db.add(project)
        db.flush()

        # Przypisanie Usera 2 jako PROJECT_OWNER
        owner_member = ProjectMember(
            project_id=project.project_id,
            user_id=user2.user_id,
            roles=[ProjectRole.PROJECT_OWNER]
        )
        db.add(owner_member)

        # Dodanie użytkowników 3-8 do projektu jako QA (dla urozmaicenia danych na froncie)
        for pu in pool_users:
            member = ProjectMember(
                project_id=project.project_id,
                user_id=pu.user_id,
                roles=[ProjectRole.QA]
            )
            db.add(member)

    # Zapisujemy wszystko do bazy
    db.commit()
    logger.info("Pomyślnie zapisano wszystkie dane projektów i członków!")

    # 4. Podsumowanie dla Frontendu
    print("\n" + "="*60)
    print(" DANE TESTOWE GOTOWE ")
    print("="*60)
    print("Wygenerowano 10 kont. Hasło do wszystkich to: password123")
    print("\nKluczowi użytkownicy:")
    print(f" 1. Właściciel 5 projektów: {user1.email}")
    print(f" 2. Właściciel 5 projektów: {user2.email}")
    print(f" 3. Zwykły członek (przypisany do 10): {pool_users[0].email}")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Konfiguracja parsera argumentów
    parser = argparse.ArgumentParser(description="Seedowanie danych dla modułu Projects.")
    parser.add_argument("--clear", action="store_true", help="Wyczyść dane modułu przed seedowaniem")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        seed_projects_module(db, should_clear=args.clear)
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas seedowania: {e}")
        db.rollback()
    finally:
        db.close()