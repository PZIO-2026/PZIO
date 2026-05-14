"""Tests for the first-admin bootstrap serialisation.

`_pick_role_for_new_user` must acquire a PostgreSQL transaction-scoped
advisory lock before checking whether an Administrator already exists, so
that two concurrent first-time registrations cannot both be auto-promoted.
On SQLite (and any non-PostgreSQL dialect) the helper must not emit the
lock SQL because the function is dialect-specific.
"""

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pzio.modules.auth import service
from pzio.modules.auth.models import UserRole


def _captured_sql(engine: Engine) -> list[str]:
    """Attach a `before_cursor_execute` listener and return the captured SQL log."""
    log: list[str] = []

    def _record(conn, cursor, statement, parameters, context, executemany):
        log.append(statement)

    event.listen(engine, "before_cursor_execute", _record)
    return log


def test_pick_role_returns_admin_on_empty_db(db_session: Session) -> None:
    assert service._pick_role_for_new_user(db_session) == UserRole.ADMINISTRATOR


def test_pick_role_returns_team_member_when_admin_exists(db_session: Session) -> None:
    from ._helpers import seed_user

    seed_user(db_session, email="root@example.com", role=UserRole.ADMINISTRATOR)
    assert service._pick_role_for_new_user(db_session) == UserRole.TEAM_MEMBER


def test_pick_role_does_not_emit_advisory_lock_on_sqlite(db_session: Session) -> None:
    # SQLite serialises writes at the database level, so the helper must skip
    # the PostgreSQL-only `pg_advisory_xact_lock` call. Skipped when the
    # suite runs against a real PostgreSQL (PZIO_TEST_DB=postgres) — the
    # `_on_postgresql` test below covers that path.
    if db_session.bind.dialect.name != "sqlite":
        pytest.skip("SQLite-specific assertion")
    log = _captured_sql(db_session.bind)
    service._pick_role_for_new_user(db_session)
    assert all("pg_advisory_xact_lock" not in stmt for stmt in log)


def test_pick_role_emits_advisory_lock_on_postgresql(monkeypatch, db_session: Session) -> None:
    # Under the default in-memory SQLite config we patch the dialect name so
    # the helper takes the PostgreSQL branch. The lock SQL is invalid on
    # SQLite so the execute raises — we swallow it and only assert that the
    # SQL was attempted. On a real PostgreSQL (PZIO_TEST_DB=postgres) the
    # dialect is already "postgresql" and the SQL succeeds.
    log = _captured_sql(db_session.bind)
    monkeypatch.setattr(db_session.bind.dialect, "name", "postgresql")

    try:
        service._pick_role_for_new_user(db_session)
    except Exception:
        db_session.rollback()

    assert any("pg_advisory_xact_lock" in stmt for stmt in log)
