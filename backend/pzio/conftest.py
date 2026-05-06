import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from pzio.db import Base, get_db
from pzio.main import app


# Default: in-memory SQLite — fast, hermetic, zero external dependencies.
# Set `PZIO_TEST_DB=postgres` to spin up a real PostgreSQL via testcontainers
# (matches production / SAD §7.4); requires a Docker socket accessible to the
# current user.
TEST_DB_BACKEND = os.getenv("PZIO_TEST_DB", "sqlite").lower()


@pytest.fixture(scope="session")
def _engine() -> Generator[Engine, None, None]:
    if TEST_DB_BACKEND == "postgres":
        from testcontainers.postgres import PostgresContainer

        with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
            engine = create_engine(postgres.get_connection_url(), future=True)
            try:
                yield engine
            finally:
                engine.dispose()
    else:
        # In-memory SQLite shared across the connection pool so all sessions
        # opened during one test see the same data. StaticPool keeps a single
        # underlying connection.
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            yield engine
        finally:
            engine.dispose()


@pytest.fixture
def db_session(_engine: Engine) -> Generator[Session, None, None]:
    # Recreate the schema between tests for full isolation (sequences reset, FKs
    # cascade) without us tracking which rows each test touched.
    Base.metadata.create_all(bind=_engine)
    TestingSession = sessionmaker(
        autocommit=False, autoflush=False, bind=_engine, expire_on_commit=False
    )
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
