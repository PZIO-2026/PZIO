from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from pzio.config import settings


# SQLite needs check_same_thread=False because FastAPI runs sync routes in a threadpool.
# Other backends (e.g. Postgres) reject this argument, so apply it conditionally.
_connect_args: dict[str, object] = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base shared by every module's ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
