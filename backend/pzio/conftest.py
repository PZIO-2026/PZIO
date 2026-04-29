from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from pzio.db import Base, get_db
from pzio.main import app


# Tests use a real PostgreSQL instance (SAD §7.4) running in a throw-away
# container. The container is started once per test session and reused for all
# tests; per-test isolation is achieved by recreating the schema between tests.
@pytest.fixture(scope="session")
def postgres_engine() -> Generator[Engine, None, None]:
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        engine = create_engine(postgres.get_connection_url(), future=True)
        try:
            yield engine
        finally:
            engine.dispose()


@pytest.fixture
def db_session(postgres_engine: Engine) -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=postgres_engine)
    TestingSession = sessionmaker(
        autocommit=False, autoflush=False, bind=postgres_engine, expire_on_commit=False
    )
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        # Wipe the schema between tests — cheaper than a fresh container, fully
        # isolates writes (sequences reset, FKs cascade) without us tracking
        # which rows each test touched.
        Base.metadata.drop_all(bind=postgres_engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
